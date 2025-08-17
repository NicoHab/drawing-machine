#!/usr/bin/env python3
"""
TDD Project Template Generator

Creates production-ready TDD projects based on the proven Drawing Machine methodology
that achieved 97.6% test success rate (40/41 tests passing).

Includes:
- Pydantic models with comprehensive validation
- FastAPI services with TDD infrastructure
- Automatic test execution with FileWatcher
- Docker development environment
- Poetry dependency management
- Proven testing patterns from Drawing Machine

Author: Claude Code
Based on: Drawing Machine TDD Infrastructure
"""

import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

try:
    from colorama import init, Fore, Style, Back

    init(autoreset=True)
except ImportError:
    # Fallback if colorama not available
    class Fore:
        GREEN = YELLOW = RED = CYAN = BLUE = MAGENTA = ""

    class Style:
        DIM = RESET_ALL = ""

    class Back:
        BLUE = ""


@dataclass
class ProjectConfig:
    """Configuration for TDD project generation."""

    name: str
    description: str
    author: str
    template_type: str
    target_directory: Path
    include_docker: bool = True
    include_fastapi: bool = False
    include_database: bool = False
    python_version: str = "3.11"
    coverage_target: int = 90


class TDDProjectGenerator:
    """
    TDD Project Template Generator based on Drawing Machine patterns.

    Generates production-ready projects with comprehensive TDD infrastructure,
    proven patterns, and automatic test execution capabilities.
    """

    def __init__(self, source_root: Optional[Path] = None):
        """
        Initialize the TDD project generator.

        Args:
            source_root: Root directory containing the Drawing Machine source
        """
        self.source_root = source_root or Path(__file__).parent.parent
        self.templates_dir = self.source_root / "templates"

        # Available project templates
        self.template_types = {
            "service": "FastAPI service with TDD infrastructure",
            "models": "Pydantic models with comprehensive testing",
            "integration": "Integration testing framework",
            "minimal": "Minimal TDD project setup",
        }

        print(f"{Fore.CYAN}TDD Project Generator initialized")
        print(f"{Fore.CYAN}Source: {self.source_root}")
        print(f"{Fore.CYAN}Templates: {len(self.template_types)} available")

    def create_project(self, config: ProjectConfig) -> bool:
        """
        Create a TDD project from configuration.

        Args:
            config: Project configuration

        Returns:
            True if project created successfully
        """
        try:
            print(
                f"\n{Back.BLUE}{Fore.WHITE} CREATING TDD PROJECT: {config.name} {Style.RESET_ALL}"
            )
            print(f"{Fore.GREEN}Template: {config.template_type}")
            print(f"{Fore.GREEN}Target: {config.target_directory}")
            print(f"{Fore.GREEN}Coverage Target: {config.coverage_target}%")

            # Create project directory
            project_dir = config.target_directory / config.name
            if project_dir.exists():
                print(f"{Fore.RED}Error: Directory {project_dir} already exists")
                return False

            project_dir.mkdir(parents=True)
            print(f"{Fore.GREEN}Created project directory: {project_dir}")

            # Generate project structure
            self._create_project_structure(project_dir, config)

            # Generate core files
            self._generate_core_files(project_dir, config)

            # Generate template-specific files
            if config.template_type == "service":
                self._generate_service_files(project_dir, config)
            elif config.template_type == "models":
                self._generate_models_files(project_dir, config)
            elif config.template_type == "integration":
                self._generate_integration_files(project_dir, config)
            elif config.template_type == "minimal":
                self._generate_minimal_files(project_dir, config)

            # Copy TDD infrastructure
            self._copy_tdd_infrastructure(project_dir, config)

            # Generate documentation
            self._generate_documentation(project_dir, config)

            print(f"\n{Fore.GREEN}✅ TDD Project '{config.name}' created successfully!")
            print(f"{Fore.YELLOW}Next steps:")
            print(f"{Fore.YELLOW}  1. cd {project_dir}")
            print(f"{Fore.YELLOW}  2. poetry install")
            print(f"{Fore.YELLOW}  3. python scripts/auto_test_runner.py --test")
            print(
                f"{Fore.YELLOW}  4. python scripts/auto_test_runner.py  # Start TDD monitoring"
            )

            return True

        except Exception as e:
            print(f"{Fore.RED}Error creating project: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _create_project_structure(self, project_dir: Path, config: ProjectConfig):
        """Create the basic project directory structure."""
        directories = [
            "src",
            "src/models",
            "tests",
            "tests/unit",
            "tests/integration",
            "tests/fixtures",
            "scripts",
            "docs",
            "reports",
            "reports/pytest",
            "reports/coverage",
        ]

        if config.include_fastapi or config.template_type == "service":
            directories.extend(
                ["src/api", "src/api/routes", "src/services", "tests/api"]
            )

        if config.include_docker:
            directories.extend(["docker", "docker/dev"])

        for directory in directories:
            (project_dir / directory).mkdir(parents=True, exist_ok=True)
            # Create __init__.py files for Python packages
            if any(pkg in directory for pkg in ["src", "tests"]):
                (project_dir / directory / "__init__.py").write_text("")

        print(f"{Fore.BLUE}Created {len(directories)} directories")

    def _generate_core_files(self, project_dir: Path, config: ProjectConfig):
        """Generate core project files."""

        # pyproject.toml with proven dependencies
        pyproject_content = self._generate_pyproject_toml(config)
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        # pytest.ini with coverage configuration
        pytest_ini = self._generate_pytest_ini(config)
        (project_dir / "pytest.ini").write_text(pytest_ini)

        # .gitignore
        gitignore = self._generate_gitignore()
        (project_dir / ".gitignore").write_text(gitignore)

        # VS Code settings for TDD
        vscode_dir = project_dir / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        (vscode_dir / "settings.json").write_text(self._generate_vscode_settings())
        (vscode_dir / "tasks.json").write_text(self._generate_vscode_tasks())

        # Environment configuration
        (project_dir / ".env.example").write_text(self._generate_env_example(config))

        print(f"{Fore.BLUE}Generated core configuration files")

    def _generate_service_files(self, project_dir: Path, config: ProjectConfig):
        """Generate FastAPI service files with TDD patterns."""

        # Main FastAPI application
        main_app = self._generate_fastapi_main(config)
        (project_dir / "src" / "main.py").write_text(main_app)

        # Example API models
        api_models = self._generate_api_models(config)
        (project_dir / "src" / "models" / "api_models.py").write_text(api_models)

        # Example API routes
        api_routes = self._generate_api_routes(config)
        (project_dir / "src" / "api" / "routes" / "example.py").write_text(api_routes)
        (project_dir / "src" / "api" / "__init__.py").write_text("")
        (project_dir / "src" / "api" / "routes" / "__init__.py").write_text("")

        # Service layer
        service_layer = self._generate_service_layer(config)
        (project_dir / "src" / "services" / "example_service.py").write_text(
            service_layer
        )
        (project_dir / "src" / "services" / "__init__.py").write_text("")

        # API tests
        api_tests = self._generate_api_tests(config)
        (project_dir / "tests" / "api" / "test_example_api.py").write_text(api_tests)
        (project_dir / "tests" / "api" / "__init__.py").write_text("")

        print(f"{Fore.BLUE}Generated FastAPI service files with TDD patterns")

    def _generate_models_files(self, project_dir: Path, config: ProjectConfig):
        """Generate Pydantic models with comprehensive testing."""

        # Example models based on Drawing Machine patterns
        example_models = self._generate_example_models(config)
        (project_dir / "src" / "models" / "example_models.py").write_text(
            example_models
        )

        # Base model with common patterns
        base_model = self._generate_base_model(config)
        (project_dir / "src" / "models" / "base.py").write_text(base_model)

        # Model tests based on test_foundational_models.py success
        model_tests = self._generate_model_tests(config)
        (project_dir / "tests" / "unit" / "test_example_models.py").write_text(
            model_tests
        )

        # Test fixtures
        test_fixtures = self._generate_test_fixtures(config)
        (project_dir / "tests" / "fixtures" / "model_fixtures.py").write_text(
            test_fixtures
        )

        print(f"{Fore.BLUE}Generated Pydantic models with comprehensive tests")

    def _generate_integration_files(self, project_dir: Path, config: ProjectConfig):
        """Generate integration testing framework."""

        # Integration test base
        integration_base = self._generate_integration_base(config)
        (project_dir / "tests" / "integration" / "test_base.py").write_text(
            integration_base
        )

        # Example integration tests
        integration_tests = self._generate_integration_tests(config)
        (
            project_dir / "tests" / "integration" / "test_example_integration.py"
        ).write_text(integration_tests)

        # Test utilities
        test_utils = self._generate_test_utils(config)
        (project_dir / "tests" / "utils.py").write_text(test_utils)

        print(f"{Fore.BLUE}Generated integration testing framework")

    def _generate_minimal_files(self, project_dir: Path, config: ProjectConfig):
        """Generate minimal TDD setup."""

        # Simple example module
        example_module = self._generate_minimal_module(config)
        (project_dir / "src" / "example.py").write_text(example_module)

        # Basic tests
        basic_tests = self._generate_minimal_tests(config)
        (project_dir / "tests" / "unit" / "test_example.py").write_text(basic_tests)

        print(f"{Fore.BLUE}Generated minimal TDD setup")

    def _generate_minimal_module(self, config: ProjectConfig) -> str:
        """Generate a minimal example module."""
        return f'''"""
{config.name} - Minimal Example Module

A simple calculator module to demonstrate TDD methodology.
"""

class Calculator:
    """Simple calculator for TDD demonstration."""
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        return a + b
    
    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a."""
        return a - b
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b
    
    def divide(self, a: float, b: float) -> float:
        """Divide a by b."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b


def main():
    """Example usage of the calculator."""
    calc = Calculator()
    print(f"2 + 3 = {{calc.add(2, 3)}}")
    print(f"5 - 2 = {{calc.subtract(5, 2)}}")
    print(f"4 * 3 = {{calc.multiply(4, 3)}}")
    print(f"10 / 2 = {{calc.divide(10, 2)}}")


if __name__ == "__main__":
    main()
'''

    def _generate_minimal_tests(self, config: ProjectConfig) -> str:
        """Generate minimal test suite."""
        return f'''"""
Test suite for {config.name} Calculator module.

This demonstrates TDD best practices with comprehensive test coverage.
"""

import pytest
from src.example import Calculator


class TestCalculator:
    """Test cases for the Calculator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calc = Calculator()
    
    def test_add_positive_numbers(self):
        """Test adding two positive numbers."""
        result = self.calc.add(2, 3)
        assert result == 5
    
    def test_add_negative_numbers(self):
        """Test adding negative numbers."""
        result = self.calc.add(-2, -3)
        assert result == -5
    
    def test_add_zero(self):
        """Test adding zero."""
        result = self.calc.add(5, 0)
        assert result == 5
    
    def test_subtract_positive_numbers(self):
        """Test subtracting positive numbers."""
        result = self.calc.subtract(5, 3)
        assert result == 2
    
    def test_subtract_negative_result(self):
        """Test subtraction resulting in negative number."""
        result = self.calc.subtract(3, 5)
        assert result == -2
    
    def test_multiply_positive_numbers(self):
        """Test multiplying positive numbers."""
        result = self.calc.multiply(4, 3)
        assert result == 12
    
    def test_multiply_by_zero(self):
        """Test multiplying by zero."""
        result = self.calc.multiply(5, 0)
        assert result == 0
    
    def test_multiply_negative_numbers(self):
        """Test multiplying negative numbers."""
        result = self.calc.multiply(-2, -3)
        assert result == 6
    
    def test_divide_positive_numbers(self):
        """Test dividing positive numbers."""
        result = self.calc.divide(10, 2)
        assert result == 5
    
    def test_divide_by_zero_raises_error(self):
        """Test that dividing by zero raises ValueError."""
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            self.calc.divide(10, 0)
    
    def test_divide_negative_numbers(self):
        """Test dividing negative numbers."""
        result = self.calc.divide(-10, -2)
        assert result == 5
    
    def test_divide_fractional_result(self):
        """Test division with fractional result."""
        result = self.calc.divide(7, 2)
        assert result == 3.5


# Integration tests
class TestCalculatorIntegration:
    """Integration tests for Calculator usage patterns."""
    
    def test_chain_operations(self):
        """Test chaining multiple operations."""
        calc = Calculator()
        
        # ((2 + 3) * 4) - 1 = 19
        step1 = calc.add(2, 3)  # 5
        step2 = calc.multiply(step1, 4)  # 20
        final = calc.subtract(step2, 1)  # 19
        
        assert final == 19
    
    def test_complex_calculation(self):
        """Test a more complex calculation."""
        calc = Calculator()
        
        # (10 / 2) + (3 * 4) = 5 + 12 = 17
        division_result = calc.divide(10, 2)
        multiplication_result = calc.multiply(3, 4)
        final_result = calc.add(division_result, multiplication_result)
        
        assert final_result == 17
'''

    def _copy_tdd_infrastructure(self, project_dir: Path, config: ProjectConfig):
        """Copy TDD infrastructure from Drawing Machine."""

        scripts_dir = project_dir / "scripts"

        # Copy auto_test_runner.py
        auto_test_runner_source = self.source_root / "scripts" / "auto_test_runner.py"
        if auto_test_runner_source.exists():
            shutil.copy2(auto_test_runner_source, scripts_dir / "auto_test_runner.py")
            print(
                f"{Fore.GREEN}Copied auto_test_runner.py (FileWatcher + TestExecutor)"
            )

        # Copy TDD workflow tools if they exist
        tdd_workflow_source = self.source_root / "scripts" / "tdd_workflow.py"
        if tdd_workflow_source.exists():
            shutil.copy2(tdd_workflow_source, scripts_dir / "tdd_workflow.py")
            print(f"{Fore.GREEN}Copied tdd_workflow.py (TDD Workflow Manager)")

        # Generate Docker configuration if requested
        if config.include_docker:
            self._generate_docker_files(project_dir, config)

        print(f"{Fore.BLUE}Copied TDD infrastructure from Drawing Machine")

    def _generate_documentation(self, project_dir: Path, config: ProjectConfig):
        """Generate comprehensive project documentation."""

        # Main README
        #         readme = self._generate_readme(config) # TODO: Fix missing method
        (project_dir / "README.md").write_text(f"# {config['name']}\n\nTDD Project")

        # TDD workflow documentation
        tdd_guide = self._generate_tdd_guide(config)
        (project_dir / "docs" / "TDD_GUIDE.md").write_text(tdd_guide)

        # API documentation (if service)
        if config.template_type == "service":
            api_docs = self._generate_api_docs(config)
            (project_dir / "docs" / "API.md").write_text(api_docs)

        print(f"{Fore.BLUE}Generated comprehensive documentation")

    def _generate_pyproject_toml(self, config: ProjectConfig) -> str:
        """Generate pyproject.toml with proven dependencies."""
        return f"""[tool.poetry]
name = "{config.name.lower().replace(' ', '-')}"
version = "0.1.0"
description = "{config.description}"
authors = ["{config.author}"]
readme = "README.md"
packages = [{{include = "src"}}]

[tool.poetry.dependencies]
python = "^{config.python_version}"
pydantic = "^2.8.0"
{'fastapi = "^0.104.0"' if config.include_fastapi or config.template_type == 'service' else ''}
{'uvicorn = "^0.24.0"' if config.include_fastapi or config.template_type == 'service' else ''}
watchdog = "^3.0.0"
colorama = "^0.4.6"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
pytest-json-report = "^1.5.0"
pytest-asyncio = "^0.21.0"
{'httpx = "^0.25.0"' if config.include_fastapi or config.template_type == 'service' else ''}
black = "^23.0.0"
isort = "^5.12.0"
mypy = "^1.5.0"
flake8 = "^6.0.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html:reports/coverage",
    "--cov-fail-under={config.coverage_target}",
    "--json-report",
    "--json-report-file=reports/pytest/report.json"
]

[tool.black]
line-length = 88
target-version = ["py{config.python_version.replace('.', '')}"]
include = '\\.pyi?$'

[tool.isort]
profile = "black"
multi_line_output = 3

[tool.mypy]
python_version = "{config.python_version}"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
"""

    def _generate_pytest_ini(self, config: ProjectConfig) -> str:
        """Generate pytest.ini configuration."""
        return f"""[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --cov=src
    --cov-report=term-missing
    --cov-report=html:reports/coverage
    --cov-fail-under={config.coverage_target}
    --json-report
    --json-report-file=reports/pytest/report.json
    -v
    --tb=short
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
"""

    def _generate_gitignore(self) -> str:
        """Generate .gitignore file."""
        return """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
reports/

# Environment
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Docker
.dockerignore

# Logs
*.log
logs/

# Database
*.db
*.sqlite3

# Node.js (if frontend included)
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
"""

    def _generate_vscode_settings(self) -> str:
        """Generate VS Code settings for TDD development."""
        return """{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".pytest_cache": true,
        "htmlcov": true,
        ".coverage": true
    },
    "python.analysis.typeCheckingMode": "basic"
}"""

    def _generate_vscode_tasks(self) -> str:
        """Generate VS Code tasks for TDD workflow."""
        return """{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Run Tests",
            "type": "shell",
            "command": "python",
            "args": ["-m", "pytest", "tests/", "-v"],
            "group": "test",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        },
        {
            "label": "Run Tests with Coverage",
            "type": "shell", 
            "command": "python",
            "args": ["-m", "pytest", "tests/", "--cov=src", "--cov-report=html"],
            "group": "test",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        },
        {
            "label": "Start TDD File Watcher",
            "type": "shell",
            "command": "python",
            "args": ["scripts/auto_test_runner.py"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        },
        {
            "label": "Format Code",
            "type": "shell",
            "command": "black",
            "args": ["src/", "tests/"],
            "group": "build"
        }
    ]
}"""

    def _generate_env_example(self, config: ProjectConfig) -> str:
        """Generate example environment file."""
        env_content = f"""# {config.name} Environment Configuration

# Development settings
DEBUG=true
LOG_LEVEL=INFO

# Testing
PYTEST_COVERAGE_TARGET={config.coverage_target}
"""

        if config.include_fastapi or config.template_type == "service":
            env_content += """
# FastAPI settings
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
"""

        if config.include_database:
            env_content += """
# Database settings
DATABASE_URL=sqlite:///./test.db
TEST_DATABASE_URL=sqlite:///./test_db.db
"""

        return env_content

    def _generate_fastapi_main(self, config: ProjectConfig) -> str:
        """Generate FastAPI main application."""
        return f'''"""
{config.name} FastAPI Application

Generated by TDD Project Generator based on Drawing Machine methodology.
Includes comprehensive testing infrastructure and TDD patterns.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import example

# Create FastAPI application
app = FastAPI(
    title="{config.name}",
    description="{config.description}",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(example.router, prefix="/api/v1", tags=["example"])


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {{
        "message": "Welcome to {config.name}",
        "status": "healthy",
        "version": "0.1.0"
    }}


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {{
        "status": "healthy",
        "timestamp": "{{datetime.now().isoformat()}}"
    }}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0", 
        port=8000,
        reload=True
    )
'''

    def _generate_api_models(self, config: ProjectConfig) -> str:
        """Generate API models based on Drawing Machine patterns."""
        return f'''"""
API Models for {config.name}

Based on proven Pydantic patterns from Drawing Machine foundational models.
Includes comprehensive validation, computed fields, and JSON serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field, field_validator


class APIResponse(BaseModel):
    """Base API response model."""
    
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    @computed_field
    @property
    def timestamp_iso(self) -> str:
        """ISO formatted timestamp."""
        return self.timestamp.isoformat()


class ExampleStatus(str, Enum):
    """Example status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class ExampleModel(BaseModel):
    """
    Example model following Drawing Machine patterns.
    
    Demonstrates:
    - Comprehensive validation
    - Computed fields
    - JSON serialization support
    - Type safety
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Example name")
    value: float = Field(..., ge=0, le=1000, description="Example value (0-1000)")
    status: ExampleStatus = Field(default=ExampleStatus.ACTIVE, description="Current status")
    tags: List[str] = Field(default_factory=list, description="Associated tags")
    metadata: Dict[str, Union[str, int, float]] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name field."""
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip()
    
    @field_validator('tags')
    @classmethod 
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate tags field."""
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        return [tag.strip().lower() for tag in v if tag.strip()]
    
    @computed_field
    @property
    def display_name(self) -> str:
        """Display-friendly name."""
        return f"{{self.name}} ({{self.status.value}})"
    
    @computed_field
    @property
    def is_active(self) -> bool:
        """Check if model is active."""
        return self.status == ExampleStatus.ACTIVE
    
    @computed_field
    @property
    def age_seconds(self) -> float:
        """Age in seconds since creation."""
        return (datetime.now() - self.created_at).total_seconds()
    
    def to_summary(self) -> Dict[str, Union[str, float, bool]]:
        """Generate summary representation."""
        return {{
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "is_active": self.is_active,
            "age_seconds": self.age_seconds
        }}
    
    @classmethod
    def model_validate_json_safe(cls, json_data):
        """Safe JSON validation that excludes computed fields."""
        if isinstance(json_data, str):
            import json as std_json
            data = std_json.loads(json_data)
        else:
            data = json_data.copy() if isinstance(json_data, dict) else json_data
        
        # Remove computed fields
        computed_fields = {{'display_name', 'is_active', 'age_seconds', 'timestamp_iso'}}
        filtered_data = {{k: v for k, v in data.items() if k not in computed_fields}}
        return cls.model_validate(filtered_data)
    
    def model_dump_json_safe(self, **kwargs):
        """Safe JSON dump that excludes computed fields."""
        exclude_computed = {{'display_name', 'is_active', 'age_seconds', 'timestamp_iso'}}
        exclude = kwargs.get('exclude', set())
        if isinstance(exclude, set):
            exclude = exclude.union(exclude_computed)
        else:
            exclude = exclude_computed
        return self.model_dump_json(exclude=exclude, **kwargs)
    
    model_config = {{
        "validate_assignment": True,
        "extra": "forbid",
        "json_encoders": {{
            datetime: lambda v: v.isoformat()
        }}
    }}


class ExampleCreateRequest(BaseModel):
    """Request model for creating examples."""
    
    name: str = Field(..., min_length=1, max_length=100)
    value: float = Field(..., ge=0, le=1000)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Union[str, int, float]] = Field(default_factory=dict)


class ExampleUpdateRequest(BaseModel):
    """Request model for updating examples."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    value: Optional[float] = Field(None, ge=0, le=1000)
    status: Optional[ExampleStatus] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Union[str, int, float]]] = None


class ExampleListResponse(APIResponse):
    """Response model for listing examples."""
    
    data: List[ExampleModel] = Field(..., description="List of examples")
    total: int = Field(..., description="Total number of examples")
    page: int = Field(default=1, description="Current page number")
    per_page: int = Field(default=10, description="Items per page")
    
    @computed_field
    @property
    def has_more(self) -> bool:
        """Check if there are more pages."""
        return (self.page * self.per_page) < self.total
'''

    def _generate_api_routes(self, config: ProjectConfig) -> str:
        """Generate API routes with comprehensive testing patterns."""
        return f'''"""
Example API Routes for {config.name}

Demonstrates FastAPI patterns with comprehensive testing support.
Based on Drawing Machine TDD methodology.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from src.models.api_models import (
    ExampleModel,
    ExampleCreateRequest, 
    ExampleUpdateRequest,
    ExampleListResponse,
    APIResponse,
    ExampleStatus
)
from src.services.example_service import ExampleService

router = APIRouter()


def get_example_service() -> ExampleService:
    """Dependency injection for example service."""
    return ExampleService()


@router.get("/examples", response_model=ExampleListResponse)
async def list_examples(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[ExampleStatus] = Query(None, description="Filter by status"),
    service: ExampleService = Depends(get_example_service)
):
    """
    List examples with pagination and filtering.
    
    Returns:
        ExampleListResponse: Paginated list of examples
    """
    try:
        examples, total = await service.list_examples(
            page=page,
            per_page=per_page,
            status=status
        )
        
        return ExampleListResponse(
            success=True,
            message=f"Retrieved {{len(examples)}} examples",
            data=examples,
            total=total,
            page=page,
            per_page=per_page
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/examples/{{example_id}}", response_model=ExampleModel)
async def get_example(
    example_id: str,
    service: ExampleService = Depends(get_example_service)
):
    """
    Get a specific example by ID.
    
    Args:
        example_id: Unique identifier for the example
        
    Returns:
        ExampleModel: The requested example
        
    Raises:
        HTTPException: If example not found
    """
    example = await service.get_example(example_id)
    if not example:
        raise HTTPException(status_code=404, detail="Example not found")
    
    return example


@router.post("/examples", response_model=ExampleModel, status_code=201)
async def create_example(
    request: ExampleCreateRequest,
    service: ExampleService = Depends(get_example_service)
):
    """
    Create a new example.
    
    Args:
        request: Example creation data
        
    Returns:
        ExampleModel: The created example
    """
    try:
        example = await service.create_example(request)
        return example
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/examples/{{example_id}}", response_model=ExampleModel)
async def update_example(
    example_id: str,
    request: ExampleUpdateRequest,
    service: ExampleService = Depends(get_example_service)
):
    """
    Update an existing example.
    
    Args:
        example_id: Unique identifier for the example
        request: Update data
        
    Returns:
        ExampleModel: The updated example
        
    Raises:
        HTTPException: If example not found
    """
    try:
        example = await service.update_example(example_id, request)
        if not example:
            raise HTTPException(status_code=404, detail="Example not found")
        
        return example
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/examples/{{example_id}}", response_model=APIResponse)
async def delete_example(
    example_id: str,
    service: ExampleService = Depends(get_example_service)
):
    """
    Delete an example.
    
    Args:
        example_id: Unique identifier for the example
        
    Returns:
        APIResponse: Deletion confirmation
        
    Raises:
        HTTPException: If example not found
    """
    success = await service.delete_example(example_id)
    if not success:
        raise HTTPException(status_code=404, detail="Example not found")
    
    return APIResponse(
        success=True,
        message=f"Example {{example_id}} deleted successfully"
    )


@router.get("/examples/{{example_id}}/summary")
async def get_example_summary(
    example_id: str,
    service: ExampleService = Depends(get_example_service)
):
    """
    Get example summary information.
    
    Args:
        example_id: Unique identifier for the example
        
    Returns:
        Dict: Example summary data
    """
    example = await service.get_example(example_id)
    if not example:
        raise HTTPException(status_code=404, detail="Example not found")
    
    return example.to_summary()
'''

    def _generate_service_layer(self, config: ProjectConfig) -> str:
        """Generate service layer with business logic."""
        return f'''"""
Example Service Layer for {config.name}

Implements business logic with comprehensive error handling and testing support.
Based on Drawing Machine TDD patterns.
"""

from typing import List, Optional, Tuple
from datetime import datetime

from src.models.api_models import (
    ExampleModel,
    ExampleCreateRequest,
    ExampleUpdateRequest,
    ExampleStatus
)


class ExampleService:
    """
    Example service implementing business logic.
    
    In a real application, this would interact with a database,
    external APIs, or other data sources.
    """
    
    def __init__(self):
        """Initialize the service with in-memory storage for demo."""
        self._storage: List[ExampleModel] = []
        self._create_sample_data()
    
    def _create_sample_data(self):
        """Create some sample data for demonstration."""
        sample_examples = [
            ExampleModel(
                name="Sample Example 1",
                value=42.0,
                status=ExampleStatus.ACTIVE,
                tags=["sample", "demo"],
                metadata={{"category": "test", "priority": 1}}
            ),
            ExampleModel(
                name="Sample Example 2", 
                value=100.0,
                status=ExampleStatus.PENDING,
                tags=["sample", "pending"],
                metadata={{"category": "demo", "priority": 2}}
            )
        ]
        self._storage.extend(sample_examples)
    
    async def list_examples(
        self,
        page: int = 1,
        per_page: int = 10,
        status: Optional[ExampleStatus] = None
    ) -> Tuple[List[ExampleModel], int]:
        """
        List examples with pagination and filtering.
        
        Args:
            page: Page number (1-based)
            per_page: Items per page
            status: Optional status filter
            
        Returns:
            Tuple of (examples, total_count)
        """
        # Filter by status if provided
        filtered_examples = self._storage
        if status:
            filtered_examples = [ex for ex in self._storage if ex.status == status]
        
        total = len(filtered_examples)
        
        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_examples = filtered_examples[start_idx:end_idx]
        
        return paginated_examples, total
    
    async def get_example(self, example_id: str) -> Optional[ExampleModel]:
        """
        Get an example by ID.
        
        Args:
            example_id: Unique identifier
            
        Returns:
            ExampleModel if found, None otherwise
        """
        return next((ex for ex in self._storage if ex.id == example_id), None)
    
    async def create_example(self, request: ExampleCreateRequest) -> ExampleModel:
        """
        Create a new example.
        
        Args:
            request: Example creation data
            
        Returns:
            Created ExampleModel
            
        Raises:
            ValueError: If validation fails
        """
        # Business logic validation
        if await self._name_exists(request.name):
            raise ValueError(f"Example with name '{{request.name}}' already exists")
        
        # Create new example
        example = ExampleModel(
            name=request.name,
            value=request.value,
            tags=request.tags,
            metadata=request.metadata
        )
        
        self._storage.append(example)
        return example
    
    async def update_example(
        self,
        example_id: str,
        request: ExampleUpdateRequest
    ) -> Optional[ExampleModel]:
        """
        Update an existing example.
        
        Args:
            example_id: Unique identifier
            request: Update data
            
        Returns:
            Updated ExampleModel if found, None otherwise
            
        Raises:
            ValueError: If validation fails
        """
        example = await self.get_example(example_id)
        if not example:
            return None
        
        # Apply updates
        update_data = request.model_dump(exclude_unset=True)
        
        # Business logic validation for name uniqueness
        if "name" in update_data:
            if await self._name_exists(update_data["name"], exclude_id=example_id):
                raise ValueError(f"Example with name '{{update_data['name']}}' already exists")
        
        # Update the example
        for field, value in update_data.items():
            setattr(example, field, value)
        
        return example
    
    async def delete_example(self, example_id: str) -> bool:
        """
        Delete an example.
        
        Args:
            example_id: Unique identifier
            
        Returns:
            True if deleted, False if not found
        """
        example = await self.get_example(example_id)
        if not example:
            return False
        
        self._storage.remove(example)
        return True
    
    async def _name_exists(self, name: str, exclude_id: Optional[str] = None) -> bool:
        """
        Check if an example name already exists.
        
        Args:
            name: Name to check
            exclude_id: Optional ID to exclude from check
            
        Returns:
            True if name exists, False otherwise
        """
        for example in self._storage:
            if example.name.lower() == name.lower():
                if exclude_id and example.id == exclude_id:
                    continue
                return True
        return False
    
    async def get_statistics(self) -> dict:
        """
        Get service statistics.
        
        Returns:
            Dictionary with service statistics
        """
        total = len(self._storage)
        active = sum(1 for ex in self._storage if ex.status == ExampleStatus.ACTIVE)
        pending = sum(1 for ex in self._storage if ex.status == ExampleStatus.PENDING)
        inactive = sum(1 for ex in self._storage if ex.status == ExampleStatus.INACTIVE)
        
        return {{
            "total_examples": total,
            "active_examples": active,
            "pending_examples": pending,
            "inactive_examples": inactive,
            "last_updated": datetime.now().isoformat()
        }}
'''

    def _generate_api_tests(self, config: ProjectConfig) -> str:
        """Generate comprehensive API tests."""
        return f'''"""
API Tests for {config.name}

Comprehensive FastAPI testing based on Drawing Machine TDD methodology.
Tests all endpoints with edge cases and error conditions.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.main import app
from src.models.api_models import ExampleModel, ExampleStatus


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_example():
    """Sample example for testing."""
    return ExampleModel(
        name="Test Example",
        value=50.0,
        status=ExampleStatus.ACTIVE,
        tags=["test", "sample"],
        metadata={{"category": "test"}}
    )


class TestExampleAPI:
    """Test suite for Example API endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Welcome to {config.name}"
        assert data["status"] == "healthy"
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_list_examples_default(self, client):
        """Test listing examples with default parameters."""
        response = client.get("/api/v1/examples")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "total" in data
        assert data["page"] == 1
        assert data["per_page"] == 10
    
    def test_list_examples_with_pagination(self, client):
        """Test listing examples with pagination parameters."""
        response = client.get("/api/v1/examples?page=2&per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["per_page"] == 5
    
    def test_list_examples_with_status_filter(self, client):
        """Test listing examples with status filter."""
        response = client.get("/api/v1/examples?status=active")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Verify all returned examples have active status
        for example in data["data"]:
            assert example["status"] == "active"
    
    def test_list_examples_invalid_pagination(self, client):
        """Test listing examples with invalid pagination."""
        response = client.get("/api/v1/examples?page=0")
        assert response.status_code == 422  # Validation error
    
    def test_get_example_success(self, client, sample_example):
        """Test getting a specific example successfully."""
        # First create an example
        create_response = client.post(
            "/api/v1/examples",
            json={{
                "name": sample_example.name,
                "value": sample_example.value,
                "tags": sample_example.tags,
                "metadata": sample_example.metadata
            }}
        )
        assert create_response.status_code == 201
        created_example = create_response.json()
        example_id = created_example["id"]
        
        # Then get it
        response = client.get(f"/api/v1/examples/{{example_id}}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == example_id
        assert data["name"] == sample_example.name
    
    def test_get_example_not_found(self, client):
        """Test getting a non-existent example."""
        response = client.get("/api/v1/examples/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Example not found"
    
    def test_create_example_success(self, client):
        """Test creating an example successfully."""
        example_data = {{
            "name": "New Test Example",
            "value": 75.0,
            "tags": ["new", "test"],
            "metadata": {{"priority": 1}}
        }}
        
        response = client.post("/api/v1/examples", json=example_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == example_data["name"]
        assert data["value"] == example_data["value"]
        assert "id" in data
        assert data["status"] == "active"  # Default status
    
    def test_create_example_invalid_data(self, client):
        """Test creating an example with invalid data."""
        invalid_data = {{
            "name": "",  # Empty name should fail
            "value": -10.0  # Negative value should fail
        }}
        
        response = client.post("/api/v1/examples", json=invalid_data)
        assert response.status_code == 422
    
    def test_create_example_duplicate_name(self, client):
        """Test creating an example with duplicate name."""
        example_data = {{
            "name": "Duplicate Test",
            "value": 50.0
        }}
        
        # Create first example
        response1 = client.post("/api/v1/examples", json=example_data)
        assert response1.status_code == 201
        
        # Try to create second with same name
        response2 = client.post("/api/v1/examples", json=example_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]
    
    def test_update_example_success(self, client):
        """Test updating an example successfully."""
        # Create example first
        create_data = {{
            "name": "Update Test Example",
            "value": 30.0
        }}
        create_response = client.post("/api/v1/examples", json=create_data)
        example_id = create_response.json()["id"]
        
        # Update the example
        update_data = {{
            "name": "Updated Test Example",
            "value": 40.0,
            "status": "pending"
        }}
        
        response = client.put(f"/api/v1/examples/{{example_id}}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["value"] == update_data["value"]
        assert data["status"] == update_data["status"]
    
    def test_update_example_not_found(self, client):
        """Test updating a non-existent example."""
        update_data = {{"name": "Updated Name"}}
        response = client.put("/api/v1/examples/nonexistent-id", json=update_data)
        assert response.status_code == 404
    
    def test_update_example_invalid_data(self, client):
        """Test updating an example with invalid data."""
        # Create example first
        create_response = client.post(
            "/api/v1/examples",
            json={{"name": "Invalid Update Test", "value": 50.0}}
        )
        example_id = create_response.json()["id"]
        
        # Try to update with invalid data
        invalid_update = {{"value": 2000.0}}  # Exceeds maximum
        response = client.put(f"/api/v1/examples/{{example_id}}", json=invalid_update)
        assert response.status_code == 422
    
    def test_delete_example_success(self, client):
        """Test deleting an example successfully."""
        # Create example first
        create_response = client.post(
            "/api/v1/examples",
            json={{"name": "Delete Test Example", "value": 25.0}}
        )
        example_id = create_response.json()["id"]
        
        # Delete the example
        response = client.delete(f"/api/v1/examples/{{example_id}}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted successfully" in data["message"]
        
        # Verify it's deleted
        get_response = client.get(f"/api/v1/examples/{{example_id}}")
        assert get_response.status_code == 404
    
    def test_delete_example_not_found(self, client):
        """Test deleting a non-existent example."""
        response = client.delete("/api/v1/examples/nonexistent-id")
        assert response.status_code == 404
    
    def test_get_example_summary(self, client):
        """Test getting example summary."""
        # Create example first
        create_response = client.post(
            "/api/v1/examples",
            json={{"name": "Summary Test Example", "value": 60.0}}
        )
        example_id = create_response.json()["id"]
        
        # Get summary
        response = client.get(f"/api/v1/examples/{{example_id}}/summary")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "status" in data
        assert "is_active" in data
        assert "age_seconds" in data
    
    def test_api_error_handling(self, client):
        """Test API error handling for server errors."""
        with patch('src.services.example_service.ExampleService.list_examples') as mock_list:
            mock_list.side_effect = Exception("Database connection failed")
            
            response = client.get("/api/v1/examples")
            assert response.status_code == 500
            assert "Database connection failed" in response.json()["detail"]


class TestAPIValidation:
    """Test suite for API input validation."""
    
    def test_query_parameter_validation(self, client):
        """Test query parameter validation."""
        # Test invalid page number
        response = client.get("/api/v1/examples?page=-1")
        assert response.status_code == 422
        
        # Test invalid per_page number
        response = client.get("/api/v1/examples?per_page=0")
        assert response.status_code == 422
        
        # Test per_page exceeding maximum
        response = client.get("/api/v1/examples?per_page=1000")
        assert response.status_code == 422
    
    def test_request_body_validation(self, client):
        """Test request body validation."""
        # Test missing required fields
        response = client.post("/api/v1/examples", json={{}})
        assert response.status_code == 422
        
        # Test invalid field types
        response = client.post("/api/v1/examples", json={{
            "name": 123,  # Should be string
            "value": "not_a_number"  # Should be number
        }})
        assert response.status_code == 422
    
    def test_field_constraints(self, client):
        """Test field constraint validation."""
        # Test name length constraints
        response = client.post("/api/v1/examples", json={{
            "name": "x" * 101,  # Exceeds max length
            "value": 50.0
        }})
        assert response.status_code == 422
        
        # Test value range constraints
        response = client.post("/api/v1/examples", json={{
            "name": "Range Test",
            "value": -1.0  # Below minimum
        }})
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''

    def _generate_example_models(self, config: ProjectConfig) -> str:
        """Generate example models based on Drawing Machine patterns."""
        return f'''"""
Example Models for {config.name}

Based on proven Pydantic patterns from Drawing Machine foundational models.
Demonstrates comprehensive validation, computed fields, and JSON serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field, field_validator

from .base import BaseModelWithValidation


class Priority(str, Enum):
    """Priority level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExampleDataModel(BaseModelWithValidation):
    """
    Example data model following Drawing Machine patterns.
    
    Demonstrates:
    - Complex validation rules
    - Computed fields with business logic
    - JSON serialization safety
    - Error handling patterns
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Model name")
    description: Optional[str] = Field(None, max_length=1000, description="Model description")
    value: float = Field(..., ge=0.0, le=100.0, description="Percentage value (0-100)")
    priority: Priority = Field(default=Priority.MEDIUM, description="Priority level")
    tags: List[str] = Field(default_factory=list, description="Associated tags")
    metadata: Dict[str, Union[str, int, float, bool]] = Field(
        default_factory=dict, 
        description="Additional metadata"
    )
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    is_active: bool = Field(default=True, description="Whether the model is active")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name field with business rules."""
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        
        # Business rule: No special characters except spaces, hyphens, underscores
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_")
        if not all(c in allowed_chars for c in v):
            raise ValueError("Name contains invalid characters")
        
        return v.strip()
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate tags with constraints."""
        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")
        
        # Clean and validate each tag
        cleaned_tags = []
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError("All tags must be strings")
            
            cleaned_tag = tag.strip().lower()
            if len(cleaned_tag) == 0:
                continue  # Skip empty tags
            
            if len(cleaned_tag) > 50:
                raise ValueError("Tag length cannot exceed 50 characters")
            
            cleaned_tags.append(cleaned_tag)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in cleaned_tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)
        
        return unique_tags
    
    @field_validator('metadata')
    @classmethod
    def validate_metadata(cls, v: Dict[str, Union[str, int, float, bool]]) -> Dict[str, Union[str, int, float, bool]]:
        """Validate metadata constraints."""
        if len(v) > 50:
            raise ValueError("Maximum 50 metadata entries allowed")
        
        for key, value in v.items():
            if len(key) > 100:
                raise ValueError(f"Metadata key '{{key}}' exceeds 100 characters")
            
            if isinstance(value, str) and len(value) > 500:
                raise ValueError(f"Metadata value for '{{key}}' exceeds 500 characters")
        
        return v
    
    @computed_field
    @property
    def display_name(self) -> str:
        """Generate display-friendly name."""
        return f"{{self.name}} ({{self.priority.value.upper()}})"
    
    @computed_field
    @property
    def age_seconds(self) -> float:
        """Calculate age in seconds since creation."""
        return (datetime.now() - self.created_at).total_seconds()
    
    @computed_field
    @property
    def age_days(self) -> float:
        """Calculate age in days since creation."""
        return self.age_seconds / 86400  # 24 * 60 * 60
    
    @computed_field
    @property
    def is_critical(self) -> bool:
        """Check if model has critical priority."""
        return self.priority == Priority.CRITICAL
    
    @computed_field
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage based on value and priority."""
        priority_multiplier = {{
            Priority.LOW: 1.0,
            Priority.MEDIUM: 1.2,
            Priority.HIGH: 1.5,
            Priority.CRITICAL: 2.0
        }}
        
        base_completion = self.value
        adjusted_completion = base_completion * priority_multiplier[self.priority]
        
        # Cap at 100%
        return min(100.0, adjusted_completion)
    
    @computed_field
    @property
    def status_summary(self) -> str:
        """Generate status summary."""
        if not self.is_active:
            return "INACTIVE"
        
        if self.is_critical:
            return "CRITICAL_ACTIVE"
        
        if self.completion_percentage >= 90:
            return "NEAR_COMPLETE"
        elif self.completion_percentage >= 50:
            return "IN_PROGRESS"
        else:
            return "STARTING"
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()
    
    def add_tag(self, tag: str) -> bool:
        """
        Add a tag if not already present.
        
        Args:
            tag: Tag to add
            
        Returns:
            True if tag was added, False if already present
        """
        cleaned_tag = tag.strip().lower()
        if cleaned_tag not in self.tags:
            self.tags.append(cleaned_tag)
            self.update_timestamp()
            return True
        return False
    
    def remove_tag(self, tag: str) -> bool:
        """
        Remove a tag if present.
        
        Args:
            tag: Tag to remove
            
        Returns:
            True if tag was removed, False if not present
        """
        cleaned_tag = tag.strip().lower()
        if cleaned_tag in self.tags:
            self.tags.remove(cleaned_tag)
            self.update_timestamp()
            return True
        return False
    
    def get_metadata_value(self, key: str, default=None) -> Union[str, int, float, bool, None]:
        """
        Get metadata value with default.
        
        Args:
            key: Metadata key
            default: Default value if key not found
            
        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)
    
    def set_metadata_value(self, key: str, value: Union[str, int, float, bool]):
        """
        Set metadata value.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
        self.update_timestamp()
    
    def to_summary_dict(self) -> Dict[str, Union[str, float, bool, int]]:
        """
        Generate summary dictionary.
        
        Returns:
            Dictionary with summary information
        """
        return {{
            "id": self.id,
            "name": self.name,
            "priority": self.priority.value,
            "value": self.value,
            "completion_percentage": self.completion_percentage,
            "status_summary": self.status_summary,
            "is_active": self.is_active,
            "is_critical": self.is_critical,
            "age_days": round(self.age_days, 2),
            "tag_count": len(self.tags),
            "metadata_count": len(self.metadata)
        }}


class ExampleMetricsModel(BaseModelWithValidation):
    """Model for tracking metrics and analytics."""
    
    model_id: str = Field(..., description="Reference to ExampleDataModel ID")
    metric_name: str = Field(..., min_length=1, max_length=100, description="Metric name")
    metric_value: float = Field(..., description="Metric value")
    metric_unit: Optional[str] = Field(None, max_length=20, description="Metric unit")
    timestamp: datetime = Field(default_factory=datetime.now, description="Metric timestamp")
    
    @computed_field
    @property
    def formatted_value(self) -> str:
        """Format metric value with unit."""
        if self.metric_unit:
            return f"{{self.metric_value}} {{self.metric_unit}}"
        return str(self.metric_value)
    
    @computed_field
    @property
    def age_minutes(self) -> float:
        """Age of metric in minutes."""
        return (datetime.now() - self.timestamp).total_seconds() / 60


# Example schema instances for testing
EXAMPLE_DATA_SCHEMA = {{
    "name": "Test Example Model",
    "description": "A comprehensive test model for validation",
    "value": 75.5,
    "priority": "high",
    "tags": ["test", "example", "validation"],
    "metadata": {{
        "category": "test_data",
        "environment": "development",
        "version": 1,
        "automated": True
    }}
}}

EXAMPLE_METRICS_SCHEMA = {{
    "model_id": "test-model-id-123",
    "metric_name": "processing_time",
    "metric_value": 42.5,
    "metric_unit": "ms"
}}
'''

    def _generate_base_model(self, config: ProjectConfig) -> str:
        """Generate base model with common patterns."""
        return f'''"""
Base Models for {config.name}

Provides common functionality and patterns for all models.
Based on Drawing Machine foundational model success patterns.
"""

from typing import Dict, Any
from pydantic import BaseModel, ConfigDict


class BaseModelWithValidation(BaseModel):
    """
    Base model with common validation and serialization patterns.
    
    Includes safe JSON serialization methods that handle computed fields
    properly, based on proven patterns from Drawing Machine models.
    """
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        json_encoders={{
            # Add custom encoders as needed
        }},
        ignored_types=(property,)
    )
    
    @classmethod
    def model_validate_json_safe(cls, json_data):
        """
        Safe JSON validation that excludes computed fields.
        
        This method filters out computed fields before validation to prevent
        "Extra inputs are not permitted" errors during deserialization.
        
        Args:
            json_data: JSON string or dictionary
            
        Returns:
            Validated model instance
        """
        if isinstance(json_data, str):
            import json as std_json
            data = std_json.loads(json_data)
        else:
            data = json_data.copy() if isinstance(json_data, dict) else json_data
        
        # Get computed field names for this model
        computed_fields = set()
        if hasattr(cls.model_config, 'computed_fields'):
            computed_fields.update(cls.model_config.computed_fields.keys())
        
        # Also check for common computed field patterns
        common_computed = {{
            'display_name', 'age_seconds', 'age_days', 'age_minutes',
            'completion_percentage', 'status_summary', 'is_critical',
            'formatted_value', 'timestamp_iso'
        }}
        computed_fields.update(common_computed)
        
        # Filter out computed fields
        filtered_data = {{k: v for k, v in data.items() if k not in computed_fields}}
        
        return cls.model_validate(filtered_data)
    
    def model_dump_json_safe(self, **kwargs) -> str:
        """
        Safe JSON dump that excludes computed fields.
        
        This method excludes computed fields from serialization to ensure
        clean JSON output that can be safely deserialized.
        
        Args:
            **kwargs: Additional arguments for model_dump_json
            
        Returns:
            JSON string without computed fields
        """
        # Get computed field names for this model
        computed_fields = set()
        if hasattr(self.model_config, 'computed_fields'):
            computed_fields.update(self.model_config.computed_fields.keys())
        
        # Also exclude common computed field patterns
        common_computed = {{
            'display_name', 'age_seconds', 'age_days', 'age_minutes',
            'completion_percentage', 'status_summary', 'is_critical',
            'formatted_value', 'timestamp_iso'
        }}
        computed_fields.update(common_computed)
        
        # Merge with any existing exclude
        exclude = kwargs.get('exclude', set())
        if isinstance(exclude, set):
            exclude = exclude.union(computed_fields)
        else:
            exclude = computed_fields
        
        kwargs['exclude'] = exclude
        return self.model_dump_json(**kwargs)
    
    def to_dict_safe(self) -> Dict[str, Any]:
        """
        Convert to dictionary without computed fields.
        
        Returns:
            Dictionary representation without computed fields
        """
        return self.model_dump(exclude={{
            'display_name', 'age_seconds', 'age_days', 'age_minutes',
            'completion_percentage', 'status_summary', 'is_critical',
            'formatted_value', 'timestamp_iso'
        }})
    
    def refresh_computed_fields(self):
        """
        Force refresh of computed fields.
        
        This can be useful after updates to ensure computed fields
        reflect the latest state.
        """
        # This is a no-op since Pydantic handles computed fields automatically,
        # but can be overridden in subclasses if needed
        pass
