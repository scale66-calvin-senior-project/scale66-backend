import time
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

from app.services.ai import anthropic_service, gemini_service
from app.models.common import BasePipelineStep


# Type variables for generic agent input/output types
InputT = TypeVar('InputT')
OutputT = TypeVar('OutputT', bound=BasePipelineStep)


class AgentError(Exception):
    """Base exception for agent-related errors."""
    pass


class ValidationError(AgentError):
    """Raised when input validation fails."""
    pass


class ExecutionError(AgentError):
    """Raised when agent execution fails."""
    pass


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Base class for all agents with common execution flow and error handling."""
    
    def __init__(self):
        self.anthropic = anthropic_service
        self.gemini = gemini_service
        self.agent_name = self.__class__.__name__
    
    @abstractmethod
    async def _validate_input(self, input_data: InputT) -> None:
        """Validate input data before execution."""
        pass
    
    @abstractmethod
    async def _execute(self, input_data: InputT) -> OutputT:
        """Execute the agent's main logic."""
        pass
    
    async def run(self, input_data: InputT) -> OutputT:
        """Main entry point: validates input, executes logic, and tracks execution time."""
        start_time = time.time()
        
        try:
            await self._validate_input(input_data)
            
            output = await self._execute(input_data)
            
            # Track execution time in milliseconds
            execution_time = int((time.time() - start_time) * 1000)
            output.execution_time = execution_time
            
            return output
            
        except ValidationError as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Validation failed: {str(e)}"
            
            return self._create_error_output(error_msg, execution_time_ms)
            
        except ExecutionError as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Execution failed: {str(e)}"
            
            return self._create_error_output(error_msg, execution_time_ms)
            
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Unexpected error: {str(e)}"
            
            return self._create_error_output(error_msg, execution_time_ms)
    
    def _create_error_output(self, error_message: str, execution_time_ms: int) -> OutputT:
        """Create error output and raise ExecutionError."""
        raise ExecutionError(error_message)
