import tkinter as tk
from tkinter import ttk, messagebox


# Load methods using shared core utilities
import logging
from core import load_methods, calc_tolerance, TOLERANCE_FACTOR, logger

def load_methods_from_csv(file_path: str):
    """Legacy wrapper kept for backward compatibility.
    Delegates to :func:`core.load_methods` and returns a plain ``dict`` mapping
    method name → simple dict (mirroring the original GUI expectations).
    """
    try:
        methods_obj = load_methods(file_path)
        methods_dict: dict = {}
        for name, m in methods_obj.items():
            methods_dict[name] = {
                "r": m.r,
                "R": m.R,
                "unit": m.unit,
                "formula_r": m.formula_r,
                "formula_R": m.formula_R,
                "Number_of_Decimals": m.decimals,
                "Lower_Limit": m.lower,
                "Upper_Limit": m.upper,
            }
        return methods_dict

# Simple validator used by legacy tests
def validate_input(value, lower_limit, upper_limit):
    if not lower_limit <= value <= upper_limit:
        raise ValueError(f"Value must be between {lower_limit} and {upper_limit}")
    except Exception as e:
        messagebox.showerror("Error", f"Error loading methods: {e}")
        return {}




# Load methods from the CSV file
methods = load_methods_from_csv("methods.csv")


def calculate_tolerance():
    try:
        selected_method = method_combobox.get()
        if selected_method not in methods:
            raise ValueError("Please select a valid method.")

        # Retrieve the full Method object for calculation
        method_obj = load_methods("methods.csv")[selected_method]
        # Extract numeric values from entries
        value1 = float(value1_entry.get())
        value2 = float(value2_entry.get())

        # Core calculation – will raise ValueError for out‑of‑range inputs.
        result = calc_tolerance(method_obj, value1, value2)

        # Build result display (mirrors original UI layout)
        result_text = (
            f"Method: {result['method_name']}\n"
            f"Unit: {result['unit']}\n"
            f"Average (X): {result['avg']:.{result['decimals']}f} {result['unit']}\n"
            f"Absolute Difference: {result['diff']:.{result['decimals']}f} {result['unit']}\n\n"
            f"Repeatability (r): {result['r']:.{result['decimals']}f} {result['unit']} - {'PASS' if result['r_pass'] else 'FAIL'}\n"
            f"Reproducibility (R): {result['R']:.{result['decimals']}f} {result['unit']} - {'PASS' if result['R_pass'] else 'FAIL'}\n\n"
            f"0.75R: {result['tolerance_075R']:.{result['decimals']}f} {result['unit']}\n"
            f"Tolerance Range: {result['avg'] - result['tolerance_075R']:.{result['decimals']}f} to {result['avg'] + result['tolerance_075R']:.{result['decimals']}f} {result['unit']}"
        )
        result_label.config(text=result_text)

    except ValueError as e:
        messagebox.showerror("Input Error", str(e))
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")


def save_results():
    try:
        with open("results.txt", "w") as file:
            file.write(result_label.cget("text"))
        messagebox.showinfo("Success", "Results saved to results.txt")
    except Exception as e:
        messagebox.showerror("Error", f"Could not save results: {e}")


def show_help():
    messagebox.showinfo(
        "Help",
        "1. Enter two numerical values.\n"
        "2. Select a method from the dropdown.\n"
        "3. Click Calculate to see results.\n"
        "4. Use Save Results to save output to a file."
    )


# Create the GUI
root = tk.Tk()
root.title("Tolerance Calculator")
root.geometry("450x600")
root.resizable(False, False)

# Input fields
value1_label = tk.Label(root, text="Enter Value 1:")
value1_label.pack(pady=5)
value1_entry = tk.Entry(root, font=("Arial", 12))
value1_entry.pack(pady=5)

value2_label = tk.Label(root, text="Enter Value 2:")
value2_label.pack(pady=5)
value2_entry = tk.Entry(root, font=("Arial", 12))
value2_entry.pack(pady=5)

# Method dropdown
method_label = tk.Label(root, text="Select Method:")
method_label.pack(pady=5)
method_combobox = ttk.Combobox(root, values=list(methods.keys()), font=("Arial", 12))
method_combobox.set("Select a method")
method_combobox.pack(pady=5)

# Dynamic unit label
unit_label = tk.Label(root, text="", font=("Arial", 12, "italic"))
unit_label.pack(pady=5)


def update_unit(event):
    selected_method = method_combobox.get()
    if selected_method in methods:
        unit_label.config(text=f"Unit: {methods[selected_method]['unit']}")
    else:
        unit_label.config(text="")


method_combobox.bind("<<ComboboxSelected>>", update_unit)

# Buttons
calculate_button = ttk.Button(root, text="Calculate", command=calculate_tolerance)
calculate_button.pack(pady=10)

save_button = ttk.Button(root, text="Save Results", command=save_results)
save_button.pack(pady=5)

help_button = ttk.Button(root, text="Help", command=show_help)
help_button.pack(pady=5)

# Result display
result_label = tk.Label(root, text="", justify="left", wraplength=400, font=("Arial", 12))
result_label.pack(pady=10)

pass_fail_label = tk.Label(root, text="", font=("Arial", 14, "bold"))
pass_fail_label.pack(pady=5)

# Run the GUI
root.mainloop()
