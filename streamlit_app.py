import streamlit as st

# Import logic from the existing GUI module
from tolerance_calculator_gui import load_methods_from_csv, validate_input, compute_tolerance

# Load methods at startup
METHODS = load_methods_from_csv("methods.csv")

st.title("Tolerance Calculator")

# UI elements
method = st.selectbox("Method", list(METHODS.keys()))
value1 = st.number_input("Value 1", value=0.0)
value2 = st.number_input("Value 2", value=0.0)

if st.button("Calculate"):
    try:
        # Validate inputs against method limits
        validate_input(value1, METHODS[method]["Lower_Limit"], METHODS[method]["Upper_Limit"])
        validate_input(value2, METHODS[method]["Lower_Limit"], METHODS[method]["Upper_Limit"])
        # Compute and display results
        result = compute_tolerance(method, value1, value2, METHODS[method])
        st.success(result)
    except ValueError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"Unexpected error: {e}")
