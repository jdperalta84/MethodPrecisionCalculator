import pytest

# Import functions from the GUI module
from tolerance_calculator_gui import load_methods_from_csv, validate_input

# Path to the CSV file used in the application
CSV_PATH = "methods.csv"


def test_load_methods_from_csv():
    methods = load_methods_from_csv(CSV_PATH)
    assert isinstance(methods, dict)
    # Ensure at least one method is loaded
    assert len(methods) > 0
    # Pick a known method if present
    if "Method A" in methods:
        method = methods["Method A"]
        assert "r" in method and "R" in method


def test_validate_input_within_limits():
    # Assume method limits from CSV are between 0 and 1000 for testing
    lower, upper = 0.0, 1000.0
    # Value within limits should pass without error
    try:
        validate_input(500.0, lower, upper)
    except ValueError:
        pytest.fail("validate_input raised ValueError unexpectedly for value within limits")


def test_validate_input_out_of_bounds():
    lower, upper = 0.0, 1000.0
    with pytest.raises(ValueError) as excinfo:
        validate_input(-10.0, lower, upper)
    assert "between" in str(excinfo.value).lower()

    with pytest.raises(ValueError) as excinfo:
        validate_input(2000.0, lower, upper)
    assert "between" in str(excinfo.value).lower()

