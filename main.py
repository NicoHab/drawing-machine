#!/usr/bin/env python3
"""
Railway Production Entry Point for Drawing Machine

Streamlined production server for cloud deployment while maintaining
compatibility with the complete local development system.
"""

import asyncio
import logging
import os
import time
from pathlib import Path

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
                    
load_env_file()

# Global orchestrator instance for blockchain data broadcasting
cloud_orchestrator_instance = None

def get_system_mode():
    """Get current system mode from environment or file."""
    # Priority: Environment variable > file > default
    mode = os.environ.get('SYSTEM_MODE', '').lower()
    if mode in ['auto', 'manual']:
        return mode
        
    try:
        mode_file = Path(__file__).parent / "system_mode.txt"
        if mode_file.exists():
            with open(mode_file, 'r') as f:
                file_mode = f.read().strip().lower()
                if file_mode in ['auto', 'manual']:
                    return file_mode
    except Exception as e:
        logger.warning(f"Could not read mode file: {e}")
    
    return "auto"  # Default for production

def save_last_motor_states(motor_states):
    """Save last motor states for smooth transitions."""
    try:
        import json
        states_file = Path(__file__).parent / "last_motor_states.json"
        with open(states_file, 'w') as f:
            json.dump(motor_states, f, indent=2)
        logger.info(f"Saved motor states for transition: {len(motor_states)} motors")
    except Exception as e:
        logger.error(f"Error saving motor states: {e}")

async def start_cloud_orchestrator():
    """Start the cloud orchestrator for production."""
    logger.info("Starting Cloud Orchestrator for Railway deployment...")
    
    from cloud.orchestrator.cloud_orchestrator import CloudOrchestrator
    
    global cloud_orchestrator_instance
    
    # Get port from Railway environment or default
    port = int(os.environ.get('PORT', 8768))
    host = "0.0.0.0"  # Railway requires 0.0.0.0 binding
    
    cloud_orchestrator_instance = CloudOrchestrator(host=host, port=port)
    orchestrator_task = asyncio.create_task(cloud_orchestrator_instance.start_server())
    
    logger.info(f"Cloud Orchestrator started on {host}:{port}")
    return orchestrator_task

