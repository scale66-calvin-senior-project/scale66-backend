from typing import Optional
from pydantic import BaseModel, Field


class BasePipelineStep(BaseModel):
    step_name: str = Field(default="")
    success: bool = Field(default=True)
    error_message: Optional[str] = Field(default=None)
    execution_time: Optional[int] = Field(default=None)
