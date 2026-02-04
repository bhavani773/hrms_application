from datetime import date, timedelta
from src.core.base_agent import BaseAgent
from src.tools.validators import WorkflowState, ComplianceEvalState, clamp_score

class ComplianceEvalAgent(BaseAgent):
    def __init__(self):
        super().__init__("ComplianceEvalAgent")
    
    def run(self, state: WorkflowState) -> WorkflowState:
        """Evaluate compliance gaps and compute preliminary scores"""
        self.log("Evaluating compliance status")
        
        if not state.requirements or not state.documents:
            self.log("Missing requirements or documents data")
            return state
        
        # Get current document types
        current_docs = {doc.document_type for doc in state.documents if doc.status in ["submitted", "verified"]}
        
        # Find missing documents
        missing_documents = [req for req in state.requirements if req not in current_docs]
        
        # Find expiring and expired documents
        today = date.today()
        threshold_days = 30  # Default threshold
        if state.policies and "expiry_warning" in state.policies:
            threshold_days = state.policies["expiry_warning"].get("threshold_days", 30)
        
        expiring_documents = []
        expired_documents = []
        
        for doc in state.documents:
            if doc.expiry_date and doc.status in ["submitted", "verified"]:
                days_to_expiry = (doc.expiry_date - today).days
                
                if days_to_expiry < 0:
                    expired_documents.append({
                        "document_type": doc.document_type,
                        "expiry_date": doc.expiry_date.isoformat(),
                        "days_overdue": abs(days_to_expiry)
                    })
                elif days_to_expiry <= threshold_days:
                    expiring_documents.append({
                        "document_type": doc.document_type,
                        "expiry_date": doc.expiry_date.isoformat(),
                        "days_to_expiry": days_to_expiry
                    })
        
        # Calculate base compliance score
        total_required = len(state.requirements)
        missing_count = len(missing_documents)
        expired_count = len(expired_documents)
        
        # Base score: percentage of non-missing documents
        base_score = ((total_required - missing_count) / total_required * 100) if total_required > 0 else 100
        
        # Penalize for expired documents
        if expired_count > 0:
            base_score *= 0.7  # 30% penalty for expired docs
        
        base_score = clamp_score(base_score, 0, 100)
        
        # Determine priority level
        priority_level = "LOW"
        if expired_count > 0:
            priority_level = "CRITICAL"
        elif missing_count > 2 or len(expiring_documents) > 3:
            priority_level = "HIGH"
        elif missing_count > 0 or len(expiring_documents) > 0:
            priority_level = "MEDIUM"
        
        state.compliance_eval = ComplianceEvalState(
            missing_documents=missing_documents,
            expiring_documents=expiring_documents,
            expired_documents=expired_documents,
            base_score=base_score,
            priority_hint=priority_level
        )
        
        self.log(f"Found {missing_count} missing, {len(expiring_documents)} expiring, {expired_count} expired documents. Score: {base_score:.1f}")
        
        return state