async def start_blockchain_service():
    """Start blockchain data processing for production."""
    logger.info("Starting Blockchain Data Service...")
    
    from cloud.data_aggregator.data_processor import DataProcessor
    import socket
    import json
    
    # Check if API usage is authorized
    api_auth_key = os.environ.get('DRAWING_MACHINE_API_KEY', '')
    if not api_auth_key:
        logger.warning("No DRAWING_MACHINE_API_KEY set - blockchain processing disabled for API cost control")
        logger.info("To enable: Set DRAWING_MACHINE_API_KEY environment variable in Railway")
        # Return a dummy task that does nothing
        async def dummy_loop():
            while True:
                await asyncio.sleep(60)
        return asyncio.create_task(dummy_loop())
    
    processor = DataProcessor()
    
    # Event-driven blockchain processing callback
    async def on_new_block(block_number: int):
        """Handle new block events from WebSocket subscription."""
        try:
            mode = get_system_mode()
            if mode != "auto":
                logger.debug(f"System in manual mode, ignoring block {block_number}")
                return
            
            logger.info(f"🔥 Processing new block: {block_number}")
            
            # Process blockchain data (force refresh to bypass cache)
            result = await processor.process_current_data(force_refresh=True)
            
            if result and result.motors:
                # Use the SAME blockchain data for both motor commands and display
                # This ensures perfect consistency between calculated RPMs and displayed metrics
                source_data = result.source_data
                
                if source_data:
                    # Convert motor commands to execution format
                    motor_commands = {}
                    for motor_name, motor_cmd in result.motors.items():
                        motor_commands[motor_name] = {
                            "velocity_rpm": motor_cmd.velocity_rpm,
                            "direction": motor_cmd.direction.value,
                            "duration_seconds": getattr(motor_cmd, 'duration_seconds', 3.4)
                        }
                    
                    # Use the SAME blockchain data that was used for motor calculation
                    blob_util_for_motor = getattr(source_data, 'blob_space_utilization_percent', 0)
                    logger.info(f"🔍 DEBUG: Motor calculation used blob_util={blob_util_for_motor}%")
                    
                    blockchain_data = {
                        "eth_price_usd": getattr(source_data, 'eth_price_usd', 0),
                        "gas_price_gwei": getattr(source_data, 'gas_price_gwei', 0),
                        "base_fee_gwei": getattr(source_data, 'base_fee_gwei', 0),
                        "blob_space_utilization_percent": blob_util_for_motor,
                        "block_fullness_percent": getattr(source_data, 'block_fullness_percent', 0),
                        "block_number": block_number,
                        "epoch": getattr(source_data, 'epoch', 'N/A'),
                        "data_sources": getattr(source_data, 'data_sources', {})
                    }
                    
                    logger.info(f"🔍 DEBUG: Sending to frontend blob_util={blockchain_data['blob_space_utilization_percent']}%")
                    
                    # Calculate gas ratio for logging
                    if blockchain_data['base_fee_gwei'] > 0:
                        gas_ratio = (blockchain_data['gas_price_gwei'] / blockchain_data['base_fee_gwei']) * 100
                        logger.info(f"BLOCK {block_number}: ETH=${blockchain_data['eth_price_usd']:.2f}, "
                                   f"Gas={gas_ratio:.0f}% of target ({blockchain_data['gas_price_gwei']:.1f}/{blockchain_data['base_fee_gwei']:.1f} gwei)")
                    else:
                        logger.info(f"BLOCK {block_number}: ETH=${blockchain_data['eth_price_usd']:.2f}, "
                                   f"Gas={blockchain_data['gas_price_gwei']:.1f} gwei")
                    
                    # Save motor states for transitions
                    motor_states = {}
                    for motor_name, motor_data in motor_commands.items():
                        motor_states[motor_name] = {
                            "rpm": motor_data["velocity_rpm"],
                            "dir": motor_data["direction"]
                        }
                    save_last_motor_states(motor_states)
                    
                    # Broadcast to connected web clients
                    if cloud_orchestrator_instance:
                        try:
                            # Convert for frontend
                            frontend_commands = {}
                            for motor_name, motor_data in motor_commands.items():
                                frontend_commands[motor_name] = {
                                    "velocity_rpm": motor_data["velocity_rpm"],
                                    "direction": motor_data["direction"]
                                }
                            
                            # Broadcast blockchain data
                            await cloud_orchestrator_instance.broadcast_blockchain_data(
                                blockchain_data, frontend_commands
                            )
                            
                            # Update individual motor states
                            for motor_name, motor_data in frontend_commands.items():
                                await cloud_orchestrator_instance.broadcast_motor_state_update(
                                    motor_name, {
                                        "velocity_rpm": motor_data["velocity_rpm"],
                                        "direction": motor_data["direction"],
                                        "last_update": time.time(),
                                        "is_enabled": True,
                                        "source": "blockchain"
                                    }
                                )
                            
                            logger.info("Broadcasted blockchain data to web clients")
                            
                        except Exception as e:
                            logger.error(f"Failed to broadcast data: {e}")
        
        except Exception as e:
            logger.error(f"Blockchain processing error: {e}")
    
    # Start WebSocket block subscription
    logger.info("🚀 Starting WebSocket block subscription...")
    websocket_success = await processor.fetcher.start_block_subscription(on_new_block)
    
    if websocket_success:
        logger.info("✅ WebSocket block subscription active - real-time blockchain updates enabled")
    else:
        logger.info("📡 Using HTTP polling fallback - still functional but slower updates")
    
    # Keep the blockchain service alive
    async def keep_alive():
        while True:
            await asyncio.sleep(60)  # Keep alive check every minute
            if get_system_mode() == "auto":
                logger.debug("Blockchain service alive and monitoring")
    
    return asyncio.create_task(keep_alive())

async def main():
    """Main production server entry point."""
    logger.info("=" * 60)
    logger.info("DRAWING MACHINE - RAILWAY PRODUCTION SERVER")
    logger.info("=" * 60)
    
    try:
        # Start services
        orchestrator_task = await start_cloud_orchestrator()
        await asyncio.sleep(2)  # Let orchestrator start
        
        blockchain_task = await start_blockchain_service()
        
        logger.info("✅ All production services started successfully!")
        logger.info(f"🌐 Server listening on port {os.environ.get('PORT', 8768)}")
        logger.info("🎨 Drawing Machine ready for blockchain-driven art creation!")
        
        # Wait for services
        await asyncio.gather(
            orchestrator_task,
            blockchain_task,
            return_exceptions=True
        )
        
    except KeyboardInterrupt:
        logger.info("Shutting down production server...")
    except Exception as e:
        logger.error(f"Production server error: {e}")
        raise

if __name__ == "__main__":
    # Production server entry point
    asyncio.run(main())