from src.core.base_agent import BaseAgent
from src.core.blackboard import Blackboard
from src.tools.validators import WorkflowState
from src.tools.llm_utils import get_groq_chat, parse_json_with_retry, ActionPlanSchema
from src.tools.email_utils import send_admin_email

class RecommendationAgent(BaseAgent):
    def __init__(self):
        super().__init__("RecommendationAgent")
    
    def run(self, state: WorkflowState) -> WorkflowState:
        """Generate admin recommendations and finalize analysis"""
        self.log("Generating admin recommendations")
        
        if not state.risk_assessment or not state.compliance_eval:
            self.log("Missing risk assessment or compliance evaluation")
            return state
        
        # Generate action plan using LLM
        action_plan = self._generate_action_plan(state)
        
        # Calculate final compliance score
        final_score = self._calculate_final_score(state)
        
        # Write final analysis to blackboard
        with Blackboard() as bb:
            analysis_id = bb.insert_analysis_record(
                employee_id=state.candidate_id,
                compliance_score=final_score,
                missing_documents=state.compliance_eval.missing_documents,
                expiring_documents=state.compliance_eval.expiring_documents,
                risk_assessment=state.risk_assessment,
                action_plan=action_plan,
                priority_level=state.compliance_eval.priority_hint
            )
            
            self.log(f"Created analysis record {analysis_id}")
        
        # Send admin summary email
        self._send_admin_summary(state, final_score, action_plan)
        
        state.finalized = True
        return state
    
    def _generate_action_plan(self, state: WorkflowState) -> dict:
        """Generate action plan using LLM"""
        try:
            llm = get_groq_chat()
            
            risk_level = state.risk_assessment.get("risk_level", "medium")
            missing_count = len(state.compliance_eval.missing_documents)
            expiring_count = len(state.compliance_eval.expiring_documents)
            expired_count = len(state.compliance_eval.expired_documents)
            
            context = f"""
Generate an admin action plan for employee compliance management:

Risk Level: {risk_level}
Missing Documents: {missing_count}
Expiring Documents: {expiring_count}
Expired Documents: {expired_count}
Employee: {state.profile.first_name} {state.profile.last_name}
Department: {state.profile.department}

OUTPUT JSON ONLY with this structure:
{{
    "owner": "HR Ops|Manager|Employee",
    "actions": [
        {{"step": "action description", "sla_days": 7, "channel": "email|portal", "escalation_if_overdue": "escalation action"}}
    ],
    "message_templates": {{
        "employee": "template for employee communication",
        "manager": "template for manager communication", 
        "hr": "template for HR team communication"
    }}
}}

Examples:
Critical risk: {{"owner": "HR Ops", "actions": [{{"step": "Immediate follow-up with employee", "sla_days": 1, "channel": "email", "escalation_if_overdue": "Manager notification"}}]}}
Low risk: {{"owner": "Employee", "actions": [{{"step": "Self-service document upload", "sla_days": 30, "channel": "portal", "escalation_if_overdue": "HR reminder"}}]}}
"""
            
            action_result = parse_json_with_retry(llm, context, ActionPlanSchema)
            
            if action_result:
                return {
                    "owner": action_result.owner,
                    "actions": action_result.actions,
                    "message_templates": action_result.message_templates
                }
            else:
                return self._fallback_action_plan(state)
        
        except Exception as e:
            self.log(f"Action plan generation failed: {e}, using fallback")
            return self._fallback_action_plan(state)
    
    def _fallback_action_plan(self, state: WorkflowState) -> dict:
        """Fallback action plan when LLM fails"""
        risk_level = state.risk_assessment.get("risk_level", "medium")
        
        if risk_level == "critical":
            return {
                "owner": "HR Ops",
                "actions": [
                    {"step": "Immediate employee contact", "sla_days": 1, "channel": "email", "escalation_if_overdue": "Manager escalation"},
                    {"step": "Document collection follow-up", "sla_days": 3, "channel": "email", "escalation_if_overdue": "HR Director notification"}
                ],
                "message_templates": {
                    "employee": "Urgent: Critical documents required",
                    "manager": "Employee compliance issue requires attention",
                    "hr": "Critical compliance case needs immediate action"
                }
            }
        else:
            return {
                "owner": "Employee",
                "actions": [
                    {"step": "Self-service document upload", "sla_days": 14, "channel": "portal", "escalation_if_overdue": "HR reminder"}
                ],
                "message_templates": {
                    "employee": "Please update your documents",
                    "manager": "Employee document update needed",
                    "hr": "Standard compliance follow-up"
                }
            }
    
    def _calculate_final_score(self, state: WorkflowState) -> float:
        """Calculate final compliance score incorporating risk assessment"""
        base_score = state.compliance_eval.base_score
        anomaly_score = state.risk_assessment.get("anomaly_score", 0.5)
        
        # Adjust base score based on AI risk assessment
        risk_penalty = anomaly_score * 20  # Up to 20 point penalty
        final_score = max(0, base_score - risk_penalty)
        
        return round(final_score, 2)
    
    def _send_admin_summary(self, state: WorkflowState, final_score: float, action_plan: dict) -> None:
        """Send summary email to admin recipients"""
        try:
            employee_name = f"{state.profile.first_name} {state.profile.last_name}"
            risk_level = state.risk_assessment.get("risk_level", "unknown")
            
            subject = f"HR Compliance Alert: {employee_name} - {risk_level.upper()} Risk"
            
            body = f"""HR Compliance Analysis Summary

Employee: {employee_name}
Department: {state.profile.department}
Employee ID: {state.profile.employee_id}

COMPLIANCE SCORE: {final_score}%
RISK LEVEL: {risk_level.upper()}

ISSUES FOUND:
- Missing Documents: {len(state.compliance_eval.missing_documents)}
- Expiring Documents: {len(state.compliance_eval.expiring_documents)}
- Expired Documents: {len(state.compliance_eval.expired_documents)}

RECOMMENDED ACTIONS:
Owner: {action_plan.get('owner', 'HR Ops')}
{chr(10).join([f"- {action['step']} (SLA: {action['sla_days']} days)" for action in action_plan.get('actions', [])])}

RISK RATIONALE:
{state.risk_assessment.get('rationale', 'No rationale provided')}

Please review the employee's compliance status and take appropriate action.

---
This is an automated compliance analysis report.
"""
            
            status_codes = send_admin_email(subject, body)
            self.log(f"Admin summary sent with status codes: {status_codes}")
            
        except Exception as e:
            self.log(f"Failed to send admin summary: {e}")