'''

    def _generate_model_tests(self, config: ProjectConfig) -> str:
        """Generate comprehensive model tests based on test_foundational_models.py."""
        return f'''"""
Comprehensive Model Tests for {config.name}

Based on the proven testing patterns from Drawing Machine test_foundational_models.py
that achieved 97.6% test success rate (40/41 tests passing).

Tests all aspects of model functionality including:
- Model creation and validation
- Computed fields
- JSON serialization/deserialization
- Edge cases and error conditions
- Business logic validation
"""

import json
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from pydantic import ValidationError

from src.models.example_models import (
    ExampleDataModel,
    ExampleMetricsModel,
    Priority,
    EXAMPLE_DATA_SCHEMA,
    EXAMPLE_METRICS_SCHEMA
)


class TestFixtures:
    """Test data fixtures for model testing."""
    
    @pytest.fixture
    def valid_example_data(self) -> Dict[str, Any]:
        """Valid example data for testing."""
        return EXAMPLE_DATA_SCHEMA.copy()
    
    @pytest.fixture
    def valid_metrics_data(self) -> Dict[str, Any]:
        """Valid metrics data for testing."""
        return EXAMPLE_METRICS_SCHEMA.copy()
    
    @pytest.fixture
    def current_timestamp(self) -> float:
        """Current timestamp for testing."""
        return datetime.now().timestamp()


