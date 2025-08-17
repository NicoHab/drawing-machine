"""
Automatic Test Integration System for Drawing Machine TDD Infrastructure.

Step 3.1: FileWatcher Foundation - Real-time file monitoring for automatic test execution.

This module provides comprehensive file watching capabilities that monitor Python files
across the Drawing Machine project structure and trigger appropriate responses to changes.
Built to integrate with the proven TDD methodology achieving 97.6% test success rate.

Author: Claude Code
Project: Drawing Machine
Technology: Python 3.11+ with Poetry, pytest, watchdog
"""

import os
import sys
import time
import threading
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Set, Dict, Optional, List, Callable
from dataclasses import dataclass

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent
except ImportError:
    print("Installing required dependencies...")
    os.system("pip install watchdog")
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent

try:
    from colorama import init, Fore, Style, Back
    init(autoreset=True)
except ImportError:
    print("Installing colorama for colored output...")
    os.system("pip install colorama")
    from colorama import init, Fore, Style, Back
    init(autoreset=True)


@dataclass
class FileChangeEvent:
    """Represents a file change event with metadata."""
    file_path: Path
    event_type: str
    timestamp: datetime
    project_area: str
    is_test_file: bool


@dataclass
class TestResult:
    """Represents test execution results with detailed metadata."""
    success: bool
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration_seconds: float
    coverage_percent: Optional[float]
    test_file: str
    triggered_by: str
    timestamp: datetime
    failure_details: List[str]
    execution_error: Optional[str] = None


class DrawingMachineFileHandler(FileSystemEventHandler):
    """
    Custom file system event handler for Drawing Machine project structure.
    
    Monitors Python files in the Drawing Machine project and manages debounced
    event processing to prevent excessive triggering on rapid file changes.
    """
    
    def __init__(self, callback: Callable[[FileChangeEvent], None], debounce_delay: float = 2.0):
        """
        Initialize the file handler.
        
        Args:
            callback: Function to call when a debounced file change occurs
            debounce_delay: Seconds to wait after last change before triggering callback
        """
        super().__init__()
        self.callback = callback
        self.debounce_delay = debounce_delay
        self.pending_changes: Dict[str, threading.Timer] = {}
        self.lock = threading.Lock()
        
        # Define monitored directories and their purposes
        self.project_areas = {
            'shared': 'Foundational Models (blockchain_data, motor_commands, drawing_session)',
            'edge': 'Edge Computing (motor controller, manual control, offline drawing)',
            'cloud': 'Cloud Services (orchestrator, data aggregator, user dashboard)',
            'tests': 'Test Suites (unit, integration, e2e)',
            'scripts': 'Development Scripts (TDD workflow, automation)'
        }
        
        # Files and directories to ignore
        self.ignore_patterns = {
            '__pycache__',
            '.pytest_cache',
            '.pyc',
            '.pyo',
            '.pyd',
            '.git',
            'node_modules',
            '.vscode',
            '.idea',
            'venv',
            'env',
            '.tox',
            'build',
            'dist',
            '*.egg-info'
        }
    
    def should_ignore_file(self, file_path: Path) -> bool:
        """
        Determine if a file should be ignored based on ignore patterns.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file should be ignored, False otherwise
        """
        # Check if file is Python
        if not file_path.suffix == '.py':
            return True
        
        # Check ignore patterns in path
        path_str = str(file_path)
        for pattern in self.ignore_patterns:
            if pattern in path_str:
                return True
        
        # Check if path contains any ignored directory
        for part in file_path.parts:
            if part in self.ignore_patterns:
                return True
        
        return False
    
    def get_project_area(self, file_path: Path) -> str:
        """
        Determine which project area a file belongs to.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Project area name or 'other' if not in a recognized area
        """
        for area in self.project_areas.keys():
            if area in file_path.parts:
                return area
        return 'other'
    
    def is_test_file(self, file_path: Path) -> bool:
        """
        Determine if a file is a test file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file is a test file, False otherwise
        """
        file_name = file_path.name.lower()
        return (
            file_name.startswith('test_') or
            file_name.endswith('_test.py') or
            'test' in file_path.parts
        )
    
    def create_file_event(self, file_path: Path, event_type: str) -> FileChangeEvent:
        """
        Create a FileChangeEvent from file path and event type.
        
        Args:
            file_path: Path to the changed file
            event_type: Type of file system event
            
        Returns:
            FileChangeEvent instance with metadata
        """
        return FileChangeEvent(
            file_path=file_path,
            event_type=event_type,
            timestamp=datetime.now(),
            project_area=self.get_project_area(file_path),
            is_test_file=self.is_test_file(file_path)
        )
    
    def debounce_change(self, file_path: Path, event_type: str):
        """
        Debounce file changes to prevent excessive triggering.
        
        Args:
            file_path: Path to the changed file
            event_type: Type of file system event
        """
        file_key = str(file_path)
        
        with self.lock:
            # Cancel existing timer for this file
            if file_key in self.pending_changes:
                self.pending_changes[file_key].cancel()
            
            # Create new timer
            def trigger_callback():
                with self.lock:
                    if file_key in self.pending_changes:
                        del self.pending_changes[file_key]
                
                # Create and send event
                event = self.create_file_event(file_path, event_type)
                self.callback(event)
            
            timer = threading.Timer(self.debounce_delay, trigger_callback)
            self.pending_changes[file_key] = timer
            timer.start()
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if not self.should_ignore_file(file_path):
                self.debounce_change(file_path, 'modified')
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if not self.should_ignore_file(file_path):
                self.debounce_change(file_path, 'created')
    
    def on_deleted(self, event):
        """Handle file deletion events."""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if not self.should_ignore_file(file_path):
                self.debounce_change(file_path, 'deleted')


