from src.core.base_agent import BaseAgent
from src.core.blackboard import Blackboard
from src.tools.validators import WorkflowState

class RequirementsAgent(BaseAgent):
    def __init__(self):
        super().__init__("RequirementsAgent")
    
    def run(self, state: WorkflowState) -> WorkflowState:
        """Load mandatory and role-specific document requirements"""
        self.log("Loading document requirements")
        
        with Blackboard() as bb:
            # Get mandatory requirements
            mandatory_reqs = bb.get_mandatory_requirements()
            
            # Get role-specific requirements if position is available
            role_reqs = []
            if state.profile and hasattr(state.profile, 'position_id'):
                role_reqs = bb.get_requirements_for_role(state.profile.position_id)
            
            # Merge requirements (remove duplicates)
            all_reqs = list(set(mandatory_reqs + role_reqs))
            state.requirements = all_reqs
            
            # Get compliance policies
            state.policies = bb.get_org_compliance_policies()
            
            self.log(f"Loaded {len(all_reqs)} document requirements and {len(state.policies)} policies")
        
        return state