class TestExampleDataModel(TestFixtures):
    """Test suite for ExampleDataModel."""
    
    def test_create_valid_model(self, valid_example_data):
        """Test creating valid ExampleDataModel."""
        model = ExampleDataModel(**valid_example_data)
        
        assert model.name == valid_example_data["name"]
        assert model.description == valid_example_data["description"]
        assert model.value == valid_example_data["value"]
        assert model.priority == Priority(valid_example_data["priority"])
        assert model.tags == valid_example_data["tags"]
        assert model.metadata == valid_example_data["metadata"]
        assert model.is_active is True  # Default value
        assert model.id is not None  # Auto-generated
    
    def test_model_defaults(self):
        """Test model default values."""
        model = ExampleDataModel(name="Test", value=50.0)
        
        assert model.priority == Priority.MEDIUM
        assert model.tags == []
        assert model.metadata == {{}}
        assert model.is_active is True
        assert model.description is None
        assert model.updated_at is None
    
    def test_computed_fields(self, valid_example_data):
        """Test computed fields functionality."""
        model = ExampleDataModel(**valid_example_data)
        
        # Test display_name
        assert model.display_name == f"{{model.name}} ({{model.priority.value.upper()}})"
        
        # Test age calculations
        assert model.age_seconds >= 0
        assert model.age_days >= 0
        assert model.age_days == model.age_seconds / 86400
        
        # Test priority-based fields
        assert isinstance(model.is_critical, bool)
        assert model.completion_percentage >= model.value
        assert model.status_summary in [
            "INACTIVE", "CRITICAL_ACTIVE", "NEAR_COMPLETE", 
            "IN_PROGRESS", "STARTING"
        ]
    
    def test_critical_priority_detection(self):
        """Test critical priority detection."""
        critical_model = ExampleDataModel(
            name="Critical Test",
            value=50.0,
            priority=Priority.CRITICAL
        )
        
        assert critical_model.is_critical is True
        assert critical_model.completion_percentage == 100.0  # 50 * 2.0 multiplier
        assert critical_model.status_summary == "CRITICAL_ACTIVE"
        
        low_model = ExampleDataModel(
            name="Low Test",
            value=50.0,
            priority=Priority.LOW
        )
        
        assert low_model.is_critical is False
        assert low_model.completion_percentage == 50.0  # 50 * 1.0 multiplier
    
    def test_name_validation(self):
        """Test name field validation."""
        # Valid names
        valid_names = ["Test Model", "Test-Model", "Test_Model", "Test123"]
        for name in valid_names:
            model = ExampleDataModel(name=name, value=50.0)
            assert model.name == name
        
        # Invalid names
        with pytest.raises(ValidationError):
            ExampleDataModel(name="", value=50.0)  # Empty
        
        with pytest.raises(ValidationError):
            ExampleDataModel(name="   ", value=50.0)  # Whitespace only
        
        with pytest.raises(ValidationError):
            ExampleDataModel(name="Test@Model", value=50.0)  # Special chars
    
    def test_value_validation(self):
        """Test value field validation."""
        # Valid values
        valid_values = [0.0, 50.0, 100.0]
        for value in valid_values:
            model = ExampleDataModel(name="Test", value=value)
            assert model.value == value
        
        # Invalid values
        with pytest.raises(ValidationError):
            ExampleDataModel(name="Test", value=-1.0)  # Below minimum
        
        with pytest.raises(ValidationError):
            ExampleDataModel(name="Test", value=101.0)  # Above maximum
    
    def test_tags_validation(self):
        """Test tags field validation."""
        # Valid tags
        model = ExampleDataModel(
            name="Test",
            value=50.0,
            tags=["tag1", "TAG2", "  tag3  ", "tag1"]  # Duplicates and whitespace
        )
        # Should clean, lowercase, and deduplicate
        assert model.tags == ["tag1", "tag2", "tag3"]
        
        # Too many tags
        with pytest.raises(ValidationError):
            ExampleDataModel(
                name="Test",
                value=50.0,
                tags=[f"tag{{i}}" for i in range(25)]  # Exceeds 20 limit
            )
        
        # Tag too long
        with pytest.raises(ValidationError):
            ExampleDataModel(
                name="Test",
                value=50.0,
                tags=["x" * 51]  # Exceeds 50 character limit
            )
    
    def test_metadata_validation(self):
        """Test metadata field validation."""
        # Valid metadata
        valid_metadata = {{
            "string_key": "value",
            "int_key": 42,
            "float_key": 3.14,
            "bool_key": True
        }}
        model = ExampleDataModel(name="Test", value=50.0, metadata=valid_metadata)
        assert model.metadata == valid_metadata
        
        # Key too long
        with pytest.raises(ValidationError):
            ExampleDataModel(
                name="Test",
                value=50.0,
                metadata={{"x" * 101: "value"}}  # Key exceeds 100 chars
            )
        
        # String value too long
        with pytest.raises(ValidationError):
            ExampleDataModel(
                name="Test",
                value=50.0,
                metadata={{"key": "x" * 501}}  # Value exceeds 500 chars
            )
        
        # Too many entries
        with pytest.raises(ValidationError):
            ExampleDataModel(
                name="Test",
                value=50.0,
                metadata={{f"key{{i}}": f"value{{i}}" for i in range(51)}}  # Exceeds 50 entries
            )
    
    def test_tag_operations(self):
        """Test tag addition and removal operations."""
        model = ExampleDataModel(name="Test", value=50.0, tags=["initial"])
        
        # Add new tag
        result = model.add_tag("new_tag")
        assert result is True
        assert "new_tag" in model.tags
        assert model.updated_at is not None
        
        # Add duplicate tag
        result = model.add_tag("new_tag")
        assert result is False
        
        # Remove existing tag
        result = model.remove_tag("new_tag")
        assert result is True
        assert "new_tag" not in model.tags
        
        # Remove non-existent tag
        result = model.remove_tag("nonexistent")
        assert result is False
    
    def test_metadata_operations(self):
        """Test metadata operations."""
        model = ExampleDataModel(name="Test", value=50.0)
        
        # Get non-existent key with default
        value = model.get_metadata_value("nonexistent", "default")
        assert value == "default"
        
        # Set metadata value
        model.set_metadata_value("test_key", "test_value")
        assert model.metadata["test_key"] == "test_value"
        assert model.updated_at is not None
        
        # Get existing value
        value = model.get_metadata_value("test_key")
        assert value == "test_value"
    
    def test_summary_dict(self, valid_example_data):
        """Test summary dictionary generation."""
        model = ExampleDataModel(**valid_example_data)
        summary = model.to_summary_dict()
        
        required_keys = {{
            "id", "name", "priority", "value", "completion_percentage",
            "status_summary", "is_active", "is_critical", "age_days",
            "tag_count", "metadata_count"
        }}
        
        assert all(key in summary for key in required_keys)
        assert summary["tag_count"] == len(model.tags)
        assert summary["metadata_count"] == len(model.metadata)
    
    def test_json_serialization(self, valid_example_data):
        """Test JSON serialization/deserialization round-trip."""
        model = ExampleDataModel(**valid_example_data)
        
        # Test safe serialization (excludes computed fields)
        json_str = model.model_dump_json_safe()
        assert isinstance(json_str, str)
        
        # Verify computed fields are not in JSON
        json_data = json.loads(json_str)
        computed_fields = {{
            'display_name', 'age_seconds', 'age_days', 'completion_percentage',
            'status_summary', 'is_critical'
        }}
        assert not any(field in json_data for field in computed_fields)
        
        # Test safe deserialization (round-trip)
        reconstructed = ExampleDataModel.model_validate_json_safe(json_str)
        assert reconstructed.name == model.name
        assert reconstructed.value == model.value
        assert reconstructed.priority == model.priority
        
        # Test that computed fields work on reconstructed object
        assert hasattr(reconstructed, 'display_name')
        assert hasattr(reconstructed, 'completion_percentage')
        assert reconstructed.display_name is not None
    
    def test_json_with_computed_fields_error_prevention(self, valid_example_data):
        """Test that including computed fields in JSON doesn't break validation."""
        model = ExampleDataModel(**valid_example_data)
        
        # Get JSON with computed fields (unsafe)
        json_data = json.loads(model.model_dump_json())
        
        # Add computed fields manually (simulating external JSON)
        json_data['display_name'] = "Manual Display Name"
        json_data['age_seconds'] = 12345
        json_data['completion_percentage'] = 99.9
        
        # Safe validation should work despite computed fields being present
        reconstructed = ExampleDataModel.model_validate_json_safe(json_data)
        assert reconstructed.name == model.name
        
        # Computed fields should be recalculated, not from JSON
        assert reconstructed.display_name != "Manual Display Name"
        assert reconstructed.age_seconds != 12345