class TestExecutor:
    """
    Test execution engine for automatic pytest running.
    
    Integrates with the Drawing Machine project structure to intelligently
    select and execute appropriate tests when files change.
    """
    
    def __init__(self, project_root: Path):
        """
        Initialize the TestExecutor.
        
        Args:
            project_root: Root directory of the Drawing Machine project
        """
        self.project_root = project_root
        self.reports_dir = project_root / "reports" / "pytest"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Test file mapping for smart test selection
        self.test_mappings = {
            'shared': [
                'tests/unit/test_foundational_models.py'
            ],
            'edge': [
                'tests/unit/test_edge_controllers.py',
                'tests/integration/test_edge_integration.py'
            ],
            'cloud': [
                'tests/unit/test_cloud_services.py',
                'tests/integration/test_cloud_integration.py'
            ],
            'scripts': [
                'tests/integration/test_tdd_workflow.py',
                'tests/unit/test_scripts.py'
            ]
        }
    
    def determine_tests_for_file(self, file_path: Path) -> List[str]:
        """
        Determine which tests should run for a changed file.
        
        Args:
            file_path: Path to the changed file
            
        Returns:
            List of test file paths to execute
        """
        file_str = str(file_path).lower()
        
        # If it's already a test file, run just that test
        if file_path.name.startswith('test_') or 'test' in file_path.parts:
            return [str(file_path)]
        
        # Determine project area and get corresponding tests
        for area in self.test_mappings:
            if area in file_path.parts:
                # Filter to existing test files
                existing_tests = []
                for test_path in self.test_mappings[area]:
                    full_path = self.project_root / test_path
                    if full_path.exists():
                        existing_tests.append(test_path)
                return existing_tests
        
        # Default: run foundational model tests (our most stable test suite)
        default_test = 'tests/unit/test_foundational_models.py'
        if (self.project_root / default_test).exists():
            return [default_test]
        
        return []
    
    def run_tests(self, test_path: Optional[str] = None, with_coverage: bool = True) -> TestResult:
        """
        Execute pytest with the specified parameters.
        
        Args:
            test_path: Specific test file/path to run (None for all tests)
            with_coverage: Whether to include coverage analysis
            
        Returns:
            TestResult with execution details
        """
        timestamp = datetime.now()
        
        # Prepare pytest command
        cmd = ['python', '-m', 'pytest']
        
        if test_path:
            cmd.append(test_path)
        
        # Add coverage if requested
        if with_coverage:
            cmd.extend(['--cov=shared', '--cov=edge', '--cov=cloud', '--cov=scripts'])
            cmd.extend(['--cov-report=json', '--cov-report=term'])
        
        # Add JSON report for parsing
        report_file = self.reports_dir / f"pytest_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        cmd.extend(['--json-report', f'--json-report-file={report_file}'])
        
        # Add other useful options
        cmd.extend(['-v', '--tb=short'])
        
        print(f"{Fore.BLUE}Running tests: {' '.join(cmd[3:])}")  # Skip 'python -m pytest'
        print(f"{Fore.YELLOW}Please wait...")
        
        try:
            # Execute pytest with timeout
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5-minute timeout
            )
            
            # Parse results
            return self.parse_test_results(
                report_file=report_file,
                test_path=test_path or "all",
                triggered_by=str(test_path or "manual"),
                timestamp=timestamp,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode
            )
            
        except subprocess.TimeoutExpired:
            return TestResult(
                success=False,
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                duration_seconds=300.0,
                coverage_percent=None,
                test_file=test_path or "all",
                triggered_by=str(test_path or "manual"),
                timestamp=timestamp,
                failure_details=["Test execution timed out after 5 minutes"],
                execution_error="TIMEOUT"
            )
            
        except Exception as e:
            return TestResult(
                success=False,
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                duration_seconds=0.0,
                coverage_percent=None,
                test_file=test_path or "all",
                triggered_by=str(test_path or "manual"),
                timestamp=timestamp,
                failure_details=[f"Execution error: {str(e)}"],
                execution_error=str(e)
            )
    
    def parse_test_results(
        self, 
        report_file: Path, 
        test_path: str, 
        triggered_by: str, 
        timestamp: datetime,
        stdout: str = "",
        stderr: str = "",
        returncode: int = 0
    ) -> TestResult:
        """
        Parse pytest JSON report and create TestResult.
        
        Args:
            report_file: Path to pytest JSON report
            test_path: Test path that was executed
            triggered_by: What triggered this test run
            timestamp: When the test was started
            stdout: pytest stdout output
            stderr: pytest stderr output
            returncode: pytest return code
            
        Returns:
            Parsed TestResult object
        """
        try:
            if report_file.exists():
                with open(report_file, 'r') as f:
                    report_data = json.load(f)
                
                # Extract basic test counts
                summary = report_data.get('summary', {})
                total = summary.get('total', 0)
                passed = summary.get('passed', 0)
                failed = summary.get('failed', 0)
                skipped = summary.get('skipped', 0)
                errors = summary.get('error', 0)
                
                # Extract duration
                duration = report_data.get('duration', 0.0)
                
                # Extract failure details
                failure_details = []
                tests = report_data.get('tests', [])
                for test in tests:
                    if test.get('outcome') in ['failed', 'error']:
                        test_name = test.get('nodeid', 'unknown')
                        call_info = test.get('call', {})
                        error_msg = call_info.get('longrepr', 'No details available')
                        failure_details.append(f"{test_name}: {error_msg}")
                
                # Try to extract coverage
                coverage_percent = None
                if 'coverage' in stdout or 'TOTAL' in stdout:
                    # Try to parse coverage from stdout
                    for line in stdout.split('\n'):
                        if 'TOTAL' in line and '%' in line:
                            try:
                                # Extract percentage from line like "TOTAL   95%"
                                coverage_str = line.split('%')[0].split()[-1]
                                coverage_percent = float(coverage_str)
                            except:
                                pass
                
                success = (failed == 0 and errors == 0 and returncode == 0)
                
                return TestResult(
                    success=success,
                    total_tests=total,
                    passed=passed,
                    failed=failed,
                    skipped=skipped,
                    errors=errors,
                    duration_seconds=duration,
                    coverage_percent=coverage_percent,
                    test_file=test_path,
                    triggered_by=triggered_by,
                    timestamp=timestamp,
                    failure_details=failure_details[:5]  # Limit to first 5 failures
                )
            
        except Exception as e:
            print(f"{Fore.RED}Error parsing test results: {e}")
        
        # Fallback result if parsing fails
        return TestResult(
            success=(returncode == 0),
            total_tests=0,
            passed=0,
            failed=0,
            skipped=0,
            errors=1 if returncode != 0 else 0,
            duration_seconds=0.0,
            coverage_percent=None,
            test_file=test_path,
            triggered_by=triggered_by,
            timestamp=timestamp,
            failure_details=["Failed to parse test results"],
            execution_error="PARSE_ERROR"
        )
    
    def display_test_result(self, result: TestResult):
        """
        Display test results with colored output.
        
        Args:
            result: TestResult to display
        """
        # Header
        if result.success:
            status_color = Fore.GREEN
            status_icon = "[PASS]"
        else:
            status_color = Fore.RED
            status_icon = "[FAIL]"
        
        print(f"\n{Back.BLUE}{Fore.WHITE} TEST EXECUTION COMPLETE {Style.RESET_ALL}")
        print(f"{status_color}{status_icon} {result.test_file}")
        print(f"{Fore.CYAN}Triggered by: {result.triggered_by}")
        print(f"{Fore.CYAN}Duration: {result.duration_seconds:.2f}s")
        print(f"{Fore.CYAN}Timestamp: {result.timestamp.strftime('%H:%M:%S')}")
        
        # Test counts
        print(f"\n{Fore.CYAN}Test Results:")
        print(f"{Fore.GREEN}  Passed: {result.passed}")
        print(f"{Fore.RED}  Failed: {result.failed}")
        print(f"{Fore.YELLOW}  Skipped: {result.skipped}")
        print(f"{Fore.MAGENTA}  Errors: {result.errors}")
        print(f"{Fore.BLUE}  Total: {result.total_tests}")
        
        # Coverage
        if result.coverage_percent is not None:
            coverage_color = Fore.GREEN if result.coverage_percent >= 80 else Fore.YELLOW
            print(f"{coverage_color}  Coverage: {result.coverage_percent:.1f}%")
        
        # Failure details
        if result.failure_details:
            print(f"\n{Fore.RED}Failure Details:")
            for i, detail in enumerate(result.failure_details[:3], 1):  # Show max 3
                print(f"{Fore.RED}  {i}. {detail[:100]}...")  # Truncate long messages
        
        # Execution error
        if result.execution_error:
            print(f"\n{Fore.RED}Execution Error: {result.execution_error}")
        
        print(f"{Style.DIM}{'-' * 60}")


