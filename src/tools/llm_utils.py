import os
import json
from typing import Optional
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage

class RiskSchema(BaseModel):
    anomaly_score: float = Field(ge=0, le=1)
    risk_level: str = Field(pattern="^(low|medium|high|critical)$")
    verification_confidence: float = Field(ge=0, le=1)
    rationale: str

class ActionPlanSchema(BaseModel):
    owner: str
    actions: list[dict]
    message_templates: dict

def get_groq_chat(model: str = "llama-3.1-8b-instant") -> ChatGroq:
    """Get ChatGroq instance"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY not set")
    return ChatGroq(groq_api_key=api_key, model_name=model)

def parse_json_with_retry(llm: ChatGroq, prompt: str, schema_class: type, max_retries: int = 1) -> Optional[BaseModel]:
    """Parse LLM response as JSON with retry on failure"""
    for attempt in range(max_retries + 1):
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            content = response.content.strip()
            
            # Extract JSON if wrapped in markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            return schema_class(**data)
        except Exception as e:
            if attempt == max_retries:
                print(f"Failed to parse JSON after {max_retries + 1} attempts: {e}")
                return None
            print(f"Attempt {attempt + 1} failed, retrying: {e}")
    return None