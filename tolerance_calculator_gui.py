import tkinter as tk
from tkinter import ttk, messagebox
import csv


# Function to load methods from CSV
def load_methods_from_csv(file_path):
    methods_dict = {}
    try:
        with open(file_path, mode="r") as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                method = row["Method"]
                methods_dict[method] = {
                    "r": float(row["r"]) if row["r"] else None,
                    "R": float(row["R"]) if row["R"] else None,
                    "unit": row["Unit"],
                    "formula_r": row["Formula_r"],
                    "formula_R": row["Formula_R"]
                }
    except Exception as e:
        messagebox.showerror("Error", f"Error loading methods: {e}")
    return methods_dict


# Load methods from the CSV file
methods = load_methods_from_csv("methods.csv")


def calculate_tolerance():
    try:
        # Validate input
        value1 = float(value1_entry.get())
        value2 = float(value2_entry.get())
        selected_method = method_combobox.get()
        if selected_method not in methods:
            raise ValueError("Please select a valid method.")
        if value1 < 0 or value2 < 0:
            raise ValueError("Values must be non-negative.")

        # Fetch method details
        method = methods[selected_method]
        unit = method["unit"]
        avg = (value1 + value2) / 2
        diff = abs(value1 - value2)

        # Calculate r and R
        if method["formula_r"]:
            r = eval(method["formula_r"], {"avg": avg})
        else:
            r = method["r"]

        if method["formula_R"]:
            R = eval(method["formula_R"], {"avg": avg})
        else:
            R = method["R"]

        # Calculate 0.75R and tolerance range
        tolerance_075R = 0.75 * R
        tolerance_min = avg - tolerance_075R
        tolerance_max = avg + tolerance_075R

        # Determine Pass/Fail
        r_pass = diff <= r
        R_pass = diff <= R

        # Display results
        result_text = (
            f"Method: {selected_method}\n"
            f"Unit: {unit}\n"
            f"Average (X): {avg:.2f} {unit}\n"
            f"Absolute Difference: {diff:.2f} {unit}\n\n"
            f"Repeatability (r): {r:.2f} {unit} - {'PASS' if r_pass else 'FAIL'}\n"
            f"Reproducibility (R): {R:.2f} {unit} - {'PASS' if R_pass else 'FAIL'}\n\n"
            f"0.75R: {tolerance_075R:.2f} {unit}\n"
            f"Tolerance Range: {tolerance_min:.2f} to {tolerance_max:.2f} {unit}"
        )
        result_label.config(text=result_text)

        # Highlight Pass/Fail
        pass_fail_text = f"r: {'PASS' if r_pass else 'FAIL'}, R: {'PASS' if R_pass else 'FAIL'}"
        pass_fail_color = "green" if r_pass and R_pass else "red"
        pass_fail_label.config(text=pass_fail_text, fg=pass_fail_color)
    except ValueError as e:
        messagebox.showerror("Input Error", str(e))


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
root.geometry("450x600")  # Adjusted size for better visibility
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
method_combobox.set("Select a method")  # Default text
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