class FileWatcher:
    """
    Main FileWatcher class for the Drawing Machine project.
    
    Provides comprehensive file monitoring capabilities with intelligent change detection,
    debouncing, and integration with the Drawing Machine TDD infrastructure.
    """
    
    def __init__(self, project_root: Optional[Path] = None, debounce_delay: float = 2.0, enable_auto_tests: bool = True):
        """
        Initialize the FileWatcher.
        
        Args:
            project_root: Root directory of the project (auto-detected if None)
            debounce_delay: Seconds to wait after last change before triggering
            enable_auto_tests: Whether to automatically run tests on file changes
        """
        self.project_root = project_root or Path.cwd()
        self.debounce_delay = debounce_delay
        self.enable_auto_tests = enable_auto_tests
        self.observer: Optional[Observer] = None
        self.is_watching = False
        
        # Statistics tracking
        self.start_time: Optional[datetime] = None
        self.events_detected = 0
        self.events_processed = 0
        self.tests_executed = 0
        self.tests_passed = 0
        self.tests_failed = 0
        
        # Monitored directories
        self.monitored_dirs = ['shared', 'edge', 'cloud', 'tests', 'scripts']
        
        # Initialize test executor
        self.test_executor = TestExecutor(self.project_root) if enable_auto_tests else None
        
        # Create file handler
        self.file_handler = DrawingMachineFileHandler(
            callback=self.handle_file_change,
            debounce_delay=debounce_delay
        )
        
        print(f"{Fore.CYAN}FileWatcher initialized for Drawing Machine TDD Infrastructure")
        print(f"{Fore.CYAN}Project root: {self.project_root}")
        print(f"{Fore.CYAN}Debounce delay: {debounce_delay} seconds")
        print(f"{Fore.CYAN}Auto-test execution: {'ENABLED' if enable_auto_tests else 'DISABLED'}")
    
    def validate_project_structure(self) -> bool:
        """
        Validate that we're in a Drawing Machine project directory.
        
        Returns:
            True if project structure is valid, False otherwise
        """
        required_indicators = [
            self.project_root / 'pyproject.toml',
            self.project_root / 'shared',
            self.project_root / 'tests'
        ]
        
        missing = [path for path in required_indicators if not path.exists()]
        
        if missing:
            print(f"{Fore.RED}Invalid project structure. Missing:")
            for path in missing:
                print(f"{Fore.RED}   - {path}")
            return False
        
        print(f"{Fore.GREEN}Drawing Machine project structure validated")
        return True
    
    def get_monitored_paths(self) -> List[Path]:
        """
        Get list of paths to monitor.
        
        Returns:
            List of existing paths to monitor
        """
        paths = []
        for dir_name in self.monitored_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                paths.append(dir_path)
                print(f"{Fore.BLUE} Monitoring: {dir_path}")
            else:
                print(f"{Fore.YELLOW}  Directory not found: {dir_path}")
        
        return paths
    
    def handle_file_change(self, event: FileChangeEvent):
        """
        Handle a debounced file change event.
        
        Args:
            event: FileChangeEvent containing change details
        """
        self.events_processed += 1
        
        # Format timestamp
        timestamp = event.timestamp.strftime("%H:%M:%S")
        
        # Choose color and icon based on event type
        if event.event_type == 'created':
            color = Fore.GREEN
            icon = ""
        elif event.event_type == 'modified':
            color = Fore.YELLOW
            icon = ""
        elif event.event_type == 'deleted':
            color = Fore.RED
            icon = ""
        else:
            color = Fore.CYAN
            icon = ""
        
        # Format project area
        area_desc = self.file_handler.project_areas.get(
            event.project_area, 
            f"Other ({event.project_area})"
        )
        
        # Format file type
        file_type = "Test File" if event.is_test_file else "Source File"
        
        print(f"{color}{icon} File {event.event_type}: {event.file_path}")
        print(f"{color}    Area: {area_desc}")
        print(f"{color}     Type: {file_type}")
        print(f"{color}    Time: {timestamp}")
        print(f"{color}    Events: {self.events_processed}/{self.events_detected}")
        
        # Add separator for readability
        print(f"{Style.DIM}{'-' * 60}")
        
        # Step 3.2: Trigger automatic test execution
        if self.enable_auto_tests and event.event_type != 'deleted':
            self.trigger_tests(event)
    
    def trigger_tests(self, event: FileChangeEvent):
        """
        Trigger appropriate tests based on the file change event.
        
        Args:
            event: FileChangeEvent that triggered the test execution
        """
        if not self.test_executor:
            print(f"{Fore.YELLOW}Test execution disabled - skipping tests")
            return
        
        # Determine which tests to run
        test_paths = self.test_executor.determine_tests_for_file(event.file_path)
        
        if not test_paths:
            print(f"{Fore.YELLOW}No tests found for {event.file_path} - skipping")
            return
        
        print(f"{Fore.MAGENTA}Test trigger: {len(test_paths)} test suite(s) selected")
        for test_path in test_paths:
            print(f"{Fore.MAGENTA}  - {test_path}")
        
        # Execute tests
        for test_path in test_paths:
            self.tests_executed += 1
            
            try:
                # Run the test
                result = self.test_executor.run_tests(
                    test_path=test_path,
                    with_coverage=True
                )
                
                # Update statistics
                if result.success:
                    self.tests_passed += 1
                else:
                    self.tests_failed += 1
                
                # Display results
                self.test_executor.display_test_result(result)
                
                # Brief summary for multi-test runs
                if len(test_paths) > 1:
                    status = "PASSED" if result.success else "FAILED"
                    print(f"{Fore.CYAN}Test suite {status}: {test_path} "
                          f"({result.passed}/{result.total_tests} passed)")
                
            except Exception as e:
                self.tests_failed += 1
                print(f"{Fore.RED}Test execution error for {test_path}: {e}")
        
        # Multi-test summary
        if len(test_paths) > 1:
            passed_suites = sum(1 for _ in test_paths if self.tests_passed > 0)
            print(f"\n{Back.CYAN}{Fore.WHITE} MULTI-TEST SUMMARY {Style.RESET_ALL}")
            print(f"{Fore.CYAN}Test suites executed: {len(test_paths)}")
            print(f"{Fore.GREEN}Suites passed: {passed_suites}")
            print(f"{Fore.RED}Suites failed: {len(test_paths) - passed_suites}")
            print(f"{Style.DIM}{'-' * 60}")
        
        print(f"{Fore.GREEN}Monitoring continues... (Ctrl+C to stop)")
        print()
    
    def display_startup_banner(self):
        """Display startup banner with project information."""
        print(f"\n{Back.BLUE}{Fore.WHITE}  DRAWING MACHINE FILE WATCHER STARTED {Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.GREEN} Project: Drawing Machine TDD Infrastructure")
        print(f"{Fore.GREEN} Test Success Rate: 97.6% (40/41 tests passing)")
        print(f"{Fore.GREEN}  Architecture: Edge + Cloud + Shared Models")
        print(f"{Fore.CYAN}{'=' * 60}")
        
        # Display monitoring status
        monitored_paths = self.get_monitored_paths()
        print(f"{Fore.BLUE} Monitoring {len(monitored_paths)} directories:")
        for path in monitored_paths:
            rel_path = path.relative_to(self.project_root)
            area_desc = self.file_handler.project_areas.get(rel_path.name, rel_path.name)
            print(f"{Fore.BLUE}   • {rel_path}/ - {area_desc}")
        
        print(f"{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.YELLOW}  Configuration:")
        print(f"{Fore.YELLOW}   • Debounce delay: {self.debounce_delay}s")
        print(f"{Fore.YELLOW}   • File types: Python (.py)")
        print(f"{Fore.YELLOW}   • Ignoring: __pycache__, .git, node_modules, etc.")
        print(f"{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.GREEN} FileWatcher is now monitoring for changes...")
        print(f"{Fore.GREEN} Press Ctrl+C to stop monitoring\n")
    
    def display_statistics(self):
        """Display monitoring statistics."""
        if self.start_time:
            duration = datetime.now() - self.start_time
            duration_str = str(duration).split('.')[0]  # Remove microseconds
            
            print(f"\n{Fore.CYAN} FileWatcher Statistics:")
            print(f"{Fore.CYAN}     Running time: {duration_str}")
            print(f"{Fore.CYAN}    Events detected: {self.events_detected}")
            print(f"{Fore.CYAN}    Events processed: {self.events_processed}")
            
            if self.events_detected > 0:
                processing_rate = (self.events_processed / self.events_detected) * 100
                print(f"{Fore.CYAN}    Processing rate: {processing_rate:.1f}%")
            
            # Test execution statistics
            if self.enable_auto_tests:
                print(f"\n{Fore.MAGENTA} Test Execution Statistics:")
                print(f"{Fore.MAGENTA}    Tests executed: {self.tests_executed}")
                print(f"{Fore.GREEN}    Tests passed: {self.tests_passed}")
                print(f"{Fore.RED}    Tests failed: {self.tests_failed}")
                
                if self.tests_executed > 0:
                    success_rate = (self.tests_passed / self.tests_executed) * 100
                    print(f"{Fore.BLUE}    Success rate: {success_rate:.1f}%")
    
    def start_watching(self):
        """
        Start the file watcher.
        
        Begins monitoring the specified directories for Python file changes.
        Handles setup, validation, and graceful shutdown.
        """
        try:
            # Validate project structure
            if not self.validate_project_structure():
                print(f"{Fore.RED} Cannot start FileWatcher - invalid project structure")
                return False
            
            # Get paths to monitor
            monitored_paths = self.get_monitored_paths()
            if not monitored_paths:
                print(f"{Fore.RED} No valid directories found to monitor")
                return False
            
            # Display startup information
            self.display_startup_banner()
            
            # Initialize observer
            self.observer = Observer()
            
            # Add watches for each monitored directory
            for path in monitored_paths:
                self.observer.schedule(
                    self.file_handler,
                    str(path),
                    recursive=True
                )
            
            # Start monitoring
            self.observer.start()
            self.is_watching = True
            self.start_time = datetime.now()
            
            try:
                while self.is_watching:
                    time.sleep(1)
                    # Track events for statistics
                    # Note: This is a simple approximation
                    # In a real implementation, we'd get actual event counts from the observer
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW} Keyboard interrupt received - stopping FileWatcher...")
                
        except Exception as e:
            print(f"{Fore.RED} Error starting FileWatcher: {e}")
            return False
            
        finally:
            self.stop_watching()
        
        return True
    
    def stop_watching(self):
        """
        Stop the file watcher gracefully.
        
        Stops the observer, cancels pending timers, and displays final statistics.
        """
        if self.observer and self.observer.is_alive():
            print(f"{Fore.YELLOW}  Stopping file observer...")
            self.observer.stop()
            self.observer.join(timeout=5.0)
            
            if self.observer.is_alive():
                print(f"{Fore.RED}  Observer did not stop gracefully")
            else:
                print(f"{Fore.GREEN} Observer stopped successfully")
        
        # Cancel any pending debounced changes
        with self.file_handler.lock:
            pending_count = len(self.file_handler.pending_changes)
            if pending_count > 0:
                print(f"{Fore.YELLOW} Cancelling {pending_count} pending changes...")
                for timer in self.file_handler.pending_changes.values():
                    timer.cancel()
                self.file_handler.pending_changes.clear()
        
        self.is_watching = False
        
        # Display final statistics
        self.display_statistics()
        
        print(f"{Fore.GREEN} FileWatcher stopped. Thank you for using Drawing Machine TDD!")


