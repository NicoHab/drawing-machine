"""
Pipeline Orchestrator

Orchestrates the complete blockchain-to-motor control pipeline,
coordinating data fetching, processing, and motor command execution.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable

from cloud.data_aggregator import DataProcessor, ProcessingError
from edge.motor_controller import HardwareInterface, MotorDriverError, SafetyViolationError
from shared.models.blockchain_data import EthereumDataSnapshot
from shared.models.motor_commands import MotorVelocityCommands, MotorSafetyLimits
from shared.models.drawing_session import DrawingSession, DrawingMode, SessionStatus


class OrchestrationError(Exception):
    """Exception raised when pipeline orchestration fails."""
    
    def __init__(self, message: str, stage: str, underlying_error: Optional[Exception] = None):
        self.stage = stage
        self.underlying_error = underlying_error
        super().__init__(message)


class PipelineOrchestrator:
    """
    Orchestrates the complete blockchain-to-motor control pipeline.
    
    Manages the flow from blockchain data fetching through motor command
    generation to hardware execution, with comprehensive error handling
    and monitoring.
    """
    
    def __init__(
        self,
        safety_limits: Optional[MotorSafetyLimits] = None,
        motor_host: str = "localhost",
        motor_port: int = 8888,
    ):
        # Initialize components
        self.data_processor = DataProcessor(safety_limits)
        self.hardware_interface = HardwareInterface(motor_host, motor_port, safety_limits)
        
        # Pipeline configuration
        self.config = {
            "execution_interval_seconds": 3.4,  # Time between command executions
            "max_consecutive_errors": 5,
            "retry_delay_seconds": 2.0,
            "emergency_stop_threshold": 3,  # Critical errors before emergency stop
            "health_check_interval_seconds": 30.0,
        }
        
        # State tracking
        self.is_running = False
        self.current_session: Optional[DrawingSession] = None
        self.pipeline_stats = {
            "total_cycles": 0,
            "successful_cycles": 0,
            "failed_cycles": 0,
            "consecutive_errors": 0,
            "last_execution_time": None,
            "average_cycle_time_ms": 0.0,
        }
        
        # Error tracking
        self._recent_errors: List[Dict] = []
        self._critical_error_count = 0
        
        # Async tasks
        self._pipeline_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self.on_cycle_complete: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        self.logger = logging.getLogger(__name__)
    
    async def start_pipeline(self, session: DrawingSession) -> bool:
        """
        Start the blockchain-to-motor pipeline.
        
        Args:
            session: Drawing session configuration
            
        Returns:
            bool: True if pipeline started successfully
            
        Raises:
            OrchestrationError: If pipeline startup fails
        """
        if self.is_running:
            raise OrchestrationError("Pipeline is already running", "startup")
        
        try:
            self.logger.info(f"Starting pipeline for session {session.session_id}")
            
            # Initialize hardware connection
            if not await self._initialize_hardware():
                raise OrchestrationError("Hardware initialization failed", "hardware_init")
            
            # Validate session configuration
            if not self._validate_session(session):
                raise OrchestrationError("Invalid session configuration", "session_validation")
            
            # Set current session
            self.current_session = session
            self.is_running = True
            
            # Start pipeline tasks
            self._pipeline_task = asyncio.create_task(self._pipeline_loop())
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            self.logger.info(f"Pipeline started successfully for session {session.session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start pipeline: {e}")
            await self._cleanup()
            raise OrchestrationError(f"Pipeline startup failed: {e}", "startup", e)
    
    async def stop_pipeline(self) -> bool:
        """
        Stop the pipeline gracefully.
        
        Returns:
            bool: True if pipeline stopped successfully
        """
        if not self.is_running:
            return True
        
        try:
            self.logger.info("Stopping pipeline...")
            self.is_running = False
            
            # Stop background tasks
            if self._pipeline_task:
                self._pipeline_task.cancel()
                try:
                    await self._pipeline_task
                except asyncio.CancelledError:
                    pass
            
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
            
            # Emergency stop motors
            await self.hardware_interface.emergency_stop()
            
            # Cleanup
            await self._cleanup()
            
            self.logger.info("Pipeline stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping pipeline: {e}")
            return False
    
    async def execute_single_cycle(self, epoch: int = 0) -> bool:
        """
        Execute a single pipeline cycle for testing.
        
        Args:
            epoch: Drawing epoch number
            
        Returns:
            bool: True if cycle executed successfully
        """
        try:
            self.logger.debug(f"Executing single cycle for epoch {epoch}")
            
            start_time = datetime.now()
            
            # Process blockchain data
            commands = await self.data_processor.process_current_data(epoch)
            
            # Execute motor commands
            if self.hardware_interface.is_connected:
                await self.hardware_interface.execute_motor_commands(commands)
            else:
                self.logger.warning("Hardware not connected - simulating command execution")
            
            # Update statistics
            cycle_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_cycle_stats(cycle_time, True)
            
            self.logger.debug(f"Single cycle completed in {cycle_time:.1f}ms")
            return True
            
        except Exception as e:
            self.logger.error(f"Single cycle failed: {e}")
            self._update_cycle_stats(0, False)
            return False
    
    async def get_pipeline_status(self) -> Dict:
        """Get comprehensive pipeline status."""
        hardware_status = await self.hardware_interface.get_system_status() if self.hardware_interface.is_connected else {}
        processing_status = self.data_processor.get_processing_status()
        
        return {
            "is_running": self.is_running,
            "current_session": {
                "session_id": self.current_session.session_id if self.current_session else None,
                "mode": self.current_session.mode.value if self.current_session else None,
                "status": self.current_session.status.value if self.current_session else None,
            } if self.current_session else None,
            "hardware_status": hardware_status,
            "data_processing_status": processing_status,
            "pipeline_statistics": self.pipeline_stats.copy(),
            "configuration": self.config.copy(),
            "health_status": self._get_health_status(),
        }
    
    async def emergency_stop(self) -> None:
        """Execute emergency stop across entire pipeline."""
        self.logger.warning("Emergency stop initiated")
        
        try:
            # Stop pipeline
            await self.stop_pipeline()
            
            # Emergency stop hardware
            if self.hardware_interface.is_connected:
                await self.hardware_interface.emergency_stop()
            
            self._critical_error_count += 1
            self.logger.warning("Emergency stop completed")
            
        except Exception as e:
            self.logger.error(f"Error during emergency stop: {e}")
    
    def update_configuration(self, new_config: Dict) -> None:
        """Update pipeline configuration."""
        self.config.update(new_config)
        self.logger.info(f"Updated pipeline configuration: {new_config}")
    
    async def _pipeline_loop(self) -> None:
        """Main pipeline execution loop."""
        epoch = 0
        
        while self.is_running:
            try:
                cycle_start = datetime.now()
                
                # Check if we should continue based on error count
                if self.pipeline_stats["consecutive_errors"] >= self.config["max_consecutive_errors"]:
                    self.logger.error("Too many consecutive errors - stopping pipeline")
                    await self.emergency_stop()
                    break
                
                # Process blockchain data and execute commands
                success = await self._execute_pipeline_cycle(epoch)
                
                if success:
                    self.pipeline_stats["consecutive_errors"] = 0
                    epoch += 1
                else:
                    self.pipeline_stats["consecutive_errors"] += 1
                
                # Notify completion if callback is set
                if self.on_cycle_complete:
                    await self.on_cycle_complete(epoch, success)
                
                # Wait for next cycle
                cycle_time = (datetime.now() - cycle_start).total_seconds()
                wait_time = max(0, self.config["execution_interval_seconds"] - cycle_time)
                
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Pipeline loop error: {e}")
                self._record_error("pipeline_loop", str(e), e)
                
                if self.on_error:
                    await self.on_error(e)
                
                await asyncio.sleep(self.config["retry_delay_seconds"])
    
    async def _execute_pipeline_cycle(self, epoch: int) -> bool:
        """Execute a single pipeline cycle."""
        try:
            cycle_start = datetime.now()
            
            # Process blockchain data
            commands = await self.data_processor.process_current_data(epoch)
            
            # Execute motor commands
            await self.hardware_interface.execute_motor_commands(commands)
            
            # Update statistics
            cycle_time = (datetime.now() - cycle_start).total_seconds() * 1000
            self._update_cycle_stats(cycle_time, True)
            
            self.logger.debug(f"Pipeline cycle {epoch} completed in {cycle_time:.1f}ms")
            return True
            
        except (ProcessingError, MotorDriverError, SafetyViolationError) as e:
            self.logger.error(f"Pipeline cycle {epoch} failed: {e}")
            self._record_error("pipeline_cycle", str(e), e)
            self._update_cycle_stats(0, False)
            
            # Check if this is a critical error requiring emergency stop
            if isinstance(e, SafetyViolationError):
                self._critical_error_count += 1
                if self._critical_error_count >= self.config["emergency_stop_threshold"]:
                    await self.emergency_stop()
            
            return False
    
    async def _health_check_loop(self) -> None:
        """Background health monitoring loop."""
        while self.is_running:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.config["health_check_interval_seconds"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check error: {e}")
                await asyncio.sleep(self.config["health_check_interval_seconds"])
    
    async def _perform_health_check(self) -> None:
        """Perform system health check."""
        # Check hardware connection
        if not self.hardware_interface.is_connected:
            self.logger.warning("Hardware interface disconnected")
        
        # Check data processing health
        processing_status = self.data_processor.get_processing_status()
        if processing_status["status"] != "healthy":
            self.logger.warning("Data processing system unhealthy")
        
        # Check error rates
        if self.pipeline_stats["consecutive_errors"] > 2:
            self.logger.warning(f"High error rate: {self.pipeline_stats['consecutive_errors']} consecutive errors")
    
    async def _initialize_hardware(self) -> bool:
        """Initialize hardware interface."""
        try:
            return await self.hardware_interface.initialize()
        except Exception as e:
            self.logger.error(f"Hardware initialization failed: {e}")
            return False
    
    def _validate_session(self, session: DrawingSession) -> bool:
        """Validate session configuration."""
        if session.mode != DrawingMode.BLOCKCHAIN:
            self.logger.error(f"Unsupported session mode: {session.mode}")
            return False
        
        if session.status != SessionStatus.CREATED:
            self.logger.error(f"Invalid session status: {session.status}")
            return False
        
        return True
    
    async def _cleanup(self) -> None:
        """Cleanup resources."""
        try:
            await self.hardware_interface.shutdown()
            self.current_session = None
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
    
    def _update_cycle_stats(self, cycle_time_ms: float, success: bool) -> None:
        """Update pipeline cycle statistics."""
        self.pipeline_stats["total_cycles"] += 1
        self.pipeline_stats["last_execution_time"] = datetime.now().isoformat()
        
        if success:
            self.pipeline_stats["successful_cycles"] += 1
        else:
            self.pipeline_stats["failed_cycles"] += 1
        
        # Update average cycle time
        if cycle_time_ms > 0:
            total_cycles = self.pipeline_stats["total_cycles"]
            current_avg = self.pipeline_stats["average_cycle_time_ms"]
            new_avg = ((current_avg * (total_cycles - 1)) + cycle_time_ms) / total_cycles
            self.pipeline_stats["average_cycle_time_ms"] = new_avg
    
    def _record_error(self, stage: str, message: str, exception: Optional[Exception] = None) -> None:
        """Record error for analysis."""
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "message": message,
            "exception_type": type(exception).__name__ if exception else None,
        }
        
        self._recent_errors.append(error_record)
        
        # Keep only recent errors
        if len(self._recent_errors) > 50:
            self._recent_errors = self._recent_errors[-50:]
    
    def _get_health_status(self) -> str:
        """Get overall pipeline health status."""
        if not self.is_running:
            return "stopped"
        
        if self._critical_error_count >= self.config["emergency_stop_threshold"]:
            return "critical"
        
        if self.pipeline_stats["consecutive_errors"] > 2:
            return "degraded"
        
        if not self.hardware_interface.is_connected:
            return "hardware_disconnected"
        
        return "healthy"