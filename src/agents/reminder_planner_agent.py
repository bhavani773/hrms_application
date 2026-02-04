from datetime import date, timedelta
from src.core.base_agent import BaseAgent
from src.core.blackboard import Blackboard
from src.tools.validators import WorkflowState
from src.tools.email_utils import send_email

class ReminderPlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__("ReminderPlannerAgent")
    
    def run(self, state: WorkflowState) -> WorkflowState:
        """Create reminders and send notification emails"""
        self.log("Planning and sending document reminders")
        
        if not state.compliance_eval or not state.profile:
            self.log("Missing compliance evaluation or profile data")
            return state
        
        reminder_counts = {"missing": 0, "expiring": 0, "renewal": 0}
        
        with Blackboard() as bb:
            # Handle missing documents
            for doc_type in state.compliance_eval.missing_documents:
                reminder_id = bb.upsert_reminder(
                    employee_id=state.candidate_id,
                    document_type=doc_type,
                    reminder_type="missing",
                    due_date=date.today() + timedelta(days=30)
                )
                
                # Send email for missing document
                success = self._send_missing_document_email(state.profile, doc_type)
                bb.mark_reminder_sent(reminder_id, success)
                
                if success:
                    reminder_counts["missing"] += 1
            
            # Handle expiring documents
            for doc_info in state.compliance_eval.expiring_documents:
                doc_type = doc_info["document_type"]
                expiry_date = date.fromisoformat(doc_info["expiry_date"])
                
                reminder_id = bb.upsert_reminder(
                    employee_id=state.candidate_id,
                    document_type=doc_type,
                    reminder_type="expiring",
                    due_date=expiry_date
                )
                
                # Send email for expiring document
                success = self._send_expiring_document_email(state.profile, doc_type, expiry_date)
                bb.mark_reminder_sent(reminder_id, success)
                
                if success:
                    reminder_counts["expiring"] += 1
            
            # Handle expired documents
            for doc_info in state.compliance_eval.expired_documents:
                doc_type = doc_info["document_type"]
                expiry_date = date.fromisoformat(doc_info["expiry_date"])
                
                reminder_id = bb.upsert_reminder(
                    employee_id=state.candidate_id,
                    document_type=doc_type,
                    reminder_type="renewal",
                    due_date=date.today() + timedelta(days=7)  # Urgent renewal
                )
                
                # Send email for expired document
                success = self._send_expired_document_email(state.profile, doc_type, expiry_date)
                bb.mark_reminder_sent(reminder_id, success)
                
                if success:
                    reminder_counts["renewal"] += 1
        
        state.reminder_summary = reminder_counts
        self.log(f"Sent {sum(reminder_counts.values())} reminder emails")
        
        return state
    
    def _send_missing_document_email(self, profile, doc_type: str) -> bool:
        """Send email for missing document"""
        subject = f"Action Required: Your {doc_type} is missing"
        body = f"""Dear {profile.first_name} {profile.last_name},

Our records indicate that your {doc_type} is missing from your employee file.

Please upload this document as soon as possible to maintain compliance with company policies.

To upload your document:
1. Log into the employee portal
2. Navigate to Documents section
3. Upload your {doc_type}

If you have any questions, please contact HR at hr-team@company.com.

Best regards,
HR Team"""
        
        try:
            # Ensure we're using the correct employee email
            employee_email = profile.email
            print(f"Sending email to: {employee_email} for employee: {profile.first_name} {profile.last_name}")
            status_code = send_email(employee_email, subject, body)
            return status_code in [200, 202]
        except Exception as e:
            print(f"Failed to send missing document email: {e}")
            return False
    
    def _send_expiring_document_email(self, profile, doc_type: str, expiry_date: date) -> bool:
        """Send email for expiring document"""
        days_to_expiry = (expiry_date - date.today()).days
        subject = f"Reminder: Your {doc_type} is expiring on {expiry_date.strftime('%B %d, %Y')}"
        body = f"""Dear {profile.first_name} {profile.last_name},

Your {doc_type} is set to expire in {days_to_expiry} days on {expiry_date.strftime('%B %d, %Y')}.

Please renew and upload the updated document before the expiry date to avoid any compliance issues.

To upload your renewed document:
1. Log into the employee portal
2. Navigate to Documents section
3. Upload your updated {doc_type}

If you have any questions, please contact HR at hr-team@company.com.

Best regards,
HR Team"""
        
        try:
            # Ensure we're using the correct employee email
            employee_email = profile.email
            print(f"Sending email to: {employee_email} for employee: {profile.first_name} {profile.last_name}")
            status_code = send_email(employee_email, subject, body)
            return status_code in [200, 202]
        except Exception as e:
            print(f"Failed to send expiring document email: {e}")
            return False
    
    def _send_expired_document_email(self, profile, doc_type: str, expiry_date: date) -> bool:
        """Send email for expired document"""
        days_overdue = (date.today() - expiry_date).days
        subject = f"URGENT: Your {doc_type} has expired"
        body = f"""Dear {profile.first_name} {profile.last_name},

Your {doc_type} expired {days_overdue} days ago on {expiry_date.strftime('%B %d, %Y')}.

This is an urgent matter that requires immediate attention. Please renew and upload the updated document immediately.

To upload your renewed document:
1. Log into the employee portal
2. Navigate to Documents section
3. Upload your updated {doc_type}

Please contact HR immediately at hr-team@company.com if you need assistance.

Best regards,
HR Team"""
        
        try:
            # Ensure we're using the correct employee email
            employee_email = profile.email
            print(f"Sending email to: {employee_email} for employee: {profile.first_name} {profile.last_name}")
            status_code = send_email(employee_email, subject, body)
            return status_code in [200, 202]
        except Exception as e:
            print(f"Failed to send expired document email: {e}")
            return False