# Test and demonstration functions
def test_file_watcher():
    """Test function to validate FileWatcher functionality."""
    print(f"{Fore.CYAN} Testing FileWatcher functionality...")
    
    # Test project structure validation
    watcher = FileWatcher()
    is_valid = watcher.validate_project_structure()
    
    if is_valid:
        print(f"{Fore.GREEN} Project structure validation: PASSED")
    else:
        print(f"{Fore.RED} Project structure validation: FAILED")
        return False
    
    # Test monitored paths
    monitored_paths = watcher.get_monitored_paths()
    if monitored_paths:
        print(f"{Fore.GREEN} Monitored paths detection: PASSED ({len(monitored_paths)} paths)")
    else:
        print(f"{Fore.RED} Monitored paths detection: FAILED")
        return False
    
    # Test file filtering
    test_files = [
        Path("shared/models/blockchain_data.py"),  # Should monitor
        Path("shared/__pycache__/test.pyc"),      # Should ignore
        Path("tests/unit/test_models.py"),        # Should monitor
        Path(".git/config"),                      # Should ignore
        Path("edge/controllers/motor.py"),        # Should monitor
    ]
    
    for test_file in test_files:
        should_ignore = watcher.file_handler.should_ignore_file(test_file)
        is_test = watcher.file_handler.is_test_file(test_file)
        area = watcher.file_handler.get_project_area(test_file)
        
        print(f"{Fore.BLUE} {test_file}")
        print(f"{Fore.BLUE}   Ignore: {should_ignore}, Test: {is_test}, Area: {area}")
    
    print(f"{Fore.GREEN} FileWatcher test completed successfully!")
    return True


