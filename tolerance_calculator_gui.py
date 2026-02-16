def compute_tolerance(method, value1, value2, method_data):
    """Calculate tolerance metrics and return a formatted result string.

    Parameters
    ----------
    method: str
        Name of the selected method.
    value1: float
        First measured value.
    value2: float
        Second measured value.
    method_data: dict
        Dictionary containing method parameters (r, R, formulas, limits, etc.).

    Returns
    -------
    str
        Human‑readable result block.
    """
    unit = method_data["unit"]
    avg = (value1 + value2) / 2
    diff = abs(value1 - value2)

    r = eval(method_data["formula_r"], {"avg": avg}) if method_data["formula_r"] else (method_data["r"] or 0)
    R = eval(method_data["formula_R"], {"avg": avg}) if method_data["formula_R"] else (method_data["R"] or 0)

    r_pass = diff <= r
    R_pass = diff <= R

    tolerance_075R = 0.75 * R
    tolerance_min = avg - tolerance_075R
    tolerance_max = avg + tolerance_075R

    result_text = (
        f"Method: {method}\n"
        f"Unit: {unit}\n"
        f"Average (X): {avg:.{method_data['Number_of_Decimals']}f} {unit}\n"
        f"Absolute Difference: {diff:.{method_data['Number_of_Decimals']}f} {unit}\n\n"
        f"Repeatability (r): {r:.{method_data['Number_of_Decimals']}f} {unit} - {'PASS' if r_pass else 'FAIL'}\n"
        f"Reproducibility (R): {R:.{method_data['Number_of_Decimals']}f} {unit} - {'PASS' if R_pass else 'FAIL'}\n\n"
        f"0.75R: {tolerance_075R:.{method_data['Number_of_Decimals']}f} {unit}\n"
        f"Tolerance Range: {tolerance_min:.{method_data['Number_of_Decimals']}f} to {tolerance_max:.{method_data['Number_of_Decimals']}f} {unit}"
    )
    return result_text