class TestExampleMetricsModel(TestFixtures):
    """Test suite for ExampleMetricsModel."""
    
    def test_create_valid_metrics(self, valid_metrics_data):
        """Test creating valid ExampleMetricsModel."""
        metrics = ExampleMetricsModel(**valid_metrics_data)
        
        assert metrics.model_id == valid_metrics_data["model_id"]
        assert metrics.metric_name == valid_metrics_data["metric_name"]
        assert metrics.metric_value == valid_metrics_data["metric_value"]
        assert metrics.metric_unit == valid_metrics_data["metric_unit"]
    
    def test_metrics_computed_fields(self, valid_metrics_data):
        """Test metrics computed fields."""
        metrics = ExampleMetricsModel(**valid_metrics_data)
        
        # Test formatted_value
        expected_format = f"{{metrics.metric_value}} {{metrics.metric_unit}}"
        assert metrics.formatted_value == expected_format
        
        # Test age calculation
        assert metrics.age_minutes >= 0
    
    def test_metrics_without_unit(self):
        """Test metrics without unit."""
        metrics = ExampleMetricsModel(
            model_id="test-id",
            metric_name="count",
            metric_value=42.0
        )
        
        assert metrics.formatted_value == "42.0"
    
    def test_metrics_json_serialization(self, valid_metrics_data):
        """Test metrics JSON serialization."""
        metrics = ExampleMetricsModel(**valid_metrics_data)
        
        # Test round-trip
        json_str = metrics.model_dump_json_safe()
        reconstructed = ExampleMetricsModel.model_validate_json_safe(json_str)
        
        assert reconstructed.model_id == metrics.model_id
        assert reconstructed.metric_name == metrics.metric_name
        assert reconstructed.metric_value == metrics.metric_value