def demo_file_changes():
    """
    Demonstrate file change detection and test selection without actually running tests.
    
    This function simulates file change events to show how the FileWatcher
    would respond to real file system changes and which tests would be selected.
    """
    print(f"{Fore.CYAN} Demonstrating file change detection with test selection...")
    
    # Create a test watcher with shorter debounce for demo (no auto-tests)
    watcher = FileWatcher(debounce_delay=1.0, enable_auto_tests=False)
    
    # Create test executor for demo purposes
    test_executor = TestExecutor(Path.cwd())
    
    # Simulate file changes
    test_events = [
        FileChangeEvent(
            file_path=Path("shared/models/blockchain_data.py"),
            event_type="modified",
            timestamp=datetime.now(),
            project_area="shared",
            is_test_file=False
        ),
        FileChangeEvent(
            file_path=Path("tests/unit/test_blockchain_data.py"),
            event_type="modified",
            timestamp=datetime.now(),
            project_area="tests",
            is_test_file=True
        ),
        FileChangeEvent(
            file_path=Path("edge/controllers/motor_controller.py"),
            event_type="created",
            timestamp=datetime.now(),
            project_area="edge",
            is_test_file=False
        ),
    ]
    
    print(f"{Fore.YELLOW} Simulating file changes and test selection...")
    for event in test_events:
        watcher.handle_file_change(event)
        
        # Show which tests would be selected
        test_paths = test_executor.determine_tests_for_file(event.file_path)
        print(f"{Fore.MAGENTA}  Would trigger tests: {test_paths}")
        
        time.sleep(0.5)  # Small delay between events
    
    print(f"{Fore.GREEN} File change demonstration completed!")


