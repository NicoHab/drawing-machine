# Claude Code TDD Commands

Universal Test-Driven Development commands for any technology stack, language, or framework.

## /tdd-start [component-name] [language/framework]

Begin TDD session for any technology stack.

**Usage:**
```
/tdd-start UserService python/fastapi
/tdd-start PaymentProcessor javascript/node
/tdd-start DataValidator rust/tokio
/tdd-start AuthController java/spring
/tdd-start ComponentLibrary typescript/react
```

**What it does:**
- Creates component specification from requirements
- Generates comprehensive test suite first (RED phase)
- Sets up minimal implementation template
- Initializes TDD workflow tracking
- Configures language-specific test runner

**Framework Support:**
- **Python**: pytest, unittest, FastAPI, Django, Flask
- **JavaScript/TypeScript**: Jest, Vitest, Mocha, Node.js, React, Vue
- **Java**: JUnit, TestNG, Spring Boot, Maven, Gradle
- **C#**: NUnit, xUnit, MSTest, .NET Core
- **Rust**: cargo test, tokio-test
- **Go**: go test, testify
- **Ruby**: RSpec, Minitest, Rails
- **PHP**: PHPUnit, Laravel, Symfony

## /tdd-red

Write failing tests for current requirement.

**Usage:**
```
/tdd-red "User should be able to authenticate with email and password"
/tdd-red "Component should validate input data and throw specific errors"
/tdd-red "API should return paginated results with proper metadata"
```

**What it does:**
- Analyzes requirement and creates comprehensive test cases
- Generates edge cases and error conditions
- Follows language-specific testing conventions
- Ensures tests fail initially (RED phase)
- Creates test fixtures and mocks as needed

**Generated Test Types:**
- Unit tests for core functionality
- Integration tests for component interactions
- Error handling and validation tests
- Performance and boundary condition tests
- Serialization/deserialization tests (when applicable)

## /tdd-green

Implement minimal code to pass failing tests.

**Usage:**
```
/tdd-green
/tdd-green --verbose  # Show detailed implementation reasoning
/tdd-green --minimal  # Absolute minimal implementation
```

**What it does:**
- Analyzes failing tests to understand requirements
- Implements minimal code to make tests pass
- Follows SOLID principles and clean code practices
- Uses appropriate design patterns for the language
- Maintains existing test coverage

**Implementation Strategies:**
- Start with simplest possible implementation
- Use dependency injection where appropriate
- Follow language idioms and conventions
- Implement error handling as required by tests
- Add logging and observability hooks

## /tdd-refactor

Improve code quality while maintaining test success.

**Usage:**
```
/tdd-refactor
/tdd-refactor --focus performance
/tdd-refactor --focus readability
/tdd-refactor --focus patterns
/tdd-refactor --suggest-only  # Just suggest improvements
```

**What it does:**
- Analyzes current implementation for improvement opportunities
- Refactors code while ensuring all tests continue to pass
- Applies design patterns where beneficial
- Improves performance without breaking functionality
- Enhances code readability and maintainability

**Refactoring Focus Areas:**
- **Performance**: Optimize algorithms, reduce complexity
- **Readability**: Improve naming, structure, documentation
- **Patterns**: Apply appropriate design patterns
- **Security**: Address security concerns and best practices
- **Maintainability**: Reduce coupling, increase cohesion

## /tdd-cycle

Run complete RED-GREEN-REFACTOR cycle.

**Usage:**
```
/tdd-cycle "User registration with email validation"
/tdd-cycle "Data processing pipeline with error handling"
/tdd-cycle --iterations 3  # Run multiple cycles
```

**What it does:**
- Combines /tdd-red, /tdd-green, and /tdd-refactor
- Runs complete TDD cycle for a feature
- Validates each phase before proceeding
- Generates comprehensive test coverage
- Produces production-ready code

**Cycle Steps:**
1. **RED**: Write failing tests for requirement
2. **GREEN**: Implement minimal code to pass tests
3. **REFACTOR**: Improve code quality while maintaining tests
4. **VALIDATE**: Ensure all tests pass and coverage meets threshold

## /tdd-test

Run tests and analyze results.

**Usage:**
```
/tdd-test
/tdd-test --coverage
/tdd-test --watch  # Continuous testing
/tdd-test --filter "user auth"  # Run specific tests
/tdd-test --performance  # Include performance benchmarks
```

**What it does:**
- Executes test suite using appropriate runner
- Analyzes test results and failures
- Provides coverage reports and metrics
- Suggests fixes for failing tests
- Benchmarks performance where applicable

**Language-Specific Runners:**
- **Python**: `pytest --cov` or `python -m unittest`
- **JavaScript**: `npm test` or `yarn test`
- **Java**: `mvn test` or `gradle test`
- **C#**: `dotnet test`
- **Rust**: `cargo test`
- **Go**: `go test ./...`

