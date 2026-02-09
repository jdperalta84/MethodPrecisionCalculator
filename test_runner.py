import sys
from tolerance_calculator_gui import load_methods_from_csv, validate_input

CSV_PATH = "methods.csv"

print("Running simple tests...")
# Test load_methods_from_csv
methods = load_methods_from_csv(CSV_PATH)
assert isinstance(methods, dict), "load_methods_from_csv should return dict"
assert len(methods) > 0, "No methods loaded"
print("- load_methods_from_csv passed")

# Test validate_input
lower, upper = 0.0, 1000.0
try:
    validate_input(500.0, lower, upper)
    print("- validate_input within limits passed")
except Exception as e:
    print("- validate_input within limits failed:", e)
    sys.exit(1)

try:
    validate_input(-10.0, lower, upper)
    print("- validate_input out of bounds failed to raise")
    sys.exit(1)
except ValueError:
    print("- validate_input out of bounds correctly raised ValueError")

print("All tests passed")
