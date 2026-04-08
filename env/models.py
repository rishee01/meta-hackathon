from pydantic import BaseModel, Field
from typing import List, Optional

class Observation(BaseModel):
    email_content: str = Field(..., description="The full content of the email to process")
    thread_history: List[str] = Field(default_factory=list, description="Previous emails in the thread for context")
    current_task: str = Field(..., description="Current task level: easy, medium, or hard")

class Action(BaseModel):
    classification: Optional[str] = Field("", description="Classification for easy/medium tasks (spam/not_spam, high/medium/low)")
    reply: Optional[str] = Field("", description="Generated reply for hard task")

class Reward(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0, description="Overall reward score between 0.0 and 1.0")
    feedback: str = Field(..., description="Detailed feedback on the action taken")
    components: Optional[dict] = Field(default_factory=dict, description="Breakdown of score components")