"""
Cloud Orchestrator

Main coordination service that manages the complete Drawing Machine system,
providing centralized control, monitoring, and communication hub for all components.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum

import websockets
from websockets.server import WebSocketServerProtocol

from .drawing_session_manager import DrawingSessionManager, SessionError
from ..data_aggregator.data_processor import DataProcessor
from shared.models.motor_commands import MotorVelocityCommands, ControlMode
from shared.models.blockchain_data import EthereumDataSnapshot
from shared.models.drawing_session import DrawingMode, SessionStatus


class ServiceStatus(str, Enum):
    """Service status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class ConnectedClient:
    """Information about a connected client."""
    client_id: str
    websocket: WebSocketServerProtocol
    connected_at: float
    client_type: str  # "web_ui", "mobile_app", "api_client"
    user_info: Dict
    current_session: Optional[str]
    last_activity: float


@dataclass
class SystemHealth:
    """Overall system health information."""
    status: ServiceStatus
    services: Dict[str, ServiceStatus]
    active_sessions: int
    connected_clients: int
    uptime_seconds: float
    memory_usage_mb: float
    error_rate_per_minute: float
    last_updated: float


class CloudOrchestrator:
    """
    Central coordination service for the Drawing Machine system.
    
    Provides:
    - WebSocket hub for all client connections
    - Session management and coordination
    - Service health monitoring
    - Real-time event broadcasting
    - API gateway functionality
    - System-wide error handling and recovery
    """
    
    def __init__(self, host: str = "localhost", port: int = 8768):
        self.host = host
        self.port = port
        self.logger = logging.getLogger(__name__)
        
        # Core services
        self.session_manager = DrawingSessionManager()
        self.data_processor = DataProcessor()
        
        # WebSocket clients
        self.clients: Dict[str, ConnectedClient] = {}
        self.client_sessions: Dict[str, Set[str]] = {}  # session_id -> set of client_ids
        
        # System state
        self.start_time = time.time()
        self.system_health = SystemHealth(
            status=ServiceStatus.HEALTHY,
            services={},
            active_sessions=0,
            connected_clients=0,
            uptime_seconds=0,
            memory_usage_mb=0,
            error_rate_per_minute=0,
            last_updated=time.time()
        )
        
        # Event system
        self.event_handlers: Dict[str, List[Callable]] = {
            "session_created": [],
            "session_started": [],
            "session_completed": [],
            "client_connected": [],
            "client_disconnected": [],
            "motor_command": [],
            "system_error": [],
            "health_check": []
        }
        
        # Statistics
        self.stats = {
            "total_connections": 0,
            "total_sessions": 0,
            "total_motor_commands": 0,
            "total_blockchain_snapshots": 0,
            "errors_last_hour": 0,
            "peak_concurrent_clients": 0
        }
        
        # Background tasks
        self._health_check_task: Optional[asyncio.Task] = None
        self._stats_update_task: Optional[asyncio.Task] = None
        
    async def start_server(self):
        """Start the Cloud Orchestrator WebSocket server."""
        self.logger.info(f"Starting Cloud Orchestrator on {self.host}:{self.port}")
        
        # Start background tasks
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._stats_update_task = asyncio.create_task(self._stats_update_loop())
        
        # Register session manager callbacks
        self.session_manager.register_event_callback("session_created", self._on_session_created)
        self.session_manager.register_event_callback("session_started", self._on_session_started)
        self.session_manager.register_event_callback("session_completed", self._on_session_completed)
        self.session_manager.register_event_callback("client_joined", self._on_client_joined_session)
        
        # Start WebSocket server
        async with websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10,
            max_size=1024*1024  # 1MB max message size
        ):
            self.logger.info("Cloud Orchestrator server started")
            self.system_health.status = ServiceStatus.HEALTHY
            await self._emit_event("server_started", {"timestamp": time.time()})
            
            # Keep server running
            await asyncio.Future()
    
    async def handle_client(self, websocket: WebSocketServerProtocol):
        """Handle new WebSocket client connection."""
        client_id = str(uuid.uuid4())
        client_addr = websocket.remote_address
        
        client = ConnectedClient(
            client_id=client_id,
            websocket=websocket,
            connected_at=time.time(),
            client_type="unknown",
            user_info={},
            current_session=None,
            last_activity=time.time()
        )
        
        self.clients[client_id] = client
        self.stats["total_connections"] += 1
        self.stats["peak_concurrent_clients"] = max(
            self.stats["peak_concurrent_clients"], 
            len(self.clients)
        )
        
        self.logger.info(f"Client connected: {client_id} from {client_addr}")
        
        try:
            # Send initial system state with motor states
            await self._send_system_state_to_client(client_id)
            await self._emit_event("client_connected", {"client_id": client_id})
            
            # Handle messages
            async for message in websocket:
                await self.handle_message(client_id, message)
                client.last_activity = time.time()
                
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Client disconnected: {client_id}")
        except Exception as e:
            self.logger.error(f"Error handling client {client_id}: {e}")
        finally:
            await self._cleanup_client(client_id)
    
    async def handle_message(self, client_id: str, message: str):
        """Handle incoming WebSocket message from client."""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            print(f"CLOUD ORCHESTRATOR: Received {message_type} from {client_id}: {data}")
            self.logger.debug(f"Received {message_type} from {client_id}")
            
            # Route messages to appropriate handlers
            if message_type == "authenticate":
                await self._handle_authenticate(client_id, data)
            elif message_type == "create_session":
                await self._handle_create_session(client_id, data)
            elif message_type == "start_session":
                await self._handle_start_session(client_id, data)
            elif message_type == "stop_session":
                await self._handle_stop_session(client_id, data)
            elif message_type == "join_session":
                await self._handle_join_session(client_id, data)
            elif message_type == "motor_command":
                await self._handle_motor_command(client_id, data)
            elif message_type == "get_system_status":
                await self._handle_get_system_status(client_id, data)
            elif message_type == "get_sessions":
                await self._handle_get_sessions(client_id, data)
            elif message_type == "subscribe_events":
                await self._handle_subscribe_events(client_id, data)
            elif message_type == "mode_change":
                await self._handle_mode_change(client_id, data)
            elif message_type == "emergency_stop":
                await self._handle_emergency_stop(client_id, data)
            elif message_type == "start_recording":
                await self._handle_start_recording(client_id, data)
            elif message_type == "stop_recording":
                await self._handle_stop_recording(client_id, data)
            elif message_type == "get_last_motor_states":
                await self._handle_get_last_motor_states(client_id, data)
            elif message_type == "ping":
                await self._send_to_client(client_id, {"type": "pong", "timestamp": time.time()})
            else:
                await self._send_error(client_id, f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError as e:
            await self._send_error(client_id, f"Invalid JSON: {e}")
        except Exception as e:
            self.logger.error(f"Error handling message from {client_id}: {e}")
            await self._send_error(client_id, f"Message handling error: {str(e)}")
    
    async def _handle_authenticate(self, client_id: str, data: Dict):
        """Handle client authentication with API key verification."""
        import os
        
        client = self.clients.get(client_id)
        if not client:
            return
        
        # Check for API key authentication
        provided_key = data.get("api_key", "")
        required_key = os.environ.get("DRAWING_MACHINE_API_KEY", "")
        
        if not required_key or data.get("client_type") == "visitor":
            # No API key set OR visitor client - allow demo access
            client.authenticated = False
            client.client_type = data.get("client_type", "web_ui")
            client.user_info = data.get("user_info", {})
            
            demo_reason = "No API key configured" if not required_key else "Visitor mode"
            await self._send_to_client(client_id, {
                "type": "authenticated",
                "client_id": client_id,
                "server_time": time.time(),
                "api_access": False,
                "message": f"Demo mode - {demo_reason}"
            })
            
        elif provided_key == required_key:
            # Valid API key - full access
            client.authenticated = True
            client.client_type = data.get("client_type", "web_ui")
            client.user_info = data.get("user_info", {})
            
            await self._send_to_client(client_id, {
                "type": "authenticated",
                "client_id": client_id,
                "server_time": time.time(),
                "api_access": True,
                "message": "Full access - blockchain API enabled"
            })
            
        else:
            # Invalid API key
            client.authenticated = False
            await self._send_to_client(client_id, {
                "type": "authentication_failed",
                "client_id": client_id,
                "message": "Invalid API key - access denied"
            })
            return
        
        # Send initial system state to client
        await self._send_system_state_to_client(client_id)
        
        access_level = "full" if getattr(client, 'authenticated', False) else "demo"
        self.logger.info(f"Client {client_id} authenticated as {client.client_type} with {access_level} access")
    
    async def _handle_create_session(self, client_id: str, data: Dict):
        """Handle session creation request."""
        try:
            session_type_str = data.get("session_type", "manual")
            session_mode = DrawingMode(session_type_str)
            
            session = await self.session_manager.create_session(
                mode=session_mode,
                name=data.get("name", f"Session {datetime.now().strftime('%H:%M:%S')}"),
                description=data.get("description", ""),
                config=data.get("config", {})
            )
            session_id = session.session_id
            
            self.stats["total_sessions"] += 1
            
            await self._send_to_client(client_id, {
                "type": "session_created",
                "session_id": session_id,
                "timestamp": time.time()
            })
            
        except Exception as e:
            await self._send_error(client_id, f"Failed to create session: {e}")
    
    async def _handle_start_session(self, client_id: str, data: Dict):
        """Handle session start request."""
        try:
            session_id = data.get("session_id")
            if not session_id:
                await self._send_error(client_id, "Missing session_id")
                return
            
            success = await self.session_manager.start_session(session_id, client_id)
            
            if success:
                await self._send_to_client(client_id, {
                    "type": "session_started",
                    "session_id": session_id,
                    "timestamp": time.time()
                })
                
                # Broadcast to other clients in session
                await self._broadcast_to_session(session_id, {
                    "type": "session_started",
                    "session_id": session_id,
                    "started_by": client_id,
                    "timestamp": time.time()
                }, exclude=client_id)
            else:
                await self._send_error(client_id, "Failed to start session")
                
        except Exception as e:
            await self._send_error(client_id, f"Failed to start session: {e}")
    
    async def _handle_stop_session(self, client_id: str, data: Dict):
        """Handle session stop request."""
        try:
            session_id = data.get("session_id")
            success = await self.session_manager.complete_session(session_id, client_id)
            
            if success:
                await self._broadcast_to_session(session_id, {
                    "type": "session_stopped",
                    "session_id": session_id,
                    "stopped_by": client_id,
                    "timestamp": time.time()
                })
                
                # Remove session from client tracking
                if session_id in self.client_sessions:
                    del self.client_sessions[session_id]
            else:
                await self._send_error(client_id, "Failed to stop session")
                
        except Exception as e:
            await self._send_error(client_id, f"Failed to stop session: {e}")
    
    async def _handle_join_session(self, client_id: str, data: Dict):
        """Handle client joining a session."""
        try:
            session_id = data.get("session_id")
            client = self.clients.get(client_id)
            
            if not client:
                return
            
            success = await self.session_manager.join_session(
                session_id, 
                client_id, 
                {
                    "client_type": client.client_type,
                    "user_info": client.user_info,
                    "connected_at": client.connected_at
                }
            )
            
            if success:
                client.current_session = session_id
                
                # Track clients in session
                if session_id not in self.client_sessions:
                    self.client_sessions[session_id] = set()
                self.client_sessions[session_id].add(client_id)
                
                await self._send_to_client(client_id, {
                    "type": "session_joined",
                    "session_id": session_id,
                    "timestamp": time.time()
                })
                
                # Notify other clients
                await self._broadcast_to_session(session_id, {
                    "type": "client_joined",
                    "session_id": session_id,
                    "client_id": client_id,
                    "client_type": client.client_type,
                    "timestamp": time.time()
                }, exclude=client_id)
            else:
                await self._send_error(client_id, "Failed to join session")
                
        except Exception as e:
            await self._send_error(client_id, f"Failed to join session: {e}")
    
    async def _handle_motor_command(self, client_id: str, data: Dict):
        """Handle motor command from client."""
        try:
            client = self.clients.get(client_id)
            if not client:
                await self._send_error(client_id, "Client not found")
                return
            
            # Create motor command
            command_data = {
                "timestamp": time.time(),
                "client_id": client_id,
                "session_id": client.current_session,
                "motor_name": data.get("motor_name"),
                "velocity_rpm": data.get("velocity_rpm"),
                "direction": data.get("direction"),
                "source": "manual"
            }
            
            self.stats["total_motor_commands"] += 1
            
            # Send motor command directly to TCP server
            await self._send_motor_command_to_tcp_server(data)
            
            # Acknowledge to client with full command details
            await self._send_to_client(client_id, {
                "type": "motor_command_executed",
                "command": command_data,
                "timestamp": time.time()
            })
            
            # Also send motor state update
            await self._send_to_client(client_id, {
                "type": "motor_update",
                "motor_name": data.get("motor_name"),
                "state": {
                    "velocity_rpm": data.get("velocity_rpm"),
                    "direction": data.get("direction"),
                    "last_update": time.time(),
                    "is_enabled": True
                }
            })
            
            # Broadcast motor state update to ALL clients (not just session clients)
            motor_state = {
                "velocity_rpm": data.get("velocity_rpm", 0),
                "direction": data.get("direction", "CW"),
                "last_update": time.time(),
                "is_enabled": True,
                "source": "manual"
            }
            
            # Broadcast the updated motor state to all connected clients
            await self.broadcast_motor_state_update(data.get("motor_name"), motor_state)
            
            await self._emit_event("motor_command", command_data)
            
        except Exception as e:
            await self._send_error(client_id, f"Failed to execute motor command: {e}")
    
    async def _handle_get_system_status(self, client_id: str, data: Dict):
        """Handle system status request."""
        try:
            await self._update_system_health()
            
            status = {
                "type": "system_status",
                "health": asdict(self.system_health),
                "stats": self.stats.copy(),
                "session_manager_stats": self.session_manager.get_system_status(),
                "timestamp": time.time()
            }
            
            await self._send_to_client(client_id, status)
            
        except Exception as e:
            await self._send_error(client_id, f"Failed to get system status: {e}")
    
    async def _handle_get_sessions(self, client_id: str, data: Dict):
        """Handle get sessions request."""
        try:
            sessions = []
            
            for session in self.session_manager.get_active_sessions():
                sessions.append(session.to_dict())
            
            await self._send_to_client(client_id, {
                "type": "sessions_list",
                "sessions": sessions,
                "timestamp": time.time()
            })
            
        except Exception as e:
            await self._send_error(client_id, f"Failed to get sessions: {e}")
    
    async def _handle_subscribe_events(self, client_id: str, data: Dict):
        """Handle event subscription request."""
        # For now, all clients get all events
        await self._send_to_client(client_id, {
            "type": "events_subscribed",
            "events": ["all"],
            "timestamp": time.time()
        })
    
    async def _handle_mode_change(self, client_id: str, data: Dict):
        """Handle mode change request."""
        try:
            new_mode = data.get("mode")
            if not new_mode:
                await self._send_error(client_id, "Missing mode parameter")
                return
            
            client = self.clients.get(client_id)
            if not client:
                await self._send_error(client_id, "Client not found")
                return
            
            # Read current mode for transition logic
            current_mode = self._get_current_system_mode()
            
            # If switching from auto-blockchain to manual, preserve last motor states
            if current_mode in ["auto", "auto-blockchain"] and new_mode == "manual":
                await self._preserve_motor_states_for_manual_transition()
            
            # Forward the mode change to manual control server
            await self._forward_to_manual_control(data)
            
            # Update system mode file
            self._update_system_mode_file(new_mode)
            
            # Acknowledge to client
            await self._send_to_client(client_id, {
                "type": "mode_changed", 
                "new_mode": new_mode,
                "timestamp": time.time()
            })
            
            # Broadcast mode change to ALL clients (not just session clients)
            await self._broadcast_to_all({
                "type": "mode_changed",
                "new_mode": new_mode,
                "changed_by": client_id,
                "timestamp": time.time()
            })
            
            self.logger.info(f"Mode changed from {current_mode} to {new_mode} by client {client_id}")
            
        except Exception as e:
            await self._send_error(client_id, f"Failed to change mode: {e}")
    
    async def _handle_emergency_stop(self, client_id: str, data: Dict):
        """Handle emergency stop request."""
        try:
            # Forward to manual control server
            await self._forward_to_manual_control(data)
            
            # Broadcast to all clients
            await self._broadcast_to_all({
                "type": "emergency_stop",
                "initiated_by": client_id,
                "timestamp": time.time()
            })
            
            self.logger.warning(f"Emergency stop initiated by client {client_id}")
            
        except Exception as e:
            await self._send_error(client_id, f"Failed to initiate emergency stop: {e}")
    
    async def _handle_start_recording(self, client_id: str, data: Dict):
        """Handle start recording request."""
        try:
            session_name = data.get("session_name", f"session_{int(time.time())}")
            
            # Forward to manual control server
            await self._forward_to_manual_control({
                "type": "start_recording",
                "session_name": session_name
            })
            
            await self._send_to_client(client_id, {
                "type": "recording_started",
                "session_name": session_name,
                "timestamp": time.time()
            })
            
        except Exception as e:
            await self._send_error(client_id, f"Failed to start recording: {e}")
    
    async def _handle_stop_recording(self, client_id: str, data: Dict):
        """Handle stop recording request."""
        try:
            # Forward to manual control server
            await self._forward_to_manual_control(data)
            
            await self._send_to_client(client_id, {
                "type": "recording_stopped",
                "timestamp": time.time()
            })
            
        except Exception as e:
            await self._send_error(client_id, f"Failed to stop recording: {e}")
    
    async def _handle_get_last_motor_states(self, client_id: str, data: Dict):
        """Handle request for last motor states from blockchain."""
        try:
            import os
            import json
            
            # Read the last saved motor states
            last_states_file = os.path.join(os.path.dirname(__file__), "../../last_motor_states.json")
            
            if os.path.exists(last_states_file):
                with open(last_states_file, "r") as f:
                    last_states = json.load(f)
                
                # Send motor state updates to client
                for motor_name, motor_data in last_states.items():
                    await self._send_to_client(client_id, {
                        "type": "motor_update",
                        "motor_name": motor_name,
                        "state": {
                            "velocity_rpm": motor_data.get("rpm", 0),
                            "direction": motor_data.get("dir", "CW"),
                            "last_update": time.time(),
                            "is_enabled": True
                        }
                    })
                    
                self.logger.info(f"Sent {len(last_states)} last motor states to client {client_id}")
            else:
                self.logger.info("No last motor states file found")
                
        except Exception as e:
            self.logger.error(f"Failed to get last motor states: {e}")
    
    async def _forward_to_manual_control(self, data: Dict):
        """Forward command to manual control server."""
        try:
            # For now, we'll use the data processor to handle commands
            # In a full implementation, this would connect to the manual control server
            self.logger.info(f"Forwarding to manual control: {data}")
            
            # If it's a motor command, we need to send it to the motor TCP server
            if data.get("type") == "motor_command":
                await self._send_motor_command_to_tcp_server(data)
            elif data.get("type") == "mode_change":
                await self._send_mode_change_to_tcp_server(data)
            
        except Exception as e:
            self.logger.error(f"Failed to forward to manual control: {e}")
    
    async def _send_motor_command_to_tcp_server(self, data: Dict):
        """Send motor command directly to TCP server."""
        try:
            import socket
            import json
            
            # Convert to TCP server format
            tcp_command = {
                "motor_name": data.get("motor_name"),
                "velocity_rpm": data.get("velocity_rpm", 0),
                "direction": data.get("direction", "CW"),
                "source": "manual"
            }
            
            # Send to motor TCP server
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1.0)
                sock.connect(("localhost", 8767))
                sock.send(json.dumps(tcp_command).encode() + b'\n')
                
            self.logger.info(f"Sent manual motor command to TCP server: {tcp_command}")
            
        except Exception as e:
            self.logger.error(f"Failed to send motor command to TCP server: {e}")
    
    async def _send_mode_change_to_tcp_server(self, data: Dict):
        """Send mode change message to TCP server to trigger mode detection."""
        try:
            import socket
            import json
            
            new_mode = data.get("mode", "manual")
            
            # Send a special mode change command that the TCP server can detect
            if new_mode == "manual":
                # Send a dummy manual command to trigger MANUAL mode detection
                mode_command = {
                    "motor_name": "motor_canvas",
                    "velocity_rpm": 0,
                    "direction": "CW",
                    "source": "manual",
                    "mode_change": True
                }
            else:
                # For auto modes, send a blockchain-style command
                mode_command = {
                    "motors": {},
                    "blockchain_data": {
                        "eth_price_usd": 0,
                        "gas_price_gwei": 0,
                        "blob_space_utilization_percent": 0,
                        "block_fullness_percent": 0,
                        "epoch": 0,
                        "block_number": 0,
                        "data_sources": {}
                    },
                    "mode_change": True
                }
            
            # Send to motor TCP server
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1.0)
                sock.connect(("localhost", 8767))
                sock.send(json.dumps(mode_command).encode() + b'\n')
                
            self.logger.info(f"Sent mode change to TCP server: {new_mode} -> {mode_command}")
            
        except Exception as e:
            self.logger.error(f"Failed to send mode change to TCP server: {e}")
    
    def _get_current_system_mode(self) -> str:
        """Get current system mode from file."""
        try:
            import os
            mode_file = os.path.join(os.path.dirname(__file__), "../../system_mode.txt")
            if os.path.exists(mode_file):
                with open(mode_file, "r") as f:
                    return f.read().strip()
            return "auto"
        except Exception as e:
            self.logger.error(f"Failed to read system mode file: {e}")
            return "auto"
    
    def _update_system_mode_file(self, mode: str):
        """Update the system mode file for other services to read."""
        try:
            import os
            mode_file = os.path.join(os.path.dirname(__file__), "../../system_mode.txt")
            with open(mode_file, "w") as f:
                f.write(mode)
            self.logger.info(f"Updated system mode file to: {mode}")
        except Exception as e:
            self.logger.error(f"Failed to update system mode file: {e}")
    
    async def _preserve_motor_states_for_manual_transition(self):
        """Preserve last motor states when transitioning from auto to manual mode."""
        try:
            # Read the last motor states file if it exists
            import os
            import json
            last_states_file = os.path.join(os.path.dirname(__file__), "../../last_motor_states.json")
            
            if os.path.exists(last_states_file):
                with open(last_states_file, "r") as f:
                    last_states = json.load(f)
                
                # Send these states to the TCP server to initialize manual mode with last known positions
                for motor_name, state in last_states.items():
                    manual_command = {
                        "motor_name": motor_name,
                        "velocity_rpm": state.get("velocity_rpm", 0),
                        "direction": state.get("direction", "CW"),
                        "source": "transition_preserve"
                    }
                    await self._send_motor_command_to_tcp_server(manual_command)
                    
                self.logger.info(f"Preserved {len(last_states)} motor states for smooth transition to manual mode")
            else:
                self.logger.info("No previous motor states found for transition")
                
        except Exception as e:
            self.logger.error(f"Failed to preserve motor states for transition: {e}")
    
    async def _send_system_state_to_client(self, client_id: str):
        """Send system state including motor states to client."""
        try:
            # Read current system mode
            import os
            mode_file = os.path.join(os.path.dirname(__file__), "../../system_mode.txt")
            current_mode = "auto"
            try:
                with open(mode_file, "r") as f:
                    current_mode = f.read().strip()
            except:
                pass
            
            # Try to read current motor states from file, fallback to defaults
            motor_states = {
                "motor_canvas": {"velocity_rpm": 0, "direction": "CW", "last_update": time.time(), "is_enabled": True},
                "motor_pb": {"velocity_rpm": 0, "direction": "CW", "last_update": time.time(), "is_enabled": True},
                "motor_pcd": {"velocity_rpm": 0, "direction": "CW", "last_update": time.time(), "is_enabled": True},
                "motor_pe": {"velocity_rpm": 0, "direction": "CW", "last_update": time.time(), "is_enabled": True}
            }
            
            # Try to read actual motor states from saved file
            try:
                import json
                last_states_file = os.path.join(os.path.dirname(__file__), "../../last_motor_states.json")
                if os.path.exists(last_states_file):
                    with open(last_states_file, "r") as f:
                        saved_states = json.load(f)
                    
                    # Update with saved states
                    for motor_name, saved_state in saved_states.items():
                        if motor_name in motor_states:
                            motor_states[motor_name].update({
                                "velocity_rpm": saved_state.get("velocity_rpm", 0),
                                "direction": saved_state.get("direction", "CW"),
                                "last_update": saved_state.get("last_update", time.time()),
                                "is_enabled": saved_state.get("is_enabled", True)
                            })
                    
                    self.logger.info(f"Loaded actual motor states from file for client {client_id}")
                else:
                    self.logger.info(f"No saved motor states found, using defaults for client {client_id}")
                    
            except Exception as e:
                self.logger.warning(f"Failed to read saved motor states: {e}, using defaults")
            
            # Safety limits
            safety_limits = {
                "canvas_max": 100,
                "pb_max": 100,
                "pcd_max": 100,
                "pe_max": 100
            }
            
            # Send system state message that matches frontend expectations
            await self._send_to_client(client_id, {
                "type": "system_state",
                "mode": current_mode,
                "emergency_stopped": False,
                "motor_states": motor_states,
                "safety_limits": safety_limits,
                "recording_active": False
            })
            
            self.logger.info(f"Sent system state to client {client_id}: mode={current_mode}")
            
        except Exception as e:
            self.logger.error(f"Failed to send system state to client {client_id}: {e}")
    
    async def _send_to_client(self, client_id: str, message: Dict):
        """Send message to specific client."""
        client = self.clients.get(client_id)
        if not client:
            return
        
        try:
            # Debug: Log JSON serialization for blockchain data
            if message.get('type') == 'blockchain_data_update':
                self.logger.debug(f"JSON SERIALIZING base_fee_gwei: {message.get('blockchain_data', {}).get('base_fee_gwei', 'MISSING')}")
                message_json = json.dumps(message)
                # Parse it back to verify
                parsed = json.loads(message_json)
                self.logger.debug(f"JSON PARSED BACK base_fee_gwei: {parsed.get('blockchain_data', {}).get('base_fee_gwei', 'MISSING')}")
            else:
                message_json = json.dumps(message)
            
            await client.websocket.send(message_json)
        except Exception as e:
            self.logger.warning(f"Failed to send to client {client_id}: {e}")
            await self._cleanup_client(client_id)
    
    async def _broadcast_to_session(self, session_id: str, message: Dict, exclude: str = None):
        """Broadcast message to all clients in a session."""
        if session_id not in self.client_sessions:
            return
        
        for client_id in self.client_sessions[session_id]:
            if client_id != exclude:
                await self._send_to_client(client_id, message)
    
    async def _broadcast_to_all(self, message: Dict):
        """Broadcast message to all connected clients."""
        for client_id in self.clients:
            await self._send_to_client(client_id, message)
    
    async def _send_error(self, client_id: str, error_message: str):
        """Send error message to client."""
        await self._send_to_client(client_id, {
            "type": "error",
            "message": error_message,
            "timestamp": time.time()
        })
    
    async def broadcast_blockchain_data(self, blockchain_data: Dict, motor_commands: Dict):
        """Broadcast blockchain data and motor commands to all connected clients."""
        try:
            # Debug: Log what we're receiving
            self.logger.debug(f"ORCHESTRATOR RECEIVED blockchain_data: {blockchain_data}")
            self.logger.debug(f"ORCHESTRATOR RECEIVED base_fee_gwei: {blockchain_data.get('base_fee_gwei', 'MISSING')}")
            
            message = {
                "type": "blockchain_data_update",
                "blockchain_data": blockchain_data,
                "motor_commands": motor_commands,
                "timestamp": time.time()
            }
            
            # Debug: Log what we're sending
            self.logger.debug(f"ORCHESTRATOR SENDING base_fee_gwei: {message['blockchain_data'].get('base_fee_gwei', 'MISSING')}")
            
            await self._broadcast_to_all(message)
            self.logger.debug(f"Broadcasted blockchain data to {len(self.clients)} clients")
            
        except Exception as e:
            self.logger.error(f"Failed to broadcast blockchain data: {e}")
    
    async def broadcast_motor_state_update(self, motor_name: str, motor_state: Dict):
        """Broadcast individual motor state update to all connected clients."""
        try:
            message = {
                "type": "motor_update",
                "motor_name": motor_name,
                "state": motor_state,
                "timestamp": time.time()
            }
            await self._broadcast_to_all(message)
            self.logger.debug(f"Broadcasted motor {motor_name} state update")
            
        except Exception as e:
            self.logger.error(f"Failed to broadcast motor state update: {e}")
    
    async def _send_system_state(self, websocket: WebSocketServerProtocol):
        """Send initial system state to new client."""
        await self._update_system_health()
        
        state = {
            "type": "system_state",
            "health": asdict(self.system_health),
            "active_sessions": len(self.session_manager.active_sessions),
            "connected_clients": len(self.clients),
            "server_time": time.time()
        }
        
        await websocket.send(json.dumps(state))
    
    async def _cleanup_client(self, client_id: str):
        """Clean up client connection and associated resources."""
        client = self.clients.get(client_id)
        if not client:
            return
        
        # Leave current session
        if client.current_session:
            await self.session_manager.leave_session(client.current_session, client_id)
            
            # Remove from session tracking
            if client.current_session in self.client_sessions:
                self.client_sessions[client.current_session].discard(client_id)
                if not self.client_sessions[client.current_session]:
                    del self.client_sessions[client.current_session]
        
        # Remove client
        del self.clients[client_id]
        
        await self._emit_event("client_disconnected", {"client_id": client_id})
        
        self.logger.info(f"Cleaned up client: {client_id}")
    
    async def _update_system_health(self):
        """Update system health metrics."""
        self.system_health.uptime_seconds = time.time() - self.start_time
        self.system_health.connected_clients = len(self.clients)
        self.system_health.active_sessions = len(self.session_manager.active_sessions)
        self.system_health.last_updated = time.time()
        
        # Check service health
        self.system_health.services = {
            "session_manager": ServiceStatus.HEALTHY,
            "data_processor": ServiceStatus.HEALTHY,
            "websocket_server": ServiceStatus.HEALTHY
        }
        
        # Determine overall status
        service_statuses = list(self.system_health.services.values())
        if all(s == ServiceStatus.HEALTHY for s in service_statuses):
            self.system_health.status = ServiceStatus.HEALTHY
        elif any(s == ServiceStatus.OFFLINE for s in service_statuses):
            self.system_health.status = ServiceStatus.UNHEALTHY
        else:
            self.system_health.status = ServiceStatus.DEGRADED
    
    async def _health_check_loop(self):
        """Background health check loop."""
        while True:
            try:
                await self._update_system_health()
                await self._emit_event("health_check", asdict(self.system_health))
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check error: {e}")
                await asyncio.sleep(60)
    
    async def _stats_update_loop(self):
        """Background statistics update loop."""
        while True:
            try:
                # Update various statistics
                await asyncio.sleep(60)  # Update every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Stats update error: {e}")
                await asyncio.sleep(60)
    
    async def _emit_event(self, event_type: str, data):
        """Emit event to registered handlers."""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    self.logger.error(f"Event handler error for {event_type}: {e}")
    
    # Session manager event callbacks
    async def _on_session_created(self, session):
        """Handle session created event."""
        await self._broadcast_to_all({
            "type": "session_created",
            "session": session.to_dict(),
            "timestamp": time.time()
        })
    
    async def _on_session_started(self, session):
        """Handle session started event."""
        await self._broadcast_to_all({
            "type": "session_started",
            "session_id": session.metadata.session_id,
            "timestamp": time.time()
        })
    
    async def _on_session_completed(self, session):
        """Handle session completed event."""
        await self._broadcast_to_all({
            "type": "session_completed",
            "session_id": session.metadata.session_id,
            "stats": asdict(session.stats),
            "timestamp": time.time()
        })
    
    async def _on_client_joined_session(self, data):
        """Handle client joined session event."""
        session = data["session"]
        client_id = data["client_id"]
        
        await self._broadcast_to_session(session.metadata.session_id, {
            "type": "client_joined",
            "session_id": session.metadata.session_id,
            "client_id": client_id,
            "timestamp": time.time()
        }, exclude=client_id)


# Standalone server function
async def start_cloud_orchestrator():
    """Start the cloud orchestrator server."""
    orchestrator = CloudOrchestrator()
    await orchestrator.start_server()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Starting Cloud Orchestrator...")
    asyncio.run(start_cloud_orchestrator())