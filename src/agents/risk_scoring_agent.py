from src.core.base_agent import BaseAgent
from src.tools.validators import WorkflowState
from src.tools.llm_utils import get_groq_chat, parse_json_with_retry, RiskSchema

class RiskScoringAgent(BaseAgent):
    def __init__(self):
        super().__init__("RiskScoringAgent")
    
    def run(self, state: WorkflowState) -> WorkflowState:
        """Use LangChain + Groq to produce structured risk assessment"""
        self.log("Performing AI-powered risk assessment")
        
        if not state.compliance_eval:
            self.log("No compliance evaluation data available")
            return state
        
        try:
            llm = get_groq_chat()
            
            # Prepare context for LLM
            eval_data = state.compliance_eval
            context = f"""
Employee Compliance Analysis:
- Missing Documents: {len(eval_data.missing_documents)} ({', '.join(eval_data.missing_documents)})
- Expiring Documents: {len(eval_data.expiring_documents)}
- Expired Documents: {len(eval_data.expired_documents)}
- Base Compliance Score: {eval_data.base_score:.1f}%
- Priority Hint: {eval_data.priority_hint}

Analyze this compliance data and provide a risk assessment.

OUTPUT JSON ONLY with this exact structure:
{{
    "anomaly_score": 0.0-1.0,
    "risk_level": "low|medium|high|critical",
    "verification_confidence": 0.0-1.0,
    "rationale": "explanation of risk factors"
}}

Examples:
- High missing documents + expired = {{"anomaly_score": 0.8, "risk_level": "critical", "verification_confidence": 0.9, "rationale": "Multiple critical documents missing and expired"}}
- Few expiring documents = {{"anomaly_score": 0.3, "risk_level": "medium", "verification_confidence": 0.8, "rationale": "Some documents approaching expiry"}}
- All compliant = {{"anomaly_score": 0.1, "risk_level": "low", "verification_confidence": 0.95, "rationale": "All documents in compliance"}}
"""
            
            risk_result = parse_json_with_retry(llm, context, RiskSchema)
            
            if risk_result:
                state.risk_assessment = {
                    "anomaly_score": risk_result.anomaly_score,
                    "risk_level": risk_result.risk_level,
                    "verification_confidence": risk_result.verification_confidence,
                    "rationale": risk_result.rationale
                }
                self.log(f"Risk assessment: {risk_result.risk_level} ({risk_result.anomaly_score:.2f})")
            else:
                # Fallback risk assessment
                self.log("LLM parsing failed, using fallback risk assessment")
                state.risk_assessment = self._fallback_risk_assessment(eval_data)
        
        except Exception as e:
            self.log(f"Risk scoring failed: {e}, using fallback")
            state.risk_assessment = self._fallback_risk_assessment(state.compliance_eval)
        
        return state
    
    def _fallback_risk_assessment(self, eval_data) -> dict:
        """Fallback risk assessment when LLM fails"""
        expired_count = len(eval_data.expired_documents)
        missing_count = len(eval_data.missing_documents)
        
        if expired_count > 0:
            return {
                "anomaly_score": 0.8,
                "risk_level": "critical",
                "verification_confidence": 0.9,
                "rationale": f"{expired_count} expired documents detected"
            }
        elif missing_count > 2:
            return {
                "anomaly_score": 0.6,
                "risk_level": "high",
                "verification_confidence": 0.8,
                "rationale": f"{missing_count} documents missing"
            }
        elif missing_count > 0:
            return {
                "anomaly_score": 0.3,
                "risk_level": "medium",
                "verification_confidence": 0.7,
                "rationale": f"{missing_count} documents missing"
            }
        else:
            return {
                "anomaly_score": 0.1,
                "risk_level": "low",
                "verification_confidence": 0.9,
                "rationale": "All documents in compliance"
            }