#!/usr/bin/env python3
"""
Drawing Machine Pipeline Demo

Demonstrates the complete blockchain-to-motor control pipeline
with simplified components for testing and demonstration.
"""

import asyncio
import logging
from datetime import datetime

from cloud.orchestrator import DrawingSessionManager, PipelineOrchestrator
from shared.models.drawing_session import DrawingMode
from shared.models.motor_commands import MotorSafetyLimits


async def demo_pipeline():
    """Demonstrate the complete drawing machine pipeline."""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("🎨 Starting Drawing Machine Pipeline Demo")
    
    try:
        # Create session manager
        logger.info("📋 Creating session manager...")
        session_manager = DrawingSessionManager()
        
        # Create safety limits for demo
        safety_limits = MotorSafetyLimits(
            motor_canvas_max_rpm=20.0,    # Reduced for demo
            motor_pb_max_rpm=15.0,
            motor_pcd_max_rpm=12.0,
            motor_pe_max_rpm=18.0,
            emergency_stop_rpm=0.0,
        )
        
        # Create a blockchain mode session
        logger.info("🔗 Creating blockchain drawing session...")
        session = await session_manager.create_session(
            mode=DrawingMode.BLOCKCHAIN,
            name="Demo Blockchain Session",
            description="Demonstration of blockchain-driven drawing",
            config={
                "demo_mode": True,
                "reduced_safety_limits": True,
            }
        )
        
        logger.info(f"✅ Created session: {session.session_id}")
        
        # Start the session
        logger.info("🚀 Starting drawing session...")
        success = await session_manager.start_session(session.session_id)
        
        if not success:
            logger.error("❌ Failed to start session")
            return
        
        logger.info("✅ Session started successfully")
        
        # Let it run for a demo period
        logger.info("⏳ Running pipeline for 30 seconds...")
        await asyncio.sleep(30)
        
        # Get session status
        status = await session_manager.get_session_status(session.session_id)
        if status:
            logger.info(f"📊 Session Status:")
            logger.info(f"   Mode: {status['mode']}")
            logger.info(f"   Status: {status['status']}")
            logger.info(f"   Epochs: {status['metrics']['epochs_completed']}")
            logger.info(f"   Commands: {status['metrics']['commands_executed']}")
        
        # Stop the session
        logger.info("🛑 Stopping session...")
        await session_manager.stop_session(session.session_id)
        
        # Show final statistics
        stats = await session_manager.get_manager_stats()
        logger.info(f"📈 Final Statistics:")
        logger.info(f"   Sessions Created: {stats['statistics']['total_sessions_created']}")
        logger.info(f"   Sessions Completed: {stats['statistics']['total_sessions_completed']}")
        
        logger.info("🎉 Demo completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


async def demo_single_cycle():
    """Demonstrate a single pipeline cycle."""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🔄 Testing single pipeline cycle...")
    
    try:
        # Create orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Execute single cycle (without hardware connection)
        success = await orchestrator.execute_single_cycle(epoch=1)
        
        if success:
            logger.info("✅ Single cycle completed successfully")
        else:
            logger.error("❌ Single cycle failed")
        
        # Show pipeline status
        status = await orchestrator.get_pipeline_status()
        logger.info(f"📊 Pipeline Statistics:")
        logger.info(f"   Total Cycles: {status['pipeline_statistics']['total_cycles']}")
        logger.info(f"   Successful: {status['pipeline_statistics']['successful_cycles']}")
        logger.info(f"   Average Time: {status['pipeline_statistics']['average_cycle_time_ms']:.1f}ms")
        
    except Exception as e:
        logger.error(f"❌ Single cycle demo failed: {e}")


async def demo_data_processing():
    """Demonstrate just the data processing pipeline."""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("📊 Testing data processing pipeline...")
    
    try:
        from cloud.data_aggregator import DataProcessor
        
        # Create data processor
        processor = DataProcessor()
        
        # Process current data
        logger.info("🔄 Processing blockchain data...")
        commands = await processor.process_current_data(epoch=1)
        
        logger.info("✅ Data processing successful!")
        logger.info(f"📋 Generated Commands:")
        logger.info(f"   Epoch: {commands.epoch}")
        logger.info(f"   Motors: {len(commands.motors)}")
        logger.info(f"   Duration: {commands.command_duration_seconds}s")
        
        # Show processing status
        status = processor.get_processing_status()
        logger.info(f"📈 Processing Status: {status['status']}")
        
    except Exception as e:
        logger.error(f"❌ Data processing demo failed: {e}")


def main():
    """Main demo function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Drawing Machine Pipeline Demo")
    parser.add_argument(
        "--mode", 
        choices=["full", "single", "data"], 
        default="data",
        help="Demo mode: full pipeline, single cycle, or data processing only"
    )
    
    args = parser.parse_args()
    
    if args.mode == "full":
        asyncio.run(demo_pipeline())
    elif args.mode == "single":
        asyncio.run(demo_single_cycle())
    else:
        asyncio.run(demo_data_processing())


if __name__ == "__main__":
    main()