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
    
    processor = DataProcessor()
    
    async def blockchain_loop():
        current_block = None
        
        while True:
            try:
                mode = get_system_mode()
                if mode != "auto":
                    logger.debug("System in manual mode, pausing blockchain processing")
                    await asyncio.sleep(5)
                    continue
                
                # Process blockchain data
                result = await processor.process_current_data()
                
                if result and result.motors:
                    # Get latest blockchain snapshot for display data
                    snapshot = processor.fetcher.get_latest_cached_data()
                    
                    if snapshot:
                        block_number = getattr(snapshot, 'block_number', 'N/A')
                        
                        if block_number != current_block:
                            current_block = block_number
                            
                            # Convert motor commands to execution format
                            motor_commands = {}
                            for motor_name, motor_cmd in result.motors.items():
                                motor_commands[motor_name] = {
                                    "velocity_rpm": motor_cmd.velocity_rpm,
                                    "direction": motor_cmd.direction.value,
                                    "duration_seconds": motor_cmd.duration_seconds
                                }
                            
                            # Get blockchain data for display
                            blockchain_data = {
                                "eth_price_usd": getattr(snapshot, 'eth_price_usd', 0),
                                "gas_price_gwei": getattr(snapshot, 'gas_price_gwei', 0),
                                "blob_space_utilization_percent": getattr(snapshot, 'blob_space_utilization_percent', 0),
                                "block_fullness_percent": getattr(snapshot, 'block_fullness_percent', 0),
                                "block_number": block_number,
                                "epoch": getattr(snapshot, 'epoch', 'N/A'),
                                "data_sources": getattr(snapshot, 'data_sources', {})
                            }
                        
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
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Blockchain processing error: {e}")
                await asyncio.sleep(30)  # Wait longer on errors
    
    return asyncio.create_task(blockchain_loop())

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