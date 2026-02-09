import tkinter as tk
from tkinter import ttk, messagebox
import csv


# Function to load methods from CSV with encoding fallback
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
        messagebox.showerror("Error", f"Error loading methods: {e}")
    return methods_dict


# Function to validate input
def validate_input(value, lower_limit, upper_limit):
    if not lower_limit <= value <= upper_limit:
        raise ValueError(f"Value must be between {lower_limit} and {upper_limit}")


# Load methods from the CSV file
methods = load_methods_from_csv("methods.csv")


def calculate_tolerance():
    try:
        selected_method = method_combobox.get()
        if selected_method not in methods:
            raise ValueError("Please select a valid method.")

        method = methods[selected_method]
        unit = method["unit"]

        try:
            value1 = float(value1_entry.get())
            value2 = float(value2_entry.get())
        except ValueError:
            raise ValueError("Both values must be numeric.")
        validate_input(value1, method["Lower_Limit"], method["Upper_Limit"])
        validate_input(value2, method["Lower_Limit"], method["Upper_Limit"])

        avg = (value1 + value2) / 2
        diff = abs(value1 - value2)

        r = eval(method["formula_r"], {"avg": avg}) if method["formula_r"] else (method["r"] or 0)
        R = eval(method["formula_R"], {"avg": avg}) if method["formula_R"] else (method["R"] or 0)

        r_pass = diff <= r
        R_pass = diff <= R

        tolerance_075R = 0.75 * R
        tolerance_min = avg - tolerance_075R
        tolerance_max = avg + tolerance_075R

        result_text = (
            f"Method: {selected_method}\n"
            f"Unit: {unit}\n"
            f"Average (X): {avg:.{method['Number_of_Decimals']}f} {unit}\n"
            f"Absolute Difference: {diff:.{method['Number_of_Decimals']}f} {unit}\n\n"
            f"Repeatability (r): {r:.{method['Number_of_Decimals']}f} {unit} - {'PASS' if r_pass else 'FAIL'}\n"
            f"Reproducibility (R): {R:.{method['Number_of_Decimals']}f} {unit} - {'PASS' if R_pass else 'FAIL'}\n\n"
            f"0.75R: {tolerance_075R:.{method['Number_of_Decimals']}f} {unit}\n"
            f"Tolerance Range: {tolerance_min:.{method['Number_of_Decimals']}f} to {tolerance_max:.{method['Number_of_Decimals']}f} {unit}"
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
