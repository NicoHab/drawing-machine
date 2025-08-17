"""
Test script for the TDD Workflow Manager.

Demonstrates the TDD framework in action using a realistic example.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.tdd_workflow import (
    TestFirstWorkflow,
    create_component_specification,
    run_tdd_workflow,
)


def test_tdd_workflow_basic():
    """Test basic TDD workflow functionality."""

    # Create a realistic component specification
    spec = create_component_specification(
        name="EthereumDataProcessor",
        description="Process Ethereum blockchain data for drawing machine motor control",
        requirements=[
            "Accept Ethereum blockchain data in JSON format",
            "Validate data structure and ranges",
            "Transform price data to motor control values",
            "Calculate activity levels from gas prices",
            "Support JSON serialization with computed fields",
            "Handle validation errors gracefully",
        ],
        dependencies=["pydantic", "datetime", "enum"],
        interfaces={
            "input": "Dict[str, Any] - Raw blockchain data",
            "output": "EthereumDataProcessor - Validated and processed data",
            "methods": ["process_data", "get_motor_values", "validate"],
        },
        validation_rules=[
            "ETH price must be between 100-50000 USD",
            "Gas price must be between 0.1-1000 Gwei",
            "Percentages must be between 0-100",
            "Timestamp must be recent (within 24 hours)",
        ],
        examples={
            "valid_input": {
                "timestamp": 1692123456.789,
                "eth_price_usd": 2500.50,
                "gas_price_gwei": 25.5,
                "blob_space_utilization_percent": 75.2,
                "block_fullness_percent": 85.7,
            },
            "invalid_input": {
                "timestamp": "invalid",
                "eth_price_usd": -100,
                "gas_price_gwei": 2000,
                "blob_space_utilization_percent": 150,
            },
        },
        success_criteria=[
            "All validation tests pass",
            "JSON round-trip serialization works",
            "Motor control values calculated correctly",
            "Error handling covers all edge cases",
            "Code coverage exceeds 85%",
            "Integration with existing Drawing Machine models",
        ],
    )

    print("Testing TDD Workflow Manager")
    print("=" * 50)

    # Initialize workflow
    workflow = TestFirstWorkflow(project_root, "tests/tdd_demo")

    print(f"Component Specification: {spec.name}")
    print(f"Description: {spec.description}")
    print(f"Requirements: {len(spec.requirements)} items")
    print(f"Success Criteria: {len(spec.success_criteria)} items")

    # Step 1: Generate tests first
    print("\nStep 1: Writing tests first...")
    test_file = workflow.write_tests_first(spec)
    print(f"Generated test file: {test_file}")

    # Verify test file was created and has content
    assert test_file.exists(), "Test file should be created"

    with open(test_file) as f:
        test_content = f.read()

    # Check that test follows our patterns
    assert "TestFixtures" in test_content, "Should include test fixtures"
    assert (
        "test_json_serialization" in test_content
    ), "Should include JSON serialization tests"
    assert "test_validation_rules" in test_content, "Should include validation tests"
    assert "pytest" in test_content, "Should use pytest framework"

    print("Test file structure validated")

    # Step 2: Generate implementation template
    print("\nStep 2: Generating implementation template...")
    impl_path = project_root / "src" / "ethereum_data_processor.py"

    # Create implementation directory
    impl_path.parent.mkdir(parents=True, exist_ok=True)

    # Extract requirements and generate template
    requirements = workflow._extract_requirements_from_tests(test_file)
    impl_content = workflow._generate_implementation_template(requirements, impl_path)

    with open(impl_path, "w") as f:
        f.write(impl_content)

    print(f"Generated implementation template: {impl_path}")

    # Verify implementation template
    assert impl_path.exists(), "Implementation file should be created"

    with open(impl_path) as f:
        impl_content = f.read()

    assert "BaseModel" in impl_content, "Should use Pydantic BaseModel"
    assert (
        "model_validate_json_safe" in impl_content
    ), "Should include safe JSON validation"
    assert "computed_field" in impl_content, "Should include computed fields"

    print("Implementation template validated")

    # Step 3: Test validation functionality
    print("\nStep 3: Testing validation logic...")

    validation_results = workflow.validate_completion(spec)

    print(f"Validation status: {validation_results['overall_status']}")
    print(f"Criteria checked: {len(validation_results['criteria'])}")

    # Step 4: Generate comprehensive report
    print("\nStep 4: Generating comprehensive report...")

    report = workflow.generate_comprehensive_report()

    assert "session_id" in report, "Report should include session ID"
    assert "current_phase" in report, "Report should include current phase"
    assert "summary" in report, "Report should include summary"

    print("Report generation validated")

    # Display summary
    print("\nTDD Workflow Summary:")
    print(f"  Session ID: {workflow.session_id}")
    print(f"  Current Phase: {workflow.current_phase.value}")
    print(f"  Test File: {test_file.name}")
    print(f"  Implementation: {impl_path.name}")
    print(f"  Reports Directory: {workflow.reports_directory}")

    return True


def test_helper_functions():
    """Test helper functions for component specification creation."""

    print("\nTesting Helper Functions")
    print("=" * 30)

    # Test specification creation
    spec = create_component_specification(
        name="TestComponent",
        description="A test component",
        requirements=["Requirement 1", "Requirement 2"],
    )

    assert spec.name == "TestComponent"
    assert len(spec.requirements) == 2
    assert spec.dependencies == []  # Default empty
    assert len(spec.success_criteria) >= 3  # Should have defaults

    print("Component specification creation works")

    # Test with custom parameters
    custom_spec = create_component_specification(
        name="CustomComponent",
        description="Custom test component",
        requirements=["Custom requirement"],
        dependencies=["pydantic", "fastapi"],
        validation_rules=["Custom rule 1", "Custom rule 2"],
        success_criteria=["Custom success 1", "Custom success 2"],
    )

    assert len(custom_spec.dependencies) == 2
    assert len(custom_spec.validation_rules) == 2
    assert len(custom_spec.success_criteria) == 2

    print("Custom component specification works")


def test_integration_with_existing_patterns():
    """Test integration with our existing Drawing Machine testing patterns."""

    print("\nTesting Integration with Existing Patterns")
    print("=" * 45)

    # Create specification that mirrors our foundational models
    spec = create_component_specification(
        name="MotorControlProcessor",
        description="Motor control processor following Drawing Machine patterns",
        requirements=[
            "Process blockchain data into motor commands",
            "Validate safety limits for all motors",
            "Support emergency stop functionality",
            "Calculate power consumption estimates",
            "Handle JSON serialization with computed fields",
        ],
        dependencies=["shared.models.blockchain_data", "shared.models.motor_commands"],
        validation_rules=[
            "Motor velocities must be within safety limits",
            "All required motors must be present",
            "Emergency stop must set all motors to 0 RPM",
        ],
        examples={
            "valid_input": {
                "epoch": 1337,
                "motor_commands": {
                    "motor_canvas": {"velocity_rpm": 45.5, "direction": "CW"},
                    "motor_pb": {"velocity_rpm": -25.2, "direction": "CCW"},
                },
            }
        },
        success_criteria=[
            "All motor safety validations pass",
            "JSON round-trip preserves data integrity",
            "Integration with EthereumDataSnapshot works",
            "Emergency stop detection functions correctly",
            "95% test coverage achieved",
        ],
    )

    workflow = TestFirstWorkflow(project_root, "tests/integration_demo")

    # Generate tests using our proven patterns
    test_file = workflow.write_tests_first(spec)

    # Read and verify test content follows our patterns
    with open(test_file) as f:
        content = f.read()

    # Check for Drawing Machine specific patterns
    patterns_found = {
        "test_fixtures": "TestFixtures" in content,
        "json_serialization": "test_json_serialization" in content,
        "validation_rules": "test_validation_rules" in content,
        "computed_fields": "test_computed_fields" in content,
        "integration_tests": "test_integration" in content,
        "pytest_framework": "pytest" in content,
    }

    print("Pattern validation results:")
    for pattern, found in patterns_found.items():
        status = "[PASS]" if found else "[FAIL]"
        print(f"  {status} {pattern}: {found}")

    # All critical patterns should be present
    critical_patterns = ["test_fixtures", "json_serialization", "validation_rules"]
    for pattern in critical_patterns:
        assert patterns_found[pattern], f"Critical pattern {pattern} missing"

    print("Integration with existing patterns validated")


def run_complete_demo():
    """Run complete demonstration of TDD workflow."""

    print("Complete TDD Workflow Demonstration")
    print("=" * 40)

    # Example that could be used in real Claude Code sessions
    blockchain_processor_spec = create_component_specification(
        name="BlockchainDataValidator",
        description="Comprehensive blockchain data validation and processing",
        requirements=[
            "Validate Ethereum blockchain data structure",
            "Normalize price data for motor control",
            "Calculate network activity metrics",
            "Detect high-activity epochs",
            "Generate motor control parameters",
            "Support real-time data processing",
            "Handle API response time monitoring",
            "Implement data quality scoring",
        ],
        dependencies=[
            "pydantic",
            "datetime",
            "enum",
            "typing",
            "shared.models.blockchain_data",
        ],
        interfaces={
            "BlockchainDataValidator": {
                "methods": [
                    "validate_data(raw_data: Dict) -> EthereumDataSnapshot",
                    "normalize_for_motors(data: EthereumDataSnapshot) -> MotorValues",
                    "calculate_activity_score(data: EthereumDataSnapshot) -> float",
                    "is_data_quality_acceptable(data: EthereumDataSnapshot) -> bool",
                ],
                "properties": [
                    "validation_rules: List[ValidationRule]",
                    "quality_threshold: float",
                    "activity_thresholds: Dict[str, float]",
                ],
            }
        },
        validation_rules=[
            "ETH price must be realistic (100-50000 USD)",
            "Gas prices must be within network limits (0.1-1000 Gwei)",
            "Timestamp must be recent (within 24 hours)",
            "Percentage values must be 0-100",
            "API response times must be under 30 seconds",
            "Data quality score must be 0.0-1.0",
        ],
        examples={
            "valid_input": {
                "timestamp": 1692123456.789,
                "epoch": 1337,
                "eth_price_usd": 2500.50,
                "gas_price_gwei": 25.5,
                "blob_space_utilization_percent": 75.2,
                "block_fullness_percent": 85.7,
                "data_quality": {
                    "price_data_fresh": True,
                    "gas_data_fresh": True,
                    "blob_data_fresh": True,
                    "block_data_fresh": False,
                    "overall_quality_score": 0.85,
                },
                "api_response_times": {
                    "coinbase_ms": 150.5,
                    "ethereum_rpc_ms": 220.1,
                    "beacon_chain_ms": 180.3,
                },
            },
            "invalid_input": {
                "timestamp": "not_a_timestamp",
                "epoch": -1,
                "eth_price_usd": 0,
                "gas_price_gwei": -5,
            },
        },
        success_criteria=[
            "All validation rules properly enforced",
            "JSON serialization round-trip works perfectly",
            "Integration with existing Drawing Machine models",
            "Computed fields work after deserialization",
            "Error handling covers all edge cases",
            "Performance meets real-time requirements",
            "Code coverage exceeds 90%",
            "Documentation is comprehensive",
        ],
    )

    # Run the complete TDD workflow
    print("\nRunning complete TDD workflow...")

    success = run_tdd_workflow(
        spec=blockchain_processor_spec,
        project_root=project_root,
        implementation_path=project_root / "src" / "blockchain_data_validator.py",
    )

    print(f"\nTDD Workflow Result: {'SUCCESS' if success else 'NEEDS WORK'}")

    return success


if __name__ == "__main__":
    print("TDD Workflow Manager Test Suite")
    print("=" * 50)

    try:
        # Run all tests
        test_tdd_workflow_basic()
        test_helper_functions()
        test_integration_with_existing_patterns()

        # Run complete demo
        run_complete_demo()

        print("\nAll TDD Workflow tests completed successfully!")
        print("\nFramework is ready for use in Claude Code sessions")
        print("\nUsage examples:")
        print(
            "1. Import: from scripts.tdd_workflow import TestFirstWorkflow, create_component_specification"
        )
        print(
            "2. Create spec: spec = create_component_specification(name='MyComponent', ...)"
        )
        print("3. Run TDD: success = run_tdd_workflow(spec, project_root, impl_path)")

    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

