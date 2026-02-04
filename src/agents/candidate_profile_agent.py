from src.core.base_agent import BaseAgent
from src.core.blackboard import Blackboard
from src.tools.validators import WorkflowState, EmployeeProfileState, DocumentState

class CandidateProfileAgent(BaseAgent):
    def __init__(self):
        super().__init__("CandidateProfileAgent")
    
    def run(self, state: WorkflowState) -> WorkflowState:
        """Load employee profile and current document states"""
        self.log(f"Loading profile for employee {state.candidate_id}")
        
        with Blackboard() as bb:
            # Get employee profile
            profile_data = bb.get_employee_profile(state.candidate_id)
            if not profile_data:
                self.log(f"Employee {state.candidate_id} not found")
                return state
            
            state.profile = EmployeeProfileState(**profile_data)
            
            # Get employee documents
            docs_data = bb.get_employee_documents(state.candidate_id)
            state.documents = [DocumentState(**doc) for doc in docs_data]
            
            self.log(f"Loaded profile for {state.profile.first_name} {state.profile.last_name} with {len(state.documents)} documents")
        
        return state