class TestModelIntegration:
    """Integration tests between models."""
    
    def test_model_relationships(self, valid_example_data, valid_metrics_data):
        """Test relationships between models."""
        # Create data model
        data_model = ExampleDataModel(**valid_example_data)
        
        # Create metrics for the data model
        metrics_data = valid_metrics_data.copy()
        metrics_data["model_id"] = data_model.id
        
        metrics = ExampleMetricsModel(**metrics_data)
        
        assert metrics.model_id == data_model.id
    
    def test_comprehensive_json_round_trip(self, valid_example_data, valid_metrics_data):
        """Test comprehensive JSON round-trip for all models."""
        # Test ExampleDataModel
        data_model = ExampleDataModel(**valid_example_data)
        data_json = data_model.model_dump_json_safe()
        data_reconstructed = ExampleDataModel.model_validate_json_safe(data_json)
        
        assert data_reconstructed.name == data_model.name
        assert data_reconstructed.value == data_model.value
        assert data_reconstructed.priority == data_model.priority
        assert data_reconstructed.tags == data_model.tags
        assert data_reconstructed.metadata == data_model.metadata
        
        # Test ExampleMetricsModel
        metrics_model = ExampleMetricsModel(**valid_metrics_data)
        metrics_json = metrics_model.model_dump_json_safe()
        metrics_reconstructed = ExampleMetricsModel.model_validate_json_safe(metrics_json)
        
        assert metrics_reconstructed.model_id == metrics_model.model_id
        assert metrics_reconstructed.metric_name == metrics_model.metric_name
        assert metrics_reconstructed.metric_value == metrics_model.metric_value
    
    def test_example_schemas_validation(self, current_timestamp):
        """Test that all example schemas are valid."""
        # Update timestamps to current time
        example_data = EXAMPLE_DATA_SCHEMA.copy()
        
        # Test data model schema
        ExampleDataModel(**example_data)
        
        # Test metrics model schema
        metrics_data = EXAMPLE_METRICS_SCHEMA.copy()
        ExampleMetricsModel(**metrics_data)
    
    def test_edge_case_validations(self):
        """Test various edge cases and boundary conditions."""
        # Test minimum values
        min_model = ExampleDataModel(
            name="A",  # Minimum length
            value=0.0,  # Minimum value
            priority=Priority.LOW
        )
        assert min_model.name == "A"
        assert min_model.value == 0.0
        
        # Test maximum values
        max_model = ExampleDataModel(
            name="X" * 200,  # Maximum length
            value=100.0,  # Maximum value
            priority=Priority.CRITICAL,
            tags=[f"tag{{i:02d}}" for i in range(20)],  # Maximum tags
            metadata={{f"key{{i:02d}}": f"val{{i:02d}}" for i in range(50)}}  # Maximum metadata
        )
        assert len(max_model.name) == 200
        assert max_model.value == 100.0
        assert len(max_model.tags) == 20
        assert len(max_model.metadata) == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''


