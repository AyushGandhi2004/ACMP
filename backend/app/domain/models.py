from typing import Dict, Optional

from pydantic import BaseModel, Field

from backend.app.domain.enums import SupportedLanguage, SupportedFramework

from uuid import uuid4

class PipelineRequest(BaseModel):
    """What Frontend sends to backend to start the pipeline
        Language is optional, if user doesnt provide it the Profiler Agent will detect it."""
    
    code : str
    language : Optional[SupportedLanguage]

class PipelineResponse(BaseModel):
    """The Response that the backend will send IMMEDIATELY after receiving pipeline request.
    Frontend uses session id to open a websocket and listen for live updates"""
    session_id : str = Field(..., default_factory=lambda : str(uuid4())) #auto generated a unique id
    status : str = Field(..., default="started")
    message : str = Field(..., default="Pipeline started successfully")

class AgentEvent(BaseModel):
    """
    What gets broadcasted over websocket to frontend each time an agent starts, completes or fails.
    Frontend uses this to update the Agent activity pannel in real time.
    """
    agent_name : str
    status : str
    message : str
    data : Optional[dict] = Field(..., default=None)

class ModernizationResult(BaseModel):
    session_id : str 
    original_code : str
    modern_code : str
    language : SupportedLanguage
    framework : SupportedFramework
    transformation_plan : dict
    error_logs : str = Field(..., default="")
    status : str