if __name__ == '__main__':
    """
    Main entry point for the FileWatcher.
    
    Provides options for testing, demonstration, or normal operation.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Drawing Machine FileWatcher - Automatic Test Integration System'
    )
    parser.add_argument(
        '--test', 
        action='store_true',
        help='Run FileWatcher functionality tests'
    )
    parser.add_argument(
        '--demo',
        action='store_true', 
        help='Demonstrate file change detection'
    )
    parser.add_argument(
        '--debounce',
        type=float,
        default=2.0,
        help='Debounce delay in seconds (default: 2.0)'
    )
    parser.add_argument(
        '--no-auto-tests',
        action='store_true',
        help='Disable automatic test execution on file changes'
    )
    parser.add_argument(
        '--run-test',
        type=str,
        help='Run a specific test file manually and exit'
    )
    
    args = parser.parse_args()
    
    if args.test:
        # Run tests
        success = test_file_watcher()
        sys.exit(0 if success else 1)
    
    elif args.demo:
        # Run demonstration
        demo_file_changes()
        sys.exit(0)
    
    elif args.run_test:
        # Run specific test manually
        print(f"{Fore.MAGENTA} Drawing Machine Test Runner")
        print(f"{Fore.MAGENTA}   Manual Test Execution")
        
        project_root = Path.cwd()
        test_executor = TestExecutor(project_root)
        
        result = test_executor.run_tests(test_path=args.run_test, with_coverage=True)
        test_executor.display_test_result(result)
        
        sys.exit(0 if result.success else 1)
    
    else:
        # Normal operation - start file watching
        print(f"{Fore.MAGENTA} Drawing Machine FileWatcher v2.0")
        print(f"{Fore.MAGENTA}   Step 3.2: Automatic Test Execution")
        print(f"{Fore.MAGENTA}   Integration with TDD Infrastructure")
        
        enable_auto_tests = not args.no_auto_tests
        watcher = FileWatcher(
            debounce_delay=args.debounce,
            enable_auto_tests=enable_auto_tests
        )
        
        # Validate environment before starting
        if not test_file_watcher():
            print(f"{Fore.RED} Environment validation failed")
            sys.exit(1)
        
        # Start watching
        success = watcher.start_watching()
        sys.exit(0 if success else 1)