def run_interactive_wizard():
    """Run interactive project creation wizard."""
    print(f"\n{Back.BLUE}{Fore.WHITE} TDD PROJECT CREATION WIZARD {Style.RESET_ALL}")
    print(f"{Fore.CYAN}Based on Drawing Machine methodology (97.6% test success rate)")
    print(f"{Fore.CYAN}{'=' * 60}")

    # Get project details
    name = input(f"{Fore.YELLOW}Project name: ").strip()
    if not name:
        print(f"{Fore.RED}Project name is required")
        return None

    description = input(f"{Fore.YELLOW}Project description: ").strip()
    if not description:
        description = f"TDD project: {name}"

    author = input(f"{Fore.YELLOW}Author name: ").strip()
    if not author:
        author = "TDD Developer"

    # Choose template type
    print(f"\n{Fore.CYAN}Available template types:")
    generator = TDDProjectGenerator()
    for i, (template_type, description) in enumerate(
        generator.template_types.items(), 1
    ):
        print(f"{Fore.CYAN}  {i}. {template_type}: {description}")

    while True:
        try:
            choice = input(
                f"{Fore.YELLOW}Choose template type (1-{len(generator.template_types)}): "
            ).strip()
            template_index = int(choice) - 1
            template_type = list(generator.template_types.keys())[template_index]
            break
        except (ValueError, IndexError):
            print(
                f"{Fore.RED}Invalid choice. Please enter a number between 1 and {len(generator.template_types)}"
            )

    # Additional options
    include_docker = input(
        f"{Fore.YELLOW}Include Docker configuration? (Y/n): "
    ).strip().lower() in ["", "y", "yes"]

    include_fastapi = False
    if template_type in ["service", "minimal"]:
        include_fastapi = input(
            f"{Fore.YELLOW}Include FastAPI? (Y/n): "
        ).strip().lower() in ["", "y", "yes"]

    # Target directory
    target_dir = input(f"{Fore.YELLOW}Target directory (default: current): ").strip()
    if not target_dir:
        target_dir = "."

    # Coverage target
    coverage_input = input(
        f"{Fore.YELLOW}Coverage target percentage (default: 90): "
    ).strip()
    try:
        coverage_target = int(coverage_input) if coverage_input else 90
        if coverage_target < 50 or coverage_target > 100:
            coverage_target = 90
    except ValueError:
        coverage_target = 90

    # Create configuration
    config = ProjectConfig(
        name=name,
        description=description,
        author=author,
        template_type=template_type,
        target_directory=Path(target_dir),
        include_docker=include_docker,
        include_fastapi=include_fastapi,
        coverage_target=coverage_target,
    )

    return config


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="TDD Project Template Generator based on Drawing Machine methodology"
    )
    parser.add_argument("--name", type=str, help="Project name")
    parser.add_argument(
        "--type",
        choices=["service", "models", "integration", "minimal"],
        default="minimal",
        help="Template type",
    )
    parser.add_argument("--description", type=str, help="Project description")
    parser.add_argument(
        "--author", type=str, default="TDD Developer", help="Author name"
    )
    parser.add_argument("--target-dir", type=str, default=".", help="Target directory")
    parser.add_argument(
        "--coverage", type=int, default=90, help="Coverage target percentage"
    )
    parser.add_argument(
        "--no-docker", action="store_true", help="Skip Docker configuration"
    )
    parser.add_argument(
        "--interactive", action="store_true", help="Run interactive wizard"
    )

    args = parser.parse_args()

    try:
        if args.interactive:
            # Run interactive wizard
            config = run_interactive_wizard()
            if not config:
                sys.exit(1)
        else:
            # Use command line arguments
            if not args.name:
                print(
                    f"{Fore.RED}Error: Project name is required (use --name or --interactive)"
                )
                sys.exit(1)

            config = ProjectConfig(
                name=args.name,
                description=args.description or f"TDD project: {args.name}",
                author=args.author,
                template_type=args.type,
                target_directory=Path(args.target_dir),
                include_docker=not args.no_docker,
                include_fastapi=args.type == "service",
                coverage_target=args.coverage,
            )

        # Create the project
        generator = TDDProjectGenerator()
        success = generator.create_project(config)

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Project creation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
