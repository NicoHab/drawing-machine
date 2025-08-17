"""
Basic test to verify pytest functionality.
"""


def test_basic_functionality():
    """Test basic functionality to ensure pytest works."""
    assert True


def test_basic_math():
    """Test basic math operations."""
    assert 2 + 2 == 4
    assert 10 - 5 == 5
    assert 3 * 4 == 12


def test_string_operations():
    """Test string operations."""
    test_string = "Drawing Machine"
    assert len(test_string) == 15
    assert "Drawing" in test_string
    assert test_string.startswith("Drawing")