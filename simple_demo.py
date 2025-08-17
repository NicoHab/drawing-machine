#!/usr/bin/env python3
"""
Simple Drawing Machine Demo

Basic demonstration of the core components working independently.
"""

import asyncio
import logging


async def demo_motor_command_generation():
    """Demo motor command generation from blockchain data."""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🎨 Testing Motor Command Generation")
    
    try:
        from cloud.data_aggregator import MotorCommandGenerator
        
        # Create generator
        generator = MotorCommandGenerator()
        
        # Generate test commands
        logger.info("🔄 Generating test motor commands...")
        commands = await generator.generate_test_commands(epoch=1)
        
        logger.info("✅ Motor commands generated successfully!")
        logger.info(f"📋 Command Details:")
        logger.info(f"   Epoch: {commands.epoch}")
        logger.info(f"   Duration: {commands.command_duration_seconds}s")
        logger.info(f"   Motors: {len(commands.motors)}")
        
        # Show individual motor commands
        for motor_name, command in commands.motors.items():
            logger.info(f"   {motor_name}: {command.velocity_rpm:.1f} RPM {command.direction.value}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Motor command generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def demo_blockchain_data_fetch():
    """Demo blockchain data fetching."""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🔗 Testing Blockchain Data Fetching")
    
    try:
        from cloud.data_aggregator import BlockchainDataFetcher
        
        # Create fetcher
        fetcher = BlockchainDataFetcher()
        
        # Fetch current data (will use fallback data for demo)
        logger.info("📊 Fetching blockchain data...")
        data = await fetcher.fetch_current_data()
        
        logger.info("✅ Blockchain data fetched successfully!")
        logger.info(f"📈 Data Summary:")
        logger.info(f"   ETH Price: ${data.eth_price_usd:.2f}")
        logger.info(f"   Gas Price: {data.gas_price_gwei:.1f} Gwei")
        logger.info(f"   Market: {data.market_condition.value}")
        logger.info(f"   Activity: {data.activity_level.value}")
        logger.info(f"   Quality: {data.data_quality_score:.1f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Blockchain data fetch failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def demo_complete_data_pipeline():
    """Demo the complete data processing pipeline."""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🏭 Testing Complete Data Pipeline")
    
    try:
        from cloud.data_aggregator import DataProcessor
        
        # Create processor
        processor = DataProcessor()
        
        # Process data for epoch 1
        logger.info("⚙️ Processing blockchain data to motor commands...")
        commands = await processor.process_current_data(epoch=1)
        
        logger.info("✅ Data pipeline completed successfully!")
        logger.info(f"🎯 Pipeline Results:")
        logger.info(f"   Epoch: {commands.epoch}")
        logger.info(f"   Source Quality: {commands.source_data.data_quality_score:.1f}%")
        logger.info(f"   Motors Controlled: {len(commands.motors)}")
        
        # Show motor velocities
        total_velocity = sum(cmd.velocity_rpm for cmd in commands.motors.values())
        logger.info(f"   Total System Velocity: {total_velocity:.1f} RPM")
        
        # Show status
        status = processor.get_processing_status()
        logger.info(f"📊 Processing Status: {status['status']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Data pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def demo_hardware_interface():
    """Demo hardware interface (without actual hardware)."""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🔧 Testing Hardware Interface")
    
    try:
        from edge.motor_controller import HardwareInterface, MotorDriverError
        from shared.models.motor_commands import MotorSafetyLimits
        
        # Create interface (will fail to connect, but we can test the structure)
        safety_limits = MotorSafetyLimits()
        interface = HardwareInterface("localhost", 8888, safety_limits)
        
        logger.info("📡 Hardware interface created")
        logger.info(f"   Connection Status: {interface.connection_status.value}")
        logger.info(f"   Safety Level: {interface.safety_level.value}")
        
        # Test getting system status (without connection)
        try:
            await interface.initialize()
            logger.info("✅ Hardware interface initialized")
        except MotorDriverError:
            logger.info("⚠️ Hardware not connected (expected in demo)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Hardware interface test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_demos():
    """Run all component demos."""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Starting Drawing Machine Component Tests")
    
    demos = [
        ("Blockchain Data Fetch", demo_blockchain_data_fetch),
        ("Motor Command Generation", demo_motor_command_generation),
        ("Complete Data Pipeline", demo_complete_data_pipeline),
        ("Hardware Interface", demo_hardware_interface),
    ]
    
    results = {}
    
    for name, demo_func in demos:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 Running: {name}")
        logger.info(f"{'='*50}")
        
        success = await demo_func()
        results[name] = success
        
        if success:
            logger.info(f"✅ {name} - PASSED")
        else:
            logger.info(f"❌ {name} - FAILED")
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("📊 DEMO SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(results.values())
    total = len(results)
    
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"  {status} - {name}")
    
    logger.info(f"\n🎯 Overall Result: {passed}/{total} components working")
    
    if passed == total:
        logger.info("🎉 All components functional!")
    else:
        logger.info("⚠️ Some components need attention")


def main():
    """Main function."""
    asyncio.run(run_all_demos())


if __name__ == "__main__":
    main()