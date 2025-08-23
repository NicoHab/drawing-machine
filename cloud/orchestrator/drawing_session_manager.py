"""
Drawing Session Manager

Manages drawing sessions, including session lifecycle, state tracking,
and coordination between different drawing modes.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .pipeline_orchestrator import PipelineOrchestrator, OrchestrationError
from shared.models.drawing_session import DrawingMode, SessionStatus, PlaybackSpeed
from shared.models.motor_commands import MotorSafetyLimits


class SessionError(Exception):
    """Exception raised when session management fails."""
    
    def __init__(self, message: str, session_id: Optional[str] = None):
        self.session_id = session_id
        super().__init__(message)


@dataclass
class SessionMetrics:
    """Session performance metrics."""
    planned_duration_minutes: float = 0.0
    actual_duration_minutes: float = 0.0
    epochs_completed: int = 0
    commands_executed: int = 0
    errors_encountered: int = 0


class SimpleDrawingSession:
    """Simplified drawing session for the orchestrator."""
    
    def __init__(self, session_id: str, mode: DrawingMode, name: str, 
                 description: str, config: dict, safety_limits: MotorSafetyLimits):
        self.session_id = session_id
        self.mode = mode
        self.name = name
        self.description = description
        self.status = SessionStatus.CREATED
        self.config = config
        self.safety_limits = safety_limits
        self.created_time = datetime.now()
        self.actual_start_time: Optional[datetime] = None
        self.actual_end_time: Optional[datetime] = None
        self.metrics = SessionMetrics()
        self.clients = {}
    
    def to_dict(self) -> dict:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "mode": self.mode.value,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "created_time": self.created_time.isoformat(),
            "actual_start_time": self.actual_start_time.isoformat() if self.actual_start_time else None,
            "actual_end_time": self.actual_end_time.isoformat() if self.actual_end_time else None,
            "metrics": {
                "planned_duration_minutes": self.metrics.planned_duration_minutes,
                "actual_duration_minutes": self.metrics.actual_duration_minutes,
                "epochs_completed": self.metrics.epochs_completed,
                "commands_executed": self.metrics.commands_executed,
                "errors_encountered": self.metrics.errors_encountered,
            }
        }


class DrawingSessionManager:
    """
    Manages drawing sessions across different modes and states.
    
    Coordinates session lifecycle, state persistence, and mode-specific
    orchestration for the drawing machine system.
    """
    
    def __init__(
        self,
        session_storage_path: Optional[Path] = None,
        safety_limits: Optional[MotorSafetyLimits] = None,
    ):
        self.storage_path = session_storage_path or Path("./sessions")
        self.storage_path.mkdir(exist_ok=True)
        
        # Active sessions
        self.active_sessions: Dict[str, SimpleDrawingSession] = {}
        self.session_orchestrators: Dict[str, PipelineOrchestrator] = {}
        
        # Configuration
        self.safety_limits = safety_limits or MotorSafetyLimits()
        self.config = {
            "max_concurrent_sessions": 1,  # Only one active session for now
            "session_timeout_hours": 24,
            "auto_save_interval_minutes": 5,
            "cleanup_completed_sessions_hours": 48,
        }
        
        # Statistics
        self.stats = {
            "total_sessions_created": 0,
            "total_sessions_completed": 0,
            "total_sessions_failed": 0,
            "average_session_duration_minutes": 0.0,
        }
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._auto_save_task: Optional[asyncio.Task] = None
        
        # Event callbacks
        self.event_callbacks: Dict[str, List] = {}
        
        self.logger = logging.getLogger(__name__)
        
        # Start background tasks
        asyncio.create_task(self._start_background_tasks())
    
    async def create_session(
        self,
        mode: DrawingMode,
        name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[Dict] = None,
    ) -> SimpleDrawingSession:
        """
        Create a new drawing session.
        
        Args:
            mode: Drawing mode (blockchain, manual, offline, hybrid)
            name: Optional session name
            description: Optional session description
            config: Optional mode-specific configuration
            
        Returns:
            DrawingSession: Created session
            
        Raises:
            SessionError: If session creation fails
        """
        try:
            # Check concurrent session limit
            if len(self.active_sessions) >= self.config["max_concurrent_sessions"]:
                raise SessionError("Maximum concurrent sessions reached")
            
            # Create session
            session_id = str(uuid.uuid4())
            session = SimpleDrawingSession(
                session_id=session_id,
                mode=mode,
                name=name or f"{mode.value}_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                description=description or f"Drawing session in {mode.value} mode",
                config=config or {},
                safety_limits=self.safety_limits,
            )
            
            # Store session
            self.active_sessions[session_id] = session
            await self._save_session(session)
            
            # Update statistics
            self.stats["total_sessions_created"] += 1
            
            self.logger.info(f"Created session {session_id} in {mode.value} mode")
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            raise SessionError(f"Session creation failed: {e}")
    
    async def start_session(self, session_id: str, client_id: str = None) -> bool:
        """
        Start a drawing session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if session started successfully
            
        Raises:
            SessionError: If session start fails
        """
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                raise SessionError(f"Session {session_id} not found", session_id)
            
            if session.status != SessionStatus.CREATED:
                raise SessionError(f"Session {session_id} cannot be started - status: {session.status}", session_id)
            
            self.logger.info(f"Starting session {session_id}")
            
            # Update session status
            session.status = SessionStatus.INITIALIZING
            session.actual_start_time = datetime.now()
            await self._save_session(session)
            
            # Start mode-specific orchestration
            success = await self._start_mode_orchestration(session)
            
            if success:
                session.status = SessionStatus.ACTIVE
                self.logger.info(f"Session {session_id} started successfully")
            else:
                session.status = SessionStatus.FAILED
                self.logger.error(f"Session {session_id} failed to start")
            
            await self._save_session(session)
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to start session {session_id}: {e}")
            if session_id in self.active_sessions:
                self.active_sessions[session_id].status = SessionStatus.FAILED
            raise SessionError(f"Session start failed: {e}", session_id)
    
    async def stop_session(self, session_id: str) -> bool:
        """
        Stop a drawing session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if session stopped successfully
        """
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                raise SessionError(f"Session {session_id} not found", session_id)
            
            self.logger.info(f"Stopping session {session_id}")
            
            # Update session status
            session.status = SessionStatus.STOPPING
            await self._save_session(session)
            
            # Stop orchestration
            success = await self._stop_mode_orchestration(session_id)
            
            # Update final status
            session.status = SessionStatus.COMPLETED if success else SessionStatus.FAILED
            session.actual_end_time = datetime.now()
            
            # Calculate metrics
            if session.actual_start_time and session.actual_end_time:
                duration = session.actual_end_time - session.actual_start_time
                session.metrics.actual_duration_minutes = duration.total_seconds() / 60
            
            await self._save_session(session)
            
            # Update statistics
            if success:
                self.stats["total_sessions_completed"] += 1
            else:
                self.stats["total_sessions_failed"] += 1
            
            self.logger.info(f"Session {session_id} stopped")
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to stop session {session_id}: {e}")
            return False
    
    async def pause_session(self, session_id: str) -> bool:
        """Pause an active session."""
        try:
            session = self.active_sessions.get(session_id)
            if not session or session.status != SessionStatus.ACTIVE:
                raise SessionError(f"Session {session_id} cannot be paused", session_id)
            
            session.status = SessionStatus.PAUSED
            await self._save_session(session)
            
            # Pause orchestration if needed
            if session_id in self.session_orchestrators:
                orchestrator = self.session_orchestrators[session_id]
                await orchestrator.stop_pipeline()
            
            self.logger.info(f"Session {session_id} paused")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to pause session {session_id}: {e}")
            return False
    
    async def resume_session(self, session_id: str) -> bool:
        """Resume a paused session."""
        try:
            session = self.active_sessions.get(session_id)
            if not session or session.status != SessionStatus.PAUSED:
                raise SessionError(f"Session {session_id} cannot be resumed", session_id)
            
            session.status = SessionStatus.ACTIVE
            await self._save_session(session)
            
            # Resume orchestration
            success = await self._start_mode_orchestration(session)
            
            if not success:
                session.status = SessionStatus.FAILED
                await self._save_session(session)
            
            self.logger.info(f"Session {session_id} resumed")
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to resume session {session_id}: {e}")
            return False
    
    async def get_session_status(self, session_id: str) -> Optional[Dict]:
        """Get detailed session status."""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        status = {
            "session_id": session.session_id,
            "name": session.name,
            "mode": session.mode.value,
            "status": session.status.value,
            "created_time": session.created_time.isoformat(),
            "actual_start_time": session.actual_start_time.isoformat() if session.actual_start_time else None,
            "actual_end_time": session.actual_end_time.isoformat() if session.actual_end_time else None,
            "metrics": {
                "planned_duration_minutes": session.metrics.planned_duration_minutes,
                "actual_duration_minutes": session.metrics.actual_duration_minutes,
                "epochs_completed": session.metrics.epochs_completed,
                "commands_executed": session.metrics.commands_executed,
                "errors_encountered": session.metrics.errors_encountered,
            }
        }
        
        # Add orchestrator status if available
        if session_id in self.session_orchestrators:
            orchestrator = self.session_orchestrators[session_id]
            pipeline_status = await orchestrator.get_pipeline_status()
            status["pipeline_status"] = pipeline_status
        
        return status
    
    async def list_sessions(self, include_completed: bool = False) -> List[Dict]:
        """List all sessions."""
        sessions = []
        
        for session in self.active_sessions.values():
            if not include_completed and session.status == SessionStatus.COMPLETED:
                continue
            
            sessions.append({
                "session_id": session.session_id,
                "name": session.name,
                "mode": session.mode.value,
                "status": session.status.value,
                "created_time": session.created_time.isoformat(),
                "duration_minutes": session.metrics.actual_duration_minutes or 0,
            })
        
        return sorted(sessions, key=lambda x: x["created_time"], reverse=True)
    
    async def get_manager_stats(self) -> Dict:
        """Get session manager statistics."""
        return {
            "statistics": self.stats.copy(),
            "active_sessions": len(self.active_sessions),
            "configuration": self.config.copy(),
            "storage_path": str(self.storage_path),
        }
    
    async def _start_mode_orchestration(self, session: SimpleDrawingSession) -> bool:
        """Start mode-specific orchestration."""
        try:
            if session.mode == DrawingMode.BLOCKCHAIN:
                return await self._start_blockchain_mode(session)
            elif session.mode == DrawingMode.MANUAL:
                return await self._start_manual_mode(session)
            elif session.mode == DrawingMode.OFFLINE:
                return await self._start_offline_mode(session)
            elif session.mode == DrawingMode.HYBRID:
                return await self._start_hybrid_mode(session)
            else:
                raise SessionError(f"Unsupported session mode: {session.mode}")
                
        except Exception as e:
            self.logger.error(f"Failed to start {session.mode.value} orchestration: {e}")
            return False
    
    async def _start_blockchain_mode(self, session: SimpleDrawingSession) -> bool:
        """Start blockchain mode orchestration."""
        try:
            orchestrator = PipelineOrchestrator(self.safety_limits)
            self.session_orchestrators[session.session_id] = orchestrator
            
            return await orchestrator.start_pipeline(session)
            
        except OrchestrationError as e:
            self.logger.error(f"Blockchain orchestration failed: {e}")
            return False
    
    async def _start_manual_mode(self, session: SimpleDrawingSession) -> bool:
        """Start manual mode (user-controlled)."""
        # Manual mode doesn't need orchestration - user controls directly
        self.logger.info(f"Manual mode session {session.session_id} ready for user control")
        return True
    
    async def _start_offline_mode(self, session: SimpleDrawingSession) -> bool:
        """Start offline mode (pre-recorded sequence playback)."""
        # Would load and play pre-recorded sequences
        self.logger.info(f"Offline mode not fully implemented for session {session.session_id}")
        return True
    
    async def _start_hybrid_mode(self, session: SimpleDrawingSession) -> bool:
        """Start hybrid mode (combination of blockchain and manual)."""
        # Would combine blockchain automation with manual overrides
        self.logger.info(f"Hybrid mode not fully implemented for session {session.session_id}")
        return True
    
    async def _stop_mode_orchestration(self, session_id: str) -> bool:
        """Stop mode-specific orchestration."""
        try:
            if session_id in self.session_orchestrators:
                orchestrator = self.session_orchestrators[session_id]
                success = await orchestrator.stop_pipeline()
                del self.session_orchestrators[session_id]
                return success
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop orchestration for session {session_id}: {e}")
            return False
    
    async def _save_session(self, session: SimpleDrawingSession) -> None:
        """Save session to persistent storage."""
        try:
            session_file = self.storage_path / f"{session.session_id}.json"
            session_data = session.to_dict()
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save session {session.session_id}: {e}")
    
    async def _start_background_tasks(self) -> None:
        """Start background maintenance tasks."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._auto_save_task = asyncio.create_task(self._auto_save_loop())
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup of old sessions."""
        while True:
            try:
                await self._cleanup_old_sessions()
                await asyncio.sleep(3600)  # Run every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(3600)
    
    async def _auto_save_loop(self) -> None:
        """Background auto-save of active sessions."""
        while True:
            try:
                for session in self.active_sessions.values():
                    await self._save_session(session)
                
                await asyncio.sleep(self.config["auto_save_interval_minutes"] * 60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Auto-save loop error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _cleanup_old_sessions(self) -> None:
        """Clean up old completed sessions."""
        cutoff_time = datetime.now() - timedelta(hours=self.config["cleanup_completed_sessions_hours"])
        
        sessions_to_remove = []
        for session_id, session in self.active_sessions.items():
            if (session.status == SessionStatus.COMPLETED and 
                session.actual_end_time and 
                session.actual_end_time < cutoff_time):
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
            self.logger.info(f"Cleaned up old session {session_id}")
    
    def register_event_callback(self, event_name: str, callback):
        """Register event callback."""
        if event_name not in self.event_callbacks:
            self.event_callbacks[event_name] = []
        self.event_callbacks[event_name].append(callback)
    
    async def _emit_event(self, event_name: str, data):
        """Emit event to registered callbacks."""
        if event_name in self.event_callbacks:
            for callback in self.event_callbacks[event_name]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    self.logger.error(f"Event callback error for {event_name}: {e}")
    
    def get_active_sessions(self):
        """Get list of active sessions."""
        return [session for session in self.active_sessions.values() 
                if session.status not in [SessionStatus.COMPLETED, SessionStatus.FAILED]]
    
    def get_system_status(self):
        """Get system status."""
        return {
            "active_sessions": len(self.active_sessions),
            "stats": self.stats.copy(),
            "config": self.config.copy()
        }
    
    async def join_session(self, session_id: str, client_id: str, client_info: dict) -> bool:
        """Join a client to a session."""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return False
            
            # Add client info to session (simplified)
            if not hasattr(session, 'clients'):
                session.clients = {}
            session.clients[client_id] = client_info
            
            await self._emit_event("client_joined", {
                "session": session,
                "client_id": client_id,
                "client_info": client_info
            })
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to join session {session_id}: {e}")
            return False
    
    async def leave_session(self, session_id: str, client_id: str) -> bool:
        """Remove a client from a session."""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return False
            
            # Remove client from session
            if hasattr(session, 'clients') and client_id in session.clients:
                del session.clients[client_id]
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to leave session {session_id}: {e}")
            return False
    
    async def complete_session(self, session_id: str, client_id: str) -> bool:
        """Complete a session (alias for stop_session)."""
        return await self.stop_session(session_id)