## /tdd-spec

Create or update component specification.

**Usage:**
```
/tdd-spec
/tdd-spec --update  # Update existing specification
/tdd-spec --export json  # Export as JSON
/tdd-spec --import requirements.md  # Import from file
```

**What it does:**
- Creates structured component specification
- Defines requirements, dependencies, and success criteria
- Establishes validation rules and constraints
- Sets up examples and test data
- Tracks specification changes over time

**Specification Structure:**
```yaml
component:
  name: ComponentName
  description: Component purpose and functionality
  
requirements:
  functional:
    - Requirement 1
    - Requirement 2
  non_functional:
    - Performance requirements
    - Security requirements
    
dependencies:
  - External dependency 1
  - External dependency 2
  
validation_rules:
  - Input validation rule
  - Business logic rule
  
success_criteria:
  - All tests pass (100%)
  - Code coverage >= 90%
  - Performance benchmarks met
  - Security scan passes
```

## /tdd-coverage

Analyze test coverage and identify gaps.

**Usage:**
```
/tdd-coverage
/tdd-coverage --threshold 90
/tdd-coverage --report html
/tdd-coverage --uncovered  # Show uncovered lines
```

**What it does:**
- Generates comprehensive coverage reports
- Identifies untested code paths
- Suggests additional tests for uncovered areas
- Validates coverage meets project requirements
- Tracks coverage trends over time

**Coverage Metrics:**
- Line coverage
- Branch coverage
- Function/method coverage
- Statement coverage
- Condition coverage (where supported)

## /tdd-mock

Generate mocks and test doubles.

**Usage:**
```
/tdd-mock DatabaseService
/tdd-mock --type stub PaymentGateway
/tdd-mock --spy UserRepository
/tdd-mock --fake --data-generator EmailService
```

**What it does:**
- Creates appropriate test doubles for dependencies
- Generates realistic test data
- Sets up behavior verification
- Configures mock responses and side effects
- Follows language-specific mocking conventions

**Mock Types:**
- **Stub**: Returns predefined responses
- **Mock**: Behavior verification with expectations
- **Spy**: Wraps real object with behavior tracking
- **Fake**: Working implementation for testing
- **Dummy**: Placeholder objects for parameter passing

## /tdd-integration

Set up integration testing.

**Usage:**
```
/tdd-integration --database
/tdd-integration --api --port 3000
/tdd-integration --containers docker
/tdd-integration --e2e selenium
```

**What it does:**
- Sets up integration test environment
- Configures test databases and external services
- Creates end-to-end test scenarios
- Sets up containerized test environments
- Configures CI/CD integration testing

**Integration Types:**
- Database integration tests
- API integration tests
- Service-to-service integration
- UI integration tests
- End-to-end workflow tests

## /tdd-performance

Add performance testing and benchmarks.

**Usage:**
```
/tdd-performance
/tdd-performance --load-test
/tdd-performance --memory-profile
/tdd-performance --benchmark --iterations 1000
```

**What it does:**
- Creates performance test suites
- Sets up load testing scenarios
- Configures memory and CPU profiling
- Establishes performance benchmarks
- Monitors performance regressions

**Performance Test Types:**
- Unit performance tests
- Load and stress testing
- Memory usage profiling
- CPU performance benchmarking
- I/O and network performance

## /tdd-security

Add security testing to TDD workflow.

**Usage:**
```
/tdd-security
/tdd-security --owasp-top-10
/tdd-security --auth-tests
/tdd-security --input-validation
```

**What it does:**
- Creates security-focused test cases
- Tests for common vulnerabilities
- Validates authentication and authorization
- Tests input validation and sanitization
- Performs security scanning

**Security Test Areas:**
- Input validation and XSS prevention
- SQL injection prevention
- Authentication and session management
- Authorization and access control
- Data encryption and privacy

## /tdd-report

Generate comprehensive TDD session report.

**Usage:**
```
/tdd-report
/tdd-report --format html
/tdd-report --export pdf
/tdd-report --metrics-only
```

**What it does:**
- Generates detailed TDD session reports
- Includes test results and coverage metrics
- Shows code quality improvements
- Tracks TDD cycle statistics
- Provides recommendations for improvement

**Report Sections:**
- Session summary and metrics
- Test results and coverage
- Code quality analysis
- Performance benchmarks
- Security scan results
- Recommendations and next steps

## Language-Specific TDD Patterns

### Python/Pydantic Pattern
```python
# /tdd-start UserModel python/pydantic
from pydantic import BaseModel, Field, validator
import pytest

class TestUserModel:
    def test_create_valid_user(self):
        user = UserModel(name="John", email="john@example.com")
        assert user.name == "John"
    
    def test_email_validation(self):
        with pytest.raises(ValidationError):
            UserModel(name="John", email="invalid")

class UserModel(BaseModel):
    name: str = Field(..., min_length=1)
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
```

