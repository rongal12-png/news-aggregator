"""Base agent infrastructure for pipeline processing."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar, Any
import logging
import asyncio

logger = logging.getLogger(__name__)

# Generic types for input and output data
InputT = TypeVar('InputT')
OutputT = TypeVar('OutputT')


class AgentStatus(str, Enum):
    """Agent execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class AgentResult(Generic[OutputT]):
    """Result of an agent execution.

    Attributes:
        status: Execution status
        data: Output data (None if failed/skipped)
        error: Error message if failed
        metadata: Additional information about execution
        execution_time: Time taken in seconds
    """
    status: AgentStatus
    data: OutputT | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0

    @property
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.status == AgentStatus.SUCCESS

    @property
    def is_failed(self) -> bool:
        """Check if execution failed."""
        return self.status == AgentStatus.FAILED

    @property
    def is_skipped(self) -> bool:
        """Check if execution was skipped."""
        return self.status == AgentStatus.SKIPPED


@dataclass
class AgentConfig:
    """Configuration for agent execution.

    Attributes:
        max_retries: Maximum number of retry attempts
        timeout: Timeout in seconds (None for no timeout)
        skip_on_error: Skip to next step instead of failing pipeline
        retry_delay: Delay between retries in seconds
        log_input: Whether to log input data
        log_output: Whether to log output data
    """
    max_retries: int = 3
    timeout: float | None = 300.0  # 5 minutes default
    skip_on_error: bool = False
    retry_delay: float = 1.0
    log_input: bool = False
    log_output: bool = False


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Abstract base class for all pipeline agents.

    Provides:
    - Retry logic with exponential backoff
    - Timeout handling
    - Input/output validation hooks
    - Comprehensive logging
    - Error handling and recovery

    Subclasses must implement:
    - agent_name property
    - _execute() method
    - validate_input() (optional)
    - validate_output() (optional)
    """

    def __init__(self, config: AgentConfig | None = None):
        """Initialize agent with configuration.

        Args:
            config: Agent configuration (uses defaults if None)
        """
        self.config = config or AgentConfig()
        self._logger = logging.getLogger(f"agents.{self.agent_name}")

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Name of the agent for logging and tracking.

        Returns:
            Agent name as string
        """
        pass

    @abstractmethod
    async def _execute(self, input_data: InputT) -> OutputT:
        """Execute the core agent logic.

        This method contains the actual processing logic and must be
        implemented by all subclasses.

        Args:
            input_data: Input data to process

        Returns:
            Processed output data

        Raises:
            Exception: Any processing errors
        """
        pass

    async def validate_input(self, input_data: InputT) -> None:
        """Validate input data before processing.

        Override this method to add input validation logic.
        Should raise ValueError if validation fails.

        Args:
            input_data: Input data to validate

        Raises:
            ValueError: If input validation fails
        """
        pass

    async def validate_output(self, output_data: OutputT) -> None:
        """Validate output data after processing.

        Override this method to add output validation logic.
        Should raise ValueError if validation fails.

        Args:
            output_data: Output data to validate

        Raises:
            ValueError: If output validation fails
        """
        pass

    async def process(self, input_data: InputT) -> AgentResult[OutputT]:
        """Main entry point for agent execution.

        Orchestrates the complete execution flow:
        1. Input validation
        2. Execution with retry logic
        3. Output validation
        4. Result packaging

        Args:
            input_data: Input data to process

        Returns:
            AgentResult with status and output data
        """
        start_time = datetime.now()

        try:
            self._log_start(input_data)

            # Validate input
            await self.validate_input(input_data)

            # Execute with retry logic
            output_data = await self._execute_with_retry(input_data)

            # Validate output
            await self.validate_output(output_data)

            execution_time = (datetime.now() - start_time).total_seconds()
            result = AgentResult(
                status=AgentStatus.SUCCESS,
                data=output_data,
                execution_time=execution_time,
                metadata={'agent': self.agent_name}
            )

            self._log_success(result)
            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            if self.config.skip_on_error:
                self._logger.warning(
                    f"Agent failed but skip_on_error=True: {str(e)}"
                )
                return AgentResult(
                    status=AgentStatus.SKIPPED,
                    error=str(e),
                    execution_time=execution_time,
                    metadata={'agent': self.agent_name}
                )

            result = AgentResult(
                status=AgentStatus.FAILED,
                error=str(e),
                execution_time=execution_time,
                metadata={'agent': self.agent_name}
            )

            self._log_failure(result)
            return result

    async def _execute_with_retry(self, input_data: InputT) -> OutputT:
        """Execute with retry logic and timeout.

        Args:
            input_data: Input data to process

        Returns:
            Processed output data

        Raises:
            Exception: If all retries fail or timeout occurs
        """
        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    delay = self.config.retry_delay * (2 ** (attempt - 1))
                    self._logger.info(
                        f"Retry attempt {attempt}/{self.config.max_retries} "
                        f"after {delay}s delay"
                    )
                    await asyncio.sleep(delay)

                # Execute with timeout if configured
                if self.config.timeout:
                    output_data = await asyncio.wait_for(
                        self._execute(input_data),
                        timeout=self.config.timeout
                    )
                else:
                    output_data = await self._execute(input_data)

                if attempt > 0:
                    self._logger.info(
                        f"Succeeded on retry attempt {attempt}"
                    )

                return output_data

            except asyncio.TimeoutError as e:
                last_exception = e
                self._logger.warning(
                    f"Timeout on attempt {attempt + 1}: "
                    f"{self.config.timeout}s exceeded"
                )

            except Exception as e:
                last_exception = e
                self._logger.warning(
                    f"Error on attempt {attempt + 1}: {str(e)}"
                )

        # All retries exhausted
        raise Exception(
            f"Failed after {self.config.max_retries + 1} attempts. "
            f"Last error: {str(last_exception)}"
        )

    def _log_start(self, input_data: InputT) -> None:
        """Log agent execution start.

        Args:
            input_data: Input data being processed
        """
        log_msg = f"Starting {self.agent_name}"

        if self.config.log_input:
            log_msg += f" with input: {input_data}"

        self._logger.info(log_msg)

    def _log_success(self, result: AgentResult[OutputT]) -> None:
        """Log successful execution.

        Args:
            result: Execution result
        """
        log_msg = (
            f"Completed {self.agent_name} successfully "
            f"in {result.execution_time:.2f}s"
        )

        if self.config.log_output and result.data is not None:
            log_msg += f" with output: {result.data}"

        self._logger.info(log_msg)

    def _log_failure(self, result: AgentResult[OutputT]) -> None:
        """Log failed execution.

        Args:
            result: Execution result
        """
        self._logger.error(
            f"Failed {self.agent_name} after {result.execution_time:.2f}s: "
            f"{result.error}"
        )
