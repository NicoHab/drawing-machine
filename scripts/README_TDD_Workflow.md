# TDD Workflow Manager for Claude Code

A comprehensive Test-Driven Development framework that enforces test-first development, automates test execution, and ensures high code quality through iterative testing cycles.

## Features

- **Test-First Development**: Write comprehensive tests before implementation
- **Automated Test Cycles**: Run test-fix-iterate loops until all tests pass
- **JSON Serialization Testing**: Built-in patterns for Pydantic model testing
- **Coverage Reporting**: Ensure minimum code coverage thresholds
- **Integration Testing**: Test component interactions and workflows
- **Comprehensive Reporting**: Generate detailed TDD session reports

## Quick Start

```python
from scripts.tdd_workflow import (
    TestFirstWorkflow, 
    create_component_specification, 
    run_tdd_workflow
)

# 1. Create component specification
spec = create_component_specification(
    name="MyComponent",
    description="Component description",
    requirements=[
        "Accept JSON input data",
        "Validate data structure", 
        "Transform data",
        "Handle errors gracefully"
    ],
    dependencies=["pydantic", "datetime"],
    validation_rules=[
        "Input must be valid JSON",
        "Required fields must be present"
    ],
    success_criteria=[
        "All tests pass",
        "90% code coverage",
        "JSON serialization works"
    ]
)

# 2. Run complete TDD workflow
success = run_tdd_workflow(
    spec=spec,
    project_root=".",
    implementation_path="./src/my_component.py"
)
```

## Manual Step-by-Step Usage

```python
# Initialize workflow
workflow = TestFirstWorkflow(".", "tests")

# Step 1: Write tests first
test_file = workflow.write_tests_first(spec)

# Step 2: Implement component 
success = workflow.implement_component(test_file, implementation_path)

# Step 3: Run test cycles
success = workflow.run_test_cycle()

# Step 4: Validate completion
validation = workflow.validate_completion(spec)

# Step 5: Generate report
report = workflow.generate_comprehensive_report()
```

## Generated Test Patterns

The framework generates comprehensive test suites following proven patterns:

### Test Structure
- **TestFixtures**: Reusable test data with pytest fixtures
- **Validation Tests**: Test all validation rules and error conditions
- **JSON Serialization**: Round-trip JSON testing with computed fields
- **Integration Tests**: Component interaction and workflow testing
- **Performance Tests**: Ensure performance requirements are met

### Example Generated Test

```python
class TestMyComponent(TestFixtures):
    def test_create_valid_instance(self, valid_input_data):
        """Test creating valid MyComponent instance."""
        instance = MyComponent(**valid_input_data)
        assert instance is not None
    
    def test_json_serialization(self, valid_input_data):
        """Test JSON serialization/deserialization round-trip."""
        instance = MyComponent(**valid_input_data)
        json_str = instance.model_dump_json_safe()
        reconstructed = MyComponent.model_validate_json_safe(json_str)
        assert reconstructed.field == instance.field
    
    def test_validation_rules(self, invalid_input_data):
        """Test validation rules are enforced."""
        with pytest.raises(ValidationError):
            MyComponent(**invalid_input_data)
```

## Generated Implementation Template

The framework creates minimal Pydantic-based implementations:

```python
class MyComponent(BaseModel):
    """Component following Drawing Machine patterns."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    
    @computed_field
    @property
    def created_at(self) -> str:
        """ISO timestamp of creation."""
        return datetime.fromtimestamp(self.timestamp).isoformat()
    
    @classmethod
    def model_validate_json_safe(cls, json_data):
        """Safe JSON validation that excludes computed fields."""
        # Implementation handles computed field filtering
    
    def model_dump_json_safe(self, **kwargs):
        """Safe JSON dump that excludes computed fields."""
        # Implementation handles computed field exclusion
```

## Test Cycle Process

1. **Red**: Write failing tests first
2. **Green**: Implement minimal code to pass tests
3. **Refactor**: Improve code while maintaining test success
4. **Validate**: Ensure all success criteria are met

## Reports Generated

### Test Reports
- Individual test results with timing
- Test failure analysis and suggestions
- Coverage percentages
- Success/failure trends

### Validation Reports
- Success criteria validation
- Coverage threshold checking
- Integration test results
- Overall completion status

### Session Reports
- Complete TDD session history
- Performance metrics
- Summary statistics
- Iteration tracking

## Integration with Drawing Machine Patterns

The framework builds on successful patterns from the Drawing Machine foundational models:

- **Pydantic v2** with proper configuration
- **Computed fields** with safe JSON serialization
- **Recursive filtering** for nested objects
- **Comprehensive test coverage** with fixtures
- **Error handling** and custom exceptions

## Best Practices

### Component Specifications
- Be specific about requirements
- Include concrete examples
- Define clear success criteria
- List all dependencies

### Test Quality
- Write tests before implementation
- Cover all validation rules
- Test error conditions
- Include integration scenarios

### Implementation
- Start with minimal working code
- Iterate based on test failures
- Maintain high test coverage
- Follow existing patterns

## Example: Drawing Machine Component

```python
# Real example from the framework
ethereum_spec = create_component_specification(
    name="EthereumDataProcessor",
    description="Process Ethereum blockchain data for drawing machine motor control",
    requirements=[
        "Accept Ethereum blockchain data in JSON format",
        "Validate data structure and ranges", 
        "Transform price data to motor control values",
        "Calculate activity levels from gas prices",
        "Support JSON serialization with computed fields"
    ],
    validation_rules=[
        "ETH price must be between 100-50000 USD",
        "Gas price must be between 0.1-1000 Gwei",
        "Percentages must be between 0-100"
    ],
    success_criteria=[
        "All validation tests pass",
        "JSON round-trip serialization works",
        "Motor control values calculated correctly",
        "90% code coverage achieved"
    ]
)

# Generate complete implementation with tests
success = run_tdd_workflow(
    spec=ethereum_spec,
    project_root=".",
    implementation_path="./src/ethereum_data_processor.py"
)
```

## Files Created

The framework creates a complete project structure:

```
project/
├── tests/
│   └── test_MyComponent.py          # Comprehensive test suite
├── src/
│   └── my_component.py              # Implementation template
└── reports/
    └── tdd/
        ├── tdd_session_123.json     # Session report
        ├── test_result_123.json     # Test results
        └── validation_123.json      # Validation report
```

## Testing the Framework

Run the framework test suite:

```bash
python scripts/test_tdd_workflow.py
```

This demonstrates:
- Component specification creation
- Test generation following proven patterns
- Implementation template generation
- Integration with existing Drawing Machine models
- Complete TDD workflow execution

## Use in Claude Code Sessions

The TDD Workflow Manager is designed for Claude Code development sessions:

1. **Import** the framework at the start of coding sessions
2. **Create specifications** for new components before coding
3. **Generate tests first** to drive implementation
4. **Iterate** based on test feedback
5. **Validate** completion before moving to next component

This ensures high-quality, well-tested code that follows established patterns and maintains consistency across the Drawing Machine project.