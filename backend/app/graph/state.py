import operator
from typing import Annotated, TypedDict

from pydantic import BaseModel


class AgentState(TypedDict):
    """
    This is the common structure that the graph will use for the complete flow.
    It is the shared memory that flows in the pipeline.
    """

    session_id : str
    original_code : str
    metadata : dict
    unit_tests : str
    modern_code : str
    transformation_plan : dict
    error_logs : str
    status : str
    retry_count : int
    events : Annotated[list, operator.add]
