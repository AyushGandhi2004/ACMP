from typing import Dict, Optional

from pydantic import BaseModel, Field

from app.domain.enums import SupportedLanguage, SupportedFramework

from uuid import uuid4

class PipelineRequest(BaseModel):
    """What Frontend sends to backend to start the pipeline
        Language is optional, if user doesnt provide it the Profiler Agent will detect it."""
    
    code : str
    language : Optional[SupportedLanguage]

class PipelineResponse(BaseModel):
    session_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique ID for this pipeline run"
    )
    status: str = Field(
        default="started",          
        description="Initial status of the pipeline"
    )
    message: str = Field(
        default="Pipeline started successfully",   
        description="Human readable message for the frontend"
    )

class AgentEvent(BaseModel):
    """
    What gets broadcast over WebSocket to the frontend
    each time an agent starts, completes, or fails.
    """
    agent_name: str = Field(
        ...,                        
        description="Name of the agent sending this event"
    )
    status: str = Field(
        ...,                        
        description="Current status — running | completed | failed"
    )
    message: str = Field(
        ...,                        
        description="Human readable update message shown in the UI"
    )
    data: Optional[dict] = Field(
        default=None,               # optional — defaults to None
        description="Optional payload"
    )

class ModernizationResult(BaseModel):
    """
    The complete final result after the pipeline finishes.
    Contains both original and modernized code for the diff viewer.
    """
    session_id: str = Field(
        ...,                        
        description="Links this result back to the original pipeline request"
    )
    original_code: str = Field(
        ...,                        
        description="The original legacy code submitted by the user"
    )
    modern_code: str = Field(
        ...,                        
        description="The modernized code produced by the Engineer Agent"
    )
    language: str = Field(
        ...,                        
        description="Detected or provided programming language"
    )
    framework: str = Field(
        ...,                        
        description="Detected framework — unknown if not identified"
    )
    transformation_plan: dict = Field(
        default_factory=dict,       # optional — defaults to empty dict
        description="The step by step plan produced by the Architect Agent"
    )
    error_logs: str = Field(
        default="",                 # optional — defaults to empty string
        description="Stdout and stderr captured from Docker validation run"
    )
    status: str = Field(
        ...,                        
        description="Final pipeline status — success | failed"
    )