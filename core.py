# Core utilities for Method Precision Calculator

"""Utility module shared between the Tkinter GUI and Streamlit web UI.

It provides:
* A dataclass representation of a **Method** (ASTM repeatability/reproducibility
  specifications).
* A robust CSV loader that gracefully handles UTF‑8 and ISO‑8859‑1 encodings.
* A safe evaluator for formulas that may reference ``avg`` and common math
  functions.
* ``calc_tolerance`` – the pure‑logic function that performs the calculation
  and returns a result dictionary.
* Logging configuration used by the UI layers.
"""

import csv
import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any

# ---------------------------------------------------------------------------
# Constants & logging
# ---------------------------------------------------------------------------
TOLERANCE_FACTOR = 0.75

logger = logging.getLogger(__name__)
if not logger.handlers:
    # Basic configuration – UI code can customise further if needed.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s – %(message)s",
    )

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class Method:
    """Represent a single ASTM method.

    Attributes correspond to the columns in ``methods.csv`` / ``methods_enriched.csv``.
    ``display_label`` is a convenience string used by the UI for the dropdown.
    """

    name: str
    r: float | None
    R: float | None
    unit: str
    formula_r: str
    formula_R: str
    decimals: int
    lower: float | None
    upper: float | None
    notes: str = ""
    year: str = ""
    matrix: str = ""
    conc_range: str = ""
    scope: str = ""
    display_label: str = ""

    def __post_init__(self) -> None:
        # Populate the display label after initialisation.
        self.display_label = f"{self.name} ({self.year})" if self.year else self.name

# ---------------------------------------------------------------------------
# CSV loader
# ---------------------------------------------------------------------------
def load_methods(csv_path: str | Path) -> Dict[str, Method]:
    """Load method specifications from a CSV file.

    The function attempts UTF‑8 first, falling back to ISO‑8859‑1. It returns a
    dictionary keyed by the raw ``Method`` name (as appears in the CSV). Any
    parsing errors are logged and re‑raised as ``IOError``.
    """

    path = Path(csv_path)
    if not path.is_file():
        raise IOError(f"CSV file not found: {path}")

    rows = []
    for enc in ("utf-8", "iso-8859-1"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                rows = list(csv.DictReader(f))
            break
        except UnicodeDecodeError:
            continue
    else:
        raise IOError(f"Unable to decode CSV {path} with supported encodings")

    methods: Dict[str, Method] = {}
    for row in rows:
        try:
            name = row["Method"].strip()
            method = Method(
                name=name,
                r=float(row["r"]) if row.get("r", "").strip() else None,
                R=float(row["R"]) if row.get("R", "").strip() else None,
                unit=row.get("Unit", "").strip(),
                formula_r=row.get("Formula_r", "").strip(),
                formula_R=row.get("Formula_R", "").strip(),
                decimals=int(row["Number_of_Decimals"]) if row.get("Number_of_Decimals", "").strip() else 4,
                lower=float(row["Lower_Limit"]) if row.get("Lower_Limit", "").strip() else None,
                upper=float(row["Upper_Limit"]) if row.get("Upper_Upper", "").strip() else None,
                notes=row.get("Notes", "").strip(),
                year=row.get("Revision_Year", "").strip(),
                matrix=row.get("Sample_Matrix", "").strip(),
                conc_range=row.get("Conc_Range", "").strip(),
                scope=row.get("Scope", "").strip(),
            )
            methods[name] = method
        except Exception as exc:
            logger.error("Failed to parse method row %s: %s", row, exc)
            continue
    return methods

# ---------------------------------------------------------------------------
# Safe formula evaluator
# ---------------------------------------------------------------------------
def safe_eval(formula: str, avg: float) -> float:
    """Evaluate a formula string safely.

    Only a whitelisted set of functions is exposed (``abs`` and a few from the
    ``math`` module). ``avg`` is injected as a variable.
    """

    allowed = {
        "avg": avg,
        "abs": abs,
        "sqrt": math.sqrt,
        "log": math.log,
        "exp": math.exp,
        "pow": pow,
    }
    try:
        compiled = compile(formula, "<formula>", "eval")
        return eval(compiled, {"__builtins__": {}}, allowed)
    except Exception as exc:
        logger.error("Formula evaluation error for %s with avg=%s: %s", formula, avg, exc)
        raise

# ---------------------------------------------------------------------------
# Core calculation
# ---------------------------------------------------------------------------
def calc_tolerance(method: Method, v1: float, v2: float) -> Dict[str, Any]:
    """Return calculation results for a pair of measurements.

    The returned dictionary contains all values needed by the UI layers:
    ``avg``, ``diff``, ``r``, ``R``, ``r_pass``, ``R_pass``, ``tolerance_075R``
    and the formatted strings for display.
    """

    # Validate limits early – UI may already have done this, but the core keeps
    # the invariant.
    if method.lower is not None and (v1 < method.lower or v2 < method.lower):
        raise ValueError(f"Values must be >= {method.lower} {method.unit}")
    if method.upper is not None and (v1 > method.upper or v2 > method.upper):
        raise ValueError(f"Values must be <= {method.upper} {method.unit}")

    avg = (v1 + v2) / 2.0
    diff = abs(v1 - v2)

    # Resolve r and R – either static values or evaluated formulas.
    if method.formula_r:
        r = safe_eval(method.formula_r, avg)
    else:
        r = method.r if method.r is not None else 0.0

    if method.formula_R:
        R = safe_eval(method.formula_R, avg)
    else:
        R = method.R if method.R is not None else 0.0

    r_pass = diff <= r
    R_pass = diff <= R
    tolerance_075R = TOLERANCE_FACTOR * R
    tolerance_pass = diff <= tolerance_075R

    result: Dict[str, Any] = {
        "method_name": method.name,
        "unit": method.unit,
        "avg": avg,
        "diff": diff,
        "r": r,
        "R": R,
        "r_pass": r_pass,
        "R_pass": R_pass,
        "tolerance_075R": tolerance_075R,
        "tolerance_pass": tolerance_pass,
        "decimals": method.decimals,
    }
    return result

# ---------------------------------------------------------------------------
# Helper for display label mapping (useful for UI dropdowns)
# ---------------------------------------------------------------------------
def build_label_map(methods: Dict[str, Method]) -> Dict[str, str]:
    """Create a ``display_label → method_name`` mapping for the UI.
    """
    return {m.display_label: m.name for m in methods.values()}

# End of core.py
