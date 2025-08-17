"""
Integration test for the FileWatcher system.

Tests the complete FileWatcher functionality with real file operations
to ensure it works correctly in a live environment.
"""

import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from auto_test_runner import FileChangeEvent, FileWatcher


@contextmanager
def temporary_test_file(content="# Test file\npass\n"):
    """Create a temporary Python file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)

    try:
        yield temp_path
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_file_watcher_integration():
    """Test FileWatcher with real file operations."""
    print("Starting FileWatcher integration test...")

    # Track detected events
    detected_events = []

    def event_handler(event: FileChangeEvent):
        detected_events.append(event)
        print(f"Detected: {event.event_type} - {event.file_path}")

    # Create FileWatcher with very short debounce for testing
    watcher = FileWatcher(debounce_delay=0.5)
    watcher.file_handler.callback = event_handler

    # Start observer (but not the full watching loop)
    from watchdog.observers import Observer

    observer = Observer()

    try:
        # Create test directory in current project
        test_dir = Path("test_watcher_temp")
        test_dir.mkdir(exist_ok=True)

        # Set up monitoring on test directory
        observer.schedule(watcher.file_handler, str(test_dir), recursive=True)
        observer.start()

        print(f"Monitoring test directory: {test_dir}")

        # Test 1: Create a new Python file
        print("\nTest 1: Creating new Python file...")
        test_file = test_dir / "test_module.py"
        test_file.write_text("# New test module\ndef hello():\n    return 'world'\n")

        # Wait for event detection
        time.sleep(1.0)

        # Test 2: Modify the file
        print("\nTest 2: Modifying Python file...")
        test_file.write_text(
            "# Modified test module\ndef hello():\n    return 'modified world'\n"
        )

        # Wait for event detection
        time.sleep(1.0)

        # Test 3: Create a file that should be ignored
        print("\nTest 3: Creating file that should be ignored...")
        ignore_file = test_dir / "test.pyc"
        ignore_file.write_text("compiled bytecode")

        # Wait for event detection
        time.sleep(1.0)

        # Test 4: Delete the Python file
        print("\nTest 4: Deleting Python file...")
        test_file.unlink()

        # Wait for event detection
        time.sleep(1.0)

        # Analyze results
        print("\nAnalyzing results...")
        print(f"Total events detected: {len(detected_events)}")

        # Filter events for our test file (ignore any system-generated events)
        relevant_events = [
            e for e in detected_events if "test_module.py" in str(e.file_path)
        ]

        print(f"Relevant events for test_module.py: {len(relevant_events)}")

        # Verify we detected the expected events
        event_types = [e.event_type for e in relevant_events]
        print(f"Event types detected: {event_types}")

        # Check for expected events
        # Note: 'created' might be merged with 'modified' on some file systems
        required_events = ["modified", "deleted"]
        optional_events = ["created"]
        success = True

        # Check required events
        for required in required_events:
            if required not in event_types:
                print(f"[FAIL] Missing required event: {required}")
                success = False
            else:
                print(f"[PASS] Found required event: {required}")

        # Check optional events
        for optional in optional_events:
            if optional in event_types:
                print(f"[PASS] Found optional event: {optional}")
            else:
                print(
                    f"[NOTE] Optional event not detected: {optional} (this is normal)"
                )

        # Verify ignored file was not processed
        ignored_events = [e for e in detected_events if "test.pyc" in str(e.file_path)]

        if ignored_events:
            print(f"[FAIL] Processed {len(ignored_events)} events for ignored file")
            success = False
        else:
            print("[PASS] Correctly ignored .pyc file")

        return success

    except Exception as e:
        print(f"[ERROR] Integration test failed: {e}")
        return False

    finally:
        # Cleanup
        observer.stop()
        observer.join()

        # Remove test directory
        if test_dir.exists():
            for file in test_dir.iterdir():
                file.unlink()
            test_dir.rmdir()

        print("Integration test cleanup completed")


def test_debouncing():
    """Test the debouncing functionality."""
    print("\nTesting debouncing functionality...")

    detected_events = []

    def event_handler(event: FileChangeEvent):
        detected_events.append(event)
        print(f"Debounced event: {event.event_type} - {event.file_path}")

    # Create FileWatcher with 1 second debounce
    watcher = FileWatcher(debounce_delay=1.0)
    watcher.file_handler.callback = event_handler

    # Simulate rapid file changes
    test_file = Path("shared/models/test_debounce.py")

    print("Simulating rapid file changes...")

    # Trigger multiple rapid changes
    for i in range(5):
        watcher.file_handler.debounce_change(test_file, "modified")
        time.sleep(0.1)  # Rapid changes

    # Wait for debounce to trigger
    print("Waiting for debounce...")
    time.sleep(2.0)

    # Check that only one event was processed despite 5 triggers
    if len(detected_events) == 1:
        print(
            "[PASS] Debouncing working correctly - 5 rapid changes resulted in 1 event"
        )
        return True
    else:
        print(
            f"[FAIL] Debouncing failed - expected 1 event, got {len(detected_events)}"
        )
        return False


if __name__ == "__main__":
    print("FileWatcher Integration Test Suite")
    print("=" * 50)

    # Run integration test
    integration_success = test_file_watcher_integration()

    # Run debouncing test
    debouncing_success = test_debouncing()

    # Summary
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Integration Test: {'[PASS]' if integration_success else '[FAIL]'}")
    print(f"Debouncing Test: {'[PASS]' if debouncing_success else '[FAIL]'}")

    overall_success = integration_success and debouncing_success
    print(
        f"Overall: {'[ALL TESTS PASSED]' if overall_success else '[SOME TESTS FAILED]'}"
    )

    if overall_success:
        print("\nFileWatcher is ready for production use!")
    else:
        print("\nFileWatcher needs attention before production use.")

