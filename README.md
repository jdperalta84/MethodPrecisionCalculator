# 🧮 Method Precision Calculator

A simple and powerful web app for calculating **Repeatability (r)**, **Reproducibility (R)**, and **0.75R Tolerance Limits** based on lab test results.

Built with Python and [Streamlit](https://streamlit.io), this app makes ASTM and QC evaluations faster and easier — no spreadsheet wrangling required.

## 🌐 Live App

🔗 [Launch the Web App](https://methodprecisioncalculator.streamlit.app)

---

## 📦 Features

- 🔍 Select from pre-loaded ASTM or lab methods
- ✍️ Enter two test results
- 📊 Instantly view:
  - Average (X)
  - Absolute difference
  - r and R limits
  - Pass/fail status
  - ±0.75R tolerance range
- 💾 Save results to a `.txt` file
- 🧠 Built-in formulas for dynamic r/R calculations (when applicable)

---

## 📁 Included Files

| File                        | Description                                           |
|-----------------------------|-------------------------------------------------------|
| `tolerance_calculator_web.py` | Streamlit app code                                 |
| `methods.csv`              | CSV containing test methods, units, formulas, limits |
| `requirements.txt`         | Python dependencies for deployment                   |

---

## 🛠 Setup (Local Use)

1. Clone this repo:
   ```bash
   git clone https://github.com/jdperalta84/MethodPrecisionCalculator.git
   cd MethodPrecisionCalculator
# Phase 1 changes
