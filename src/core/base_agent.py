from abc import ABC, abstractmethod
from typing import Dict, Any
from src.tools.validators import WorkflowState

class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def run(self, state: WorkflowState) -> WorkflowState:
        """Execute agent logic and return updated state"""
        pass
    
    def log(self, message: str) -> None:
        """Log agent activity"""
        print(f"[{self.name}] {message}")