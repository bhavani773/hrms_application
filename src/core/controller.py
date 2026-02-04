from typing import Optional, List, Dict, Any
import uuid
from langgraph.graph import StateGraph, END
from src.tools.validators import WorkflowState
from src.agents.candidate_profile_agent import CandidateProfileAgent
from src.agents.requirements_agent import RequirementsAgent
from src.agents.compliance_eval_agent import ComplianceEvalAgent
from src.agents.risk_scoring_agent import RiskScoringAgent
from src.agents.reminder_planner_agent import ReminderPlannerAgent
from src.agents.recommendation_agent import RecommendationAgent
from src.core.blackboard import Blackboard

class ComplianceController:
    def __init__(self):
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes with wrapper functions
        workflow.add_node("load_profile", self._wrap_agent(CandidateProfileAgent()))
        workflow.add_node("load_requirements", self._wrap_agent(RequirementsAgent()))
        workflow.add_node("evaluate_compliance", self._wrap_agent(ComplianceEvalAgent()))
        workflow.add_node("score_risk", self._wrap_agent(RiskScoringAgent()))
        workflow.add_node("plan_reminders", self._wrap_agent(ReminderPlannerAgent()))
        workflow.add_node("generate_recommendations", self._wrap_agent(RecommendationAgent()))
        
        # Define edges (sequential flow)
        workflow.set_entry_point("load_profile")
        workflow.add_edge("load_profile", "load_requirements")
        workflow.add_edge("load_requirements", "evaluate_compliance")
        workflow.add_edge("evaluate_compliance", "score_risk")
        workflow.add_edge("score_risk", "plan_reminders")
        workflow.add_edge("plan_reminders", "generate_recommendations")
        workflow.add_edge("generate_recommendations", END)
        
        return workflow.compile()
    
    def _wrap_agent(self, agent):
        """Wrap agent to convert between dict and WorkflowState"""
        def wrapper(state_input) -> Dict[str, Any]:
            # Handle both dict and WorkflowState inputs
            if isinstance(state_input, dict):
                state_dict = state_input
            else:
                state_dict = state_input.dict() if hasattr(state_input, 'dict') else dict(state_input)
            
            # Clean up None values and ensure defaults
            clean_dict = {k: v for k, v in state_dict.items() if v is not None}
            if 'finalized' not in clean_dict:
                clean_dict['finalized'] = False
            
            # Convert dict to WorkflowState
            state = WorkflowState(**clean_dict)
            # Run agent
            updated_state = agent.run(state)
            # Convert back to dict, excluding None values
            result_dict = updated_state.dict(exclude_none=True)
            # Ensure finalized is always present
            if 'finalized' not in result_dict:
                result_dict['finalized'] = False
            return result_dict
        return wrapper
    
    def run_for_employee(self, employee_id: uuid.UUID) -> Dict[str, Any]:
        """Run compliance analysis for single employee"""
        print(f"Starting compliance analysis for employee {employee_id}")
        
        initial_state = {
            "candidate_id": employee_id,
            "profile": None,
            "documents": None,
            "requirements": None,
            "policies": None,
            "compliance_eval": None,
            "risk_assessment": None,
            "reminder_summary": None,
            "finalized": False
        }
        
        try:
            final_state = self.graph.invoke(initial_state)
            
            return {
                "employee_id": str(employee_id),
                "success": final_state.get("finalized", False),
                "compliance_score": final_state.get("compliance_eval", {}).get("base_score", 0) if final_state.get("compliance_eval") else 0,
                "risk_level": final_state.get("risk_assessment", {}).get("risk_level", "unknown") if final_state.get("risk_assessment") else "unknown",
                "reminders_sent": sum(final_state.get("reminder_summary", {}).values()) if final_state.get("reminder_summary") else 0
            }
        except Exception as e:
            print(f"Error processing employee {employee_id}: {e}")
            return {
                "employee_id": str(employee_id),
                "success": False,
                "error": str(e)
            }
    
    def run_batch(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Run compliance analysis for batch of employees"""
        print(f"Starting batch compliance analysis (limit: {limit})")
        
        with Blackboard() as bb:
            employee_ids = bb.get_all_employees(limit)
        
        results = []
        processed = 0
        created_analyses = 0
        created_reminders = 0
        emails_sent = 0
        
        for employee_id in employee_ids:
            result = self.run_for_employee(employee_id)
            results.append(result)
            processed += 1
            
            if result.get("success"):
                created_analyses += 1
                created_reminders += result.get("reminders_sent", 0)
                emails_sent += result.get("reminders_sent", 0)
        
        return {
            "processed": processed,
            "created_analyses": created_analyses,
            "created_reminders": created_reminders,
            "emails_sent": emails_sent,
            "results": results
        }