### JavaScript/Jest Pattern
```javascript
// /tdd-start UserService javascript/jest
describe('UserService', () => {
  test('should create user with valid data', () => {
    const service = new UserService();
    const user = service.create({ name: 'John', email: 'john@example.com' });
    expect(user.name).toBe('John');
  });
  
  test('should validate email format', () => {
    const service = new UserService();
    expect(() => {
      service.create({ name: 'John', email: 'invalid' });
    }).toThrow('Invalid email format');
  });
});
```

### Java/JUnit Pattern
```java
// /tdd-start UserService java/junit
@Test
public class UserServiceTest {
    @Test
    void shouldCreateUserWithValidData() {
        UserService service = new UserService();
        User user = service.create("John", "john@example.com");
        assertEquals("John", user.getName());
    }
    
    @Test
    void shouldValidateEmailFormat() {
        UserService service = new UserService();
        assertThrows(ValidationException.class, () -> {
            service.create("John", "invalid");
        });
    }
}
```

### C#/NUnit Pattern
```csharp
// /tdd-start UserService csharp/nunit
[TestFixture]
public class UserServiceTests
{
    [Test]
    public void ShouldCreateUserWithValidData()
    {
        var service = new UserService();
        var user = service.Create("John", "john@example.com");
        Assert.AreEqual("John", user.Name);
    }
    
    [Test]
    public void ShouldValidateEmailFormat()
    {
        var service = new UserService();
        Assert.Throws<ValidationException>(() => {
            service.Create("John", "invalid");
        });
    }
}
```

### Rust Pattern
```rust
// /tdd-start user_service rust/tokio
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn should_create_user_with_valid_data() {
        let service = UserService::new();
        let user = service.create("John", "john@example.com").unwrap();
        assert_eq!(user.name, "John");
    }
    
    #[test]
    fn should_validate_email_format() {
        let service = UserService::new();
        let result = service.create("John", "invalid");
        assert!(result.is_err());
    }
}
```

## TDD Workflow Integration

### With CI/CD
```yaml
# .github/workflows/tdd.yml
name: TDD Workflow
on: [push, pull_request]

jobs:
  tdd:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run TDD Tests
        run: /tdd-test --coverage --threshold 90
      - name: Performance Tests
        run: /tdd-performance --benchmark
      - name: Security Tests
        run: /tdd-security --owasp-top-10
```

### With Docker
```dockerfile
# Dockerfile.tdd
FROM node:16
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
CMD ["/tdd-test", "--watch"]
```

### With IDE Integration
```json
// .vscode/tasks.json
{
  "tasks": [
    {
      "label": "TDD Red",
      "type": "shell",
      "command": "/tdd-red",
      "group": "test"
    },
    {
      "label": "TDD Green", 
      "type": "shell",
      "command": "/tdd-green",
      "group": "test"
    },
    {
      "label": "TDD Refactor",
      "type": "shell", 
      "command": "/tdd-refactor",
      "group": "test"
    }
  ]
}
```

## Best Practices

### TDD Commandments
1. **Never write production code without a failing test**
2. **Write only enough test to demonstrate a failure**
3. **Write only enough code to make the test pass**
4. **Refactor both test and production code for quality**
5. **Run tests frequently and fix failures immediately**

### Command Usage Guidelines
- Start every feature with `/tdd-start`
- Use `/tdd-cycle` for complete feature development
- Run `/tdd-test --coverage` frequently
- Use `/tdd-refactor` to improve code quality
- Generate `/tdd-report` at milestone completion

### Quality Gates
- **Red Phase**: Tests must fail for the right reason
- **Green Phase**: All tests must pass
- **Refactor Phase**: No test failures during refactoring
- **Coverage**: Maintain minimum coverage threshold
- **Performance**: No performance regressions

## Example Complete Workflow

```bash
# Start new feature development
/tdd-start PaymentProcessor javascript/node

# Define requirements
/tdd-spec --update
# Add requirement: "Process credit card payments securely"

# Write failing test (RED)
/tdd-red "Should process valid credit card payment"

# Implement minimal code (GREEN)
/tdd-green

# Improve code quality (REFACTOR)
/tdd-refactor --focus security

# Add more tests and features
/tdd-cycle "Should handle payment failures gracefully"
/tdd-cycle "Should validate card expiration dates"

# Performance and security testing
/tdd-performance --load-test
/tdd-security --owasp-top-10

# Final validation
/tdd-test --coverage --threshold 95
/tdd-report --format html

# Integration testing
/tdd-integration --api --containers docker
```

This completes the universal TDD commands for Claude Code, supporting any technology stack with comprehensive testing strategies!