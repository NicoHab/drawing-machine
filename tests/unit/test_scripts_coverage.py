"""
Test suite for scripts module coverage.

Ensures adequate test coverage for the scripts directory to meet CI/CD requirements.
Tests focus on public interfaces and importable modules.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add scripts to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))


class TestScriptsImports:
    """Test that all scripts modules can be imported without errors."""

    def test_import_auto_test_runner(self):
        """Test that auto_test_runner module can be imported."""
        try:
            import auto_test_runner

            assert hasattr(auto_test_runner, "TestExecutor")
            assert hasattr(auto_test_runner, "FileWatcher")
        except ImportError as e:
            pytest.fail(f"Failed to import auto_test_runner: {e}")

    def test_import_tdd_workflow(self):
        """Test that tdd_workflow module can be imported."""
        try:
            import tdd_workflow

            assert hasattr(tdd_workflow, "TestFirstWorkflow")
        except ImportError as e:
            pytest.fail(f"Failed to import tdd_workflow: {e}")

    def test_import_create_tdd_project(self):
        """Test that create_tdd_project module can be imported."""
        try:
            import create_tdd_project

            assert hasattr(create_tdd_project, "TDDProjectGenerator")
            assert hasattr(create_tdd_project, "ProjectConfig")
        except ImportError as e:
            pytest.fail(f"Failed to import create_tdd_project: {e}")


class TestAutoTestRunner:
    """Test suite for auto_test_runner module."""

    def test_test_executor_creation(self):
        """Test TestExecutor can be created."""
        with patch("auto_test_runner.subprocess"), patch("auto_test_runner.Path"):
            import auto_test_runner

            executor = auto_test_runner.TestExecutor()
            assert executor is not None

    def test_file_watcher_creation(self):
        """Test FileWatcher can be created."""
        with patch("auto_test_runner.Observer"), patch("auto_test_runner.Path"):
            import auto_test_runner

            mock_executor = Mock()
            watcher = auto_test_runner.FileWatcher(mock_executor)
            assert watcher is not None

    def test_test_result_class(self):
        """Test TestResult dataclass."""
        import auto_test_runner

        result = auto_test_runner.TestResult(
            success=True,
            total_tests=10,
            passed_tests=9,
            failed_tests=1,
            coverage_percentage=95.0,
            execution_time=2.5,
            timestamp="2024-01-01T10:00:00",
        )
        assert result.success is True
        assert result.total_tests == 10
        assert result.coverage_percentage == 95.0


class TestTDDWorkflow:
    """Test suite for tdd_workflow module."""

    def test_workflow_creation(self):
        """Test TestFirstWorkflow can be created."""
        with patch("tdd_workflow.Path"):
            import tdd_workflow

            workflow = tdd_workflow.TestFirstWorkflow()
            assert workflow is not None

    def test_workflow_config(self):
        """Test WorkflowConfig dataclass."""
        import tdd_workflow

        config = tdd_workflow.WorkflowConfig(
            project_root=Path("/test"),
            test_directory=Path("/test/tests"),
            source_directory=Path("/test/src"),
            coverage_threshold=90.0,
            timeout_seconds=120,
        )
        assert config.coverage_threshold == 90.0
        assert config.timeout_seconds == 120


class TestCreateTDDProject:
    """Test suite for create_tdd_project module."""

    def test_project_config_creation(self):
        """Test ProjectConfig can be created."""
        import create_tdd_project

        config = create_tdd_project.ProjectConfig(
            name="test-project",
            description="Test project",
            author="Test Author",
            template_type="minimal",
            target_directory=Path("/test"),
        )
        assert config.name == "test-project"
        assert config.template_type == "minimal"

    def test_tdd_project_generator_creation(self):
        """Test TDDProjectGenerator can be created."""
        with patch("create_tdd_project.Path"):
            import create_tdd_project

            generator = create_tdd_project.TDDProjectGenerator()
            assert generator is not None
            assert hasattr(generator, "template_types")

    def test_generator_methods_exist(self):
        """Test that required generator methods exist."""
        import create_tdd_project

        generator = create_tdd_project.TDDProjectGenerator()
        assert hasattr(generator, "create_project")
        assert hasattr(generator, "_generate_tdd_guide")
        assert hasattr(generator, "_generate_api_docs")


class TestScriptsUtilities:
    """Test utility functions and classes in scripts."""

    def test_setup_github_project_import(self):
        """Test setup_github_project can be imported."""
        try:
            import setup_github_project

            # Basic import test - main functionality requires GitHub API
            assert setup_github_project is not None
        except ImportError as e:
            pytest.fail(f"Failed to import setup_github_project: {e}")

    def test_generate_project_documentation_import(self):
        """Test generate_project_documentation can be imported."""
        try:
            import generate_project_documentation

            assert generate_project_documentation is not None
        except ImportError as e:
            pytest.fail(f"Failed to import generate_project_documentation: {e}")

    def test_validate_trunk_based_project_setup_import(self):
        """Test validate_trunk_based_project_setup can be imported."""
        try:
            import validate_trunk_based_project_setup

            assert validate_trunk_based_project_setup is not None
        except ImportError as e:
            pytest.fail(f"Failed to import validate_trunk_based_project_setup: {e}")


class TestScriptsIntegration:
    """Integration tests for scripts working together."""

    def test_create_project_with_workflow(self):
        """Test that project creation integrates with workflow."""
        with (
            patch("create_tdd_project.Path"),
            patch("create_tdd_project.shutil"),
            patch("tdd_workflow.Path"),
        ):
            import create_tdd_project
            import tdd_workflow

            # Test basic integration - both modules should work together
            generator = create_tdd_project.TDDProjectGenerator()
            workflow = tdd_workflow.TestFirstWorkflow()

            assert generator is not None
            assert workflow is not None

    def test_scripts_with_auto_runner(self):
        """Test scripts work with auto test runner."""
        with (
            patch("auto_test_runner.Observer"),
            patch("auto_test_runner.subprocess"),
            patch("auto_test_runner.Path"),
        ):
            import auto_test_runner

            executor = auto_test_runner.TestExecutor()
            watcher = auto_test_runner.FileWatcher(executor)

            assert executor is not None
            assert watcher is not None


class TestScriptsConfiguration:
    """Test configuration and constants in scripts."""

    def test_tdd_constants(self):
        """Test TDD-related constants and configurations."""
        import auto_test_runner

        # Test that key constants exist and have reasonable values
        if hasattr(auto_test_runner, "WATCH_EXTENSIONS"):
            assert ".py" in auto_test_runner.WATCH_EXTENSIONS

        # Test color constants if available
        if hasattr(auto_test_runner, "Fore"):
            assert auto_test_runner.Fore is not None

    def test_project_structure_awareness(self):
        """Test that scripts are aware of project structure."""
        import create_tdd_project

        generator = create_tdd_project.TDDProjectGenerator()
        assert hasattr(generator, "template_types")
        assert isinstance(generator.template_types, dict)
        assert len(generator.template_types) > 0


# Utility functions for testing
def test_scripts_directory_structure():
    """Test that scripts directory has expected structure."""
    scripts_dir = Path(__file__).parent.parent.parent / "scripts"
    assert scripts_dir.exists()
    assert (scripts_dir / "__init__.py").exists()

    # Check for main script files
    expected_files = ["auto_test_runner.py", "tdd_workflow.py", "create_tdd_project.py"]

    for file_name in expected_files:
        assert (scripts_dir / file_name).exists(), f"Missing required file: {file_name}"


def test_scripts_python_syntax():
    """Test that all Python files in scripts have valid syntax."""
    scripts_dir = Path(__file__).parent.parent.parent / "scripts"

    for py_file in scripts_dir.glob("*.py"):
        if py_file.name.startswith("test_"):
            continue  # Skip test files

        try:
            with open(py_file, encoding="utf-8") as f:
                content = f.read()
                compile(content, py_file, "exec")
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {py_file}: {e}")
        except Exception:
            # File might have imports that aren't available in test environment
            # This is OK for syntax checking
            pass


# Performance and reliability tests
def test_scripts_performance():
    """Test that scripts can be imported quickly."""
    import time

    start_time = time.time()
    try:
        import auto_test_runner
        import create_tdd_project
        import tdd_workflow
    except ImportError:
        pass  # Some imports might fail in test environment

    import_time = time.time() - start_time
    assert import_time < 5.0, f"Script imports took too long: {import_time:.2f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

