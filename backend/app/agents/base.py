from abc import ABC, abstractmethod

from app.graph.state import AgentState


class BaseAgent(ABC):
    """
    Abstract base class for all ACMP agents.
    Every agent must inherit from this class
    and implement the run() method.

    This enforces a consistent interface across
    all agents — making the system predictable,
    testable and extensible.

    To add a new agent:
        1. Create a new file in app/agents/
        2. Inherit from BaseAgent
        3. Implement the run() method
        4. Add a corresponding node in app/graph/nodes.py
    """

    @abstractmethod
    async def run(self, state: AgentState) -> dict:
        """
        Every agent must implement this method.

        Args:
            state: The current ACMPState object
                   containing all pipeline data

        Returns:
            dict: Partial state update containing
                  only the fields this agent owns
        """
        pass