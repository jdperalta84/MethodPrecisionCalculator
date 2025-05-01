import streamlit as st
import csv

# Load methods from CSV with encoding fallback
def load_methods_from_csv(file_path):
    methods_dict = {}
    try:
        try:
            with open(file_path, mode="r", encoding="utf-8") as file:
                csv_reader = csv.DictReader(file)
                rows = list(csv_reader)
        except UnicodeDecodeError:
            with open(file_path, mode="r", encoding="iso-8859-1") as file:
                csv_reader = csv.DictReader(file)
                rows = list(csv_reader)

        for row in rows:
            method = row["Method"]
            methods_dict[method] = {
                "r": float(row["r"]) if row["r"] else None,
                "R": float(row["R"]) if row["R"] else None,
                "unit": row["Unit"],
                "formula_r": row["Formula_r"],
                "formula_R": row["Formula_R"],
                "Number_of_Decimals": int(row["Number_of_Decimals"]) if row["Number_of_Decimals"] else 4,
                "Lower_Limit": float(row["Lower_Limit"]) if row["Lower_Limit"] else 0.0,
                "Upper_Limit": float(row["Upper_Limit"]) if row["Upper_Limit"] else 10000000.0
            }
    except Exception as e:
        st.error(f"Error loading methods: {e}")
    return methods_dict


# Load methods
methods = load_methods_from_csv("methods.csv")

st.set_page_config(page_title="Tolerance Calculator", layout="wide")

st.markdown("## 🧮 Tolerance Calculator")

# Sidebar inputs
st.sidebar.header("Select Method & Input Values")
selected_method = st.sidebar.selectbox("Method", list(methods.keys()))

value1 = st.sidebar.number_input("Enter Value 1", format="%.4f", step=0.0001)
value2 = st.sidebar.number_input("Enter Value 2", format="%.4f", step=0.0001)

if selected_method and selected_method in methods:
    method = methods[selected_method]
    unit = method["unit"]

    try:
        # Validate values
        validate = lambda val: method["Lower_Limit"] <= val <= method["Upper_Limit"]
        if not validate(value1) or not validate(value2):
            st.warning(f"Values must be between {method['Lower_Limit']} and {method['Upper_Limit']} {unit}")
        else:
            avg = (value1 + value2) / 2
            diff = abs(value1 - value2)
            r = eval(method["formula_r"], {"avg": avg}) if method["formula_r"] else method["r"] or 0
            R = eval(method["formula_R"], {"avg": avg}) if method["formula_R"] else method["R"] or 0
            r_pass = diff <= r
            R_pass = diff <= R
            tolerance_075R = 0.75 * R
            tolerance_min = avg - tolerance_075R
            tolerance_max = avg + tolerance_075R
            decimals = method["Number_of_Decimals"]

            st.subheader(f"Results — {selected_method}")
            st.markdown(f"""
            - **Unit**: {unit}  
            - **Average (X)**: {avg:.{decimals}f}  
            - **Absolute Difference**: {diff:.{decimals}f}  
            - **Repeatability (r)**: {r:.{decimals}f} — {'✅ PASS' if r_pass else '❌ FAIL'}  
            - **Reproducibility (R)**: {R:.{decimals}f} — {'✅ PASS' if R_pass else '❌ FAIL'}  
            - **0.75R Tolerance Range**: {tolerance_min:.{decimals}f} to {tolerance_max:.{decimals}f}
            """)

            if st.button("💾 Save Results"):
                with open("results.txt", "w") as f:
                    f.write(f"Method: {selected_method}\n")
                    f.write(f"Average: {avg:.{decimals}f}\n")
                    f.write(f"Diff: {diff:.{decimals}f}\n")
                    f.write(f"r: {r:.{decimals}f} {'PASS' if r_pass else 'FAIL'}\n")
                    f.write(f"R: {R:.{decimals}f} {'PASS' if R_pass else 'FAIL'}\n")
                st.success("Results saved to results.txt")

            with st.expander("🧠 Show Calculation Formulas"):
                st.markdown(f"- **Formula for r**: `{method['formula_r'] or 'N/A'}`")
                st.markdown(f"- **Formula for R**: `{method['formula_R'] or 'N/A'}`")
                st.markdown(f"- **Decimals Used**: `{decimals}`")

    except Exception as e:
        st.error(f"An error occurred: {e}")
