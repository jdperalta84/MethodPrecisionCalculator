import streamlit as st
import csv
import io
from datetime import datetime

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Method Precision Calculator",
    page_icon="🔬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─── CUSTOM CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Sora:wght@300;400;600;700&display=swap');

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Sora', sans-serif;
}

/* ── Background ── */
.stApp {
    background: #0d1117;
    color: #e6edf3;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 720px;
}

/* ── App Header ── */
.app-header {
    text-align: center;
    padding: 2rem 0 1.5rem 0;
    border-bottom: 1px solid #21262d;
    margin-bottom: 2rem;
}
.app-header h1 {
    font-family: 'Sora', sans-serif;
    font-weight: 700;
    font-size: 1.6rem;
    letter-spacing: -0.5px;
    color: #f0f6fc;
    margin: 0;
}
.app-header .subtitle {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: #6e7681;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 0.35rem;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 1px solid #21262d;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #6e7681;
    padding: 0.6rem 1.2rem;
    border-bottom: 2px solid transparent;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    color: #58a6ff !important;
    border-bottom: 2px solid #58a6ff !important;
    background: transparent !important;
}

/* ── Cards ── */
.result-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}
.result-card-header {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    color: #6e7681;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
}

/* ── Pass/Fail badges ── */
.badge {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    font-weight: 500;
    padding: 0.2rem 0.65rem;
    border-radius: 999px;
    letter-spacing: 0.08em;
}
.badge-pass {
    background: rgba(35, 134, 54, 0.25);
    color: #3fb950;
    border: 1px solid rgba(63, 185, 80, 0.35);
}
.badge-fail {
    background: rgba(218, 54, 51, 0.2);
    color: #f85149;
    border: 1px solid rgba(248, 81, 73, 0.35);
}

/* ── Metric rows ── */
.metric-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.55rem 0;
    border-bottom: 1px solid #21262d;
}
.metric-row:last-child { border-bottom: none; }
.metric-label {
    font-size: 0.82rem;
    color: #8b949e;
}
.metric-value {
    font-family: 'DM Mono', monospace;
    font-size: 0.9rem;
    color: #e6edf3;
    font-weight: 500;
}
.metric-value.accent { color: #58a6ff; }

/* ── Method note banner ── */
.method-note {
    background: rgba(88, 166, 255, 0.07);
    border-left: 3px solid #58a6ff;
    border-radius: 0 6px 6px 0;
    padding: 0.6rem 1rem;
    font-size: 0.8rem;
    color: #8b949e;
    margin-bottom: 1.2rem;
    font-style: italic;
}

/* ── Rich method info panel ── */
.method-info-panel {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 1.2rem;
}
.info-row {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    padding: 0.35rem 0;
    border-bottom: 1px solid #21262d;
    font-size: 0.8rem;
    line-height: 1.5;
}
.info-row:last-child { border-bottom: none; }
.info-icon {
    flex-shrink: 0;
    font-size: 0.85rem;
    margin-top: 0.05rem;
}
.info-text {
    color: #8b949e;
}
.info-text strong {
    color: #c9d1d9;
    font-weight: 600;
    font-family: "DM Mono", monospace;
    font-size: 0.72rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-right: 0.3rem;
}

/* ── Input labels ── */
label, .stSelectbox label, .stNumberInput label {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #6e7681 !important;
}

/* ── Selectbox & inputs ── */
.stSelectbox > div > div,
.stNumberInput > div > div > input {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.88rem !important;
}
.stSelectbox > div > div:focus-within,
.stNumberInput > div > div:focus-within {
    border-color: #58a6ff !important;
    box-shadow: 0 0 0 3px rgba(88,166,255,0.12) !important;
}

/* ── Buttons ── */
.stButton > button {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    background: #21262d !important;
    border: 1px solid #30363d !important;
    color: #8b949e !important;
    border-radius: 8px !important;
    padding: 0.55rem 1.2rem !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    background: #30363d !important;
    border-color: #58a6ff !important;
    color: #58a6ff !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    background: rgba(88, 166, 255, 0.12) !important;
    border: 1px solid rgba(88, 166, 255, 0.4) !important;
    color: #58a6ff !important;
    border-radius: 8px !important;
    width: 100% !important;
}
.stDownloadButton > button:hover {
    background: rgba(88, 166, 255, 0.2) !important;
}

/* ── History table ── */
.stDataFrame { border-radius: 8px; overflow: hidden; }

/* ── Warning / info ── */
.stAlert {
    border-radius: 8px !important;
    font-size: 0.83rem !important;
}

/* ── Section divider ── */
.section-divider {
    height: 1px;
    background: #21262d;
    margin: 1.5rem 0;
}

/* ── Thermometer result ── */
.thermo-pass {
    background: rgba(35,134,54,0.15);
    border: 1px solid rgba(63,185,80,0.3);
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    text-align: center;
}
.thermo-fail {
    background: rgba(218,54,51,0.12);
    border: 1px solid rgba(248,81,73,0.3);
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    text-align: center;
}
.thermo-big {
    font-family: 'DM Mono', monospace;
    font-size: 2rem;
    font-weight: 500;
}
.thermo-sub {
    font-size: 0.8rem;
    color: #8b949e;
    margin-top: 0.3rem;
}
</style>
""", unsafe_allow_html=True)


# ─── DATA LOADING ─────────────────────────────────────────────────────────────
@st.cache_data
def load_methods(file_path):
    methods_dict = {}
    try:
        for enc in ["utf-8", "iso-8859-1"]:
            try:
                with open(file_path, mode="r", encoding=enc) as f:
                    rows = list(csv.DictReader(f))
                break
            except UnicodeDecodeError:
                continue
        for row in rows:
            method = row["Method"].strip()
            year = row.get("Revision_Year", "").strip()
            methods_dict[method] = {
                "r": float(row["r"]) if row.get("r", "").strip() else None,
                "R": float(row["R"]) if row.get("R", "").strip() else None,
                "unit": row.get("Unit", ""),
                "formula_r": row.get("Formula_r", "").strip(),
                "formula_R": row.get("Formula_R", "").strip(),
                "decimals": int(row["Number_of_Decimals"]) if row.get("Number_of_Decimals", "").strip() else 4,
                "lower": float(row["Lower_Limit"]) if row.get("Lower_Limit", "").strip() else None,
                "upper": float(row["Upper_Limit"]) if row.get("Upper_Limit", "").strip() else None,
                "notes": row.get("Notes", "").strip(),
                "year": year,
                "matrix": row.get("Sample_Matrix", "").strip(),
                "conc_range": row.get("Conc_Range", "").strip(),
                "scope": row.get("Scope", "").strip(),
                "display_label": f"{method}  ({year})" if year else method,
            }
    except Exception as e:
        st.error(f"Error loading methods: {e}")
    return methods_dict


def group_methods(methods_dict):
    """Group methods by base standard (D56, D93, etc.)"""
    groups = {}
    for name in methods_dict:
        prefix = name.split("-")[0].strip()
        groups.setdefault(prefix, []).append(name)
    return groups


def build_label_map(methods_dict):
    """Returns {display_label: method_key} for selectbox use."""
    return {v["display_label"]: k for k, v in methods_dict.items()}


def safe_eval(formula, avg):
    """Safer formula evaluation using only math context."""
    import math
    allowed = {"avg": avg, "abs": abs, "sqrt": math.sqrt, "log": math.log, "exp": math.exp}
    return eval(compile(formula, "<string>", "eval"), {"__builtins__": {}}, allowed)


def format_result_text(method_name, unit, avg, diff, r, R, r_pass, R_pass, decimals, v1, v2):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "=" * 44,
        "  METHOD PRECISION CALCULATOR",
        f"  {ts}",
        "=" * 44,
        f"  Method  : {method_name}",
        f"  Value 1 : {v1:.{decimals}f} {unit}",
        f"  Value 2 : {v2:.{decimals}f} {unit}",
        "-" * 44,
        f"  Average : {avg:.{decimals}f} {unit}",
        f"  |Diff|  : {diff:.{decimals}f} {unit}",
        "-" * 44,
        f"  r (repeat.)  : {r:.{decimals}f}  →  {'PASS ✓' if r_pass else 'FAIL ✗'}",
        f"  R (reprod.)  : {R:.{decimals}f}  →  {'PASS ✓' if R_pass else 'FAIL ✗'}",
        f"  0.75R Range  : {avg - 0.75*R:.{decimals}f} to {avg + 0.75*R:.{decimals}f}",
        "=" * 44,
    ]
    return "\n".join(lines)


# ─── SESSION STATE ────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []

# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <h1>🔬 Method Precision Calculator</h1>
    <div class="subtitle">ASTM Repeatability & Reproducibility</div>
</div>
""", unsafe_allow_html=True)

# ─── LOAD DATA ───────────────────────────────────────────────────────────────
methods = load_methods("methods_enriched.csv")
groups = group_methods(methods)

# ─── TABS ────────────────────────────────────────────────────────────────────
tab_calc, tab_thermo, tab_history = st.tabs(["Calculator", "Thermometer Check", "History"])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — CALCULATOR
# ═══════════════════════════════════════════════════════════════════════════════
with tab_calc:

    # Method selection with group filter
    label_map = build_label_map(methods)
    all_prefixes = sorted(groups.keys())
    col_filter, col_method = st.columns([1, 2])

    with col_filter:
        base_filter = st.selectbox("Standard", ["All"] + all_prefixes, key="base_filter")

    with col_method:
        if base_filter == "All":
            label_list = [methods[k]["display_label"] for k in methods.keys()]
        else:
            label_list = [methods[k]["display_label"] for k in groups.get(base_filter, [])]
        selected_label = st.selectbox("Method / Procedure", label_list, key="sel_method")

    # Resolve label back to method key
    selected_method = label_map.get(selected_label, selected_label)

    # ── Rich method info panel ──
    if selected_method and selected_method in methods:
        mi = methods[selected_method]
        info_parts = []
        if mi.get("notes"):
            info_parts.append(f'<div class="info-row"><span class="info-icon">📋</span><span class="info-text"><strong>Notes:</strong> {mi["notes"]}</span></div>')
        if mi.get("matrix"):
            info_parts.append(f'<div class="info-row"><span class="info-icon">🧪</span><span class="info-text"><strong>Matrix:</strong> {mi["matrix"]}</span></div>')
        if mi.get("conc_range"):
            info_parts.append(f'<div class="info-row"><span class="info-icon">📊</span><span class="info-text"><strong>Concentration Range:</strong> {mi["conc_range"]}</span></div>')
        if mi.get("scope"):
            info_parts.append(f'<div class="info-row"><span class="info-icon">🔍</span><span class="info-text"><strong>Scope:</strong> {mi["scope"]}</span></div>')
        if info_parts:
            st.markdown(
                '<div class="method-info-panel">' + "".join(info_parts) + '</div>',
                unsafe_allow_html=True
            )

    # Value inputs
    col1, col2 = st.columns(2)
    m = methods[selected_method]
    decimals = m["decimals"]
    fmt = f"%.{decimals}f"
    step = 10 ** (-decimals)

    with col1:
        value1 = st.number_input("Value 1", value=0.0, step=step, format=fmt, key="v1")
    with col2:
        value2 = st.number_input("Value 2", value=0.0, step=step, format=fmt, key="v2")

    calculate = st.button("Calculate", use_container_width=True)

    if calculate:
        if value1 == 0.0 and value2 == 0.0:
            st.warning("Both values are 0.0 — please enter your measurements.")
        else:
            # Validate range
            valid = True
            if m["lower"] is not None and (value1 < m["lower"] or value2 < m["lower"]):
                st.warning(f"Values must be ≥ {m['lower']} {m['unit']}")
                valid = False
            if m["upper"] is not None and (value1 > m["upper"] or value2 > m["upper"]):
                st.warning(f"Values must be ≤ {m['upper']} {m['unit']}")
                valid = False

            if valid:
                avg = (value1 + value2) / 2
                diff = abs(value1 - value2)
                unit = m["unit"]

                try:
                    r = safe_eval(m["formula_r"], avg) if m["formula_r"] else (m["r"] or 0)
                    R = safe_eval(m["formula_R"], avg) if m["formula_R"] else (m["R"] or 0)
                except Exception as e:
                    st.error(f"Formula error: {e}")
                    st.stop()

                r_pass = diff <= r
                R_pass = diff <= R
                tolerance_075R = 0.75 * R
                tol_pass = diff <= tolerance_075R

                # ── Results Card ──
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown('<div class="result-card-header">Results</div>', unsafe_allow_html=True)

                rows_html = f"""
                <div class="metric-row">
                    <span class="metric-label">Method</span>
                    <span class="metric-value accent">{selected_method}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Average (X̄)</span>
                    <span class="metric-value">{avg:.{decimals}f} {unit}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">|Difference|</span>
                    <span class="metric-value">{diff:.{decimals}f} {unit}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Repeatability (r)</span>
                    <span class="metric-value">{r:.{decimals}f} {unit}&nbsp;&nbsp;
                        <span class="badge {'badge-pass' if r_pass else 'badge-fail'}">{'PASS' if r_pass else 'FAIL'}</span>
                    </span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Reproducibility (R)</span>
                    <span class="metric-value">{R:.{decimals}f} {unit}&nbsp;&nbsp;
                        <span class="badge {'badge-pass' if R_pass else 'badge-fail'}">{'PASS' if R_pass else 'FAIL'}</span>
                    </span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">0.75R Tolerance</span>
                    <span class="metric-value">{tolerance_075R:.{decimals}f} {unit}&nbsp;&nbsp;
                        <span class="badge {'badge-pass' if tol_pass else 'badge-fail'}">{'PASS' if tol_pass else 'FAIL'}</span>
                    </span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">0.75R Acceptable Range</span>
                    <span class="metric-value">{avg - tolerance_075R:.{decimals}f} – {avg + tolerance_075R:.{decimals}f} {unit}</span>
                </div>
                """
                st.markdown(rows_html, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # ── Formula details (collapsed) ──
                with st.expander("Calculation details"):
                    r_src = f"`{m['formula_r']}`" if m["formula_r"] else f"Static: `{m['r']}`"
                    R_src = f"`{m['formula_R']}`" if m["formula_R"] else f"Static: `{m['R']}`"
                    st.markdown(f"**r formula:** {r_src}")
                    st.markdown(f"**R formula:** {R_src}")
                    st.markdown(f"**Decimal places:** `{decimals}`")

                # ── Download ──
                result_text = format_result_text(
                    selected_method, unit, avg, diff, r, R, r_pass, R_pass, decimals, value1, value2
                )
                st.download_button(
                    label="⬇  Download Result",
                    data=result_text,
                    file_name=f"{selected_method.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

                # ── Save to session history ──
                st.session_state.history.append({
                    "Time": datetime.now().strftime("%H:%M:%S"),
                    "Method": selected_method,
                    "V1": round(value1, decimals),
                    "V2": round(value2, decimals),
                    "Avg": round(avg, decimals),
                    "|Diff|": round(diff, decimals),
                    "r": round(r, decimals),
                    "R": round(R, decimals),
                    "0.75R": round(tolerance_075R, decimals),
                    "r ✓": "✅" if r_pass else "❌",
                    "0.75R ✓": "✅" if tol_pass else "❌",
                    "R ✓": "✅" if R_pass else "❌",
                })


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — THERMOMETER CHECK
# ═══════════════════════════════════════════════════════════════════════════════
with tab_thermo:
    st.markdown("""
    <div class="method-note">
        Per ASTM 6.4.1 — Two calibrated liquid-in-glass thermometers, with corrections applied,
        shall agree within <strong>0.04 °C</strong>.
    </div>
    """, unsafe_allow_html=True)

    t_col1, t_col2 = st.columns(2)
    with t_col1:
        t1_reading = st.number_input("Thermometer 1 Reading (°C)", value=0.0, step=0.01, format="%.2f", key="t1r")
        t1_corr = st.number_input("Thermometer 1 Correction", value=0.0, step=0.01, format="%.2f", key="t1c")
    with t_col2:
        t2_reading = st.number_input("Thermometer 2 Reading (°C)", value=0.0, step=0.01, format="%.2f", key="t2r")
        t2_corr = st.number_input("Thermometer 2 Correction", value=0.0, step=0.01, format="%.2f", key="t2c")

    custom_limit = st.number_input("Agreement Limit (°C)", value=0.04, step=0.01, format="%.2f", key="tlim",
                                   help="Default 0.04 °C per ASTM 6.4.1")

    if st.button("Check Agreement", use_container_width=True, key="thermo_check"):
        t1_corrected = t1_reading + t1_corr
        t2_corrected = t2_reading + t2_corr
        delta = abs(t1_corrected - t2_corrected)
        passes = delta <= custom_limit

        css_class = "thermo-pass" if passes else "thermo-fail"
        icon = "✅" if passes else "❌"
        verdict = "AGREEMENT" if passes else "OUT OF TOLERANCE"
        color = "#3fb950" if passes else "#f85149"

        st.markdown(f"""
        <div class="{css_class}" style="margin-top:1rem;">
            <div class="thermo-big" style="color:{color};">{icon} {verdict}</div>
            <div class="thermo-sub">|ΔT| = {delta:.4f} °C &nbsp;|&nbsp; Limit = {custom_limit:.2f} °C</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="result-card" style="margin-top:1rem;">', unsafe_allow_html=True)
        details_html = f"""
        <div class="metric-row">
            <span class="metric-label">Thermo 1 corrected</span>
            <span class="metric-value">{t1_corrected:.4f} °C</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Thermo 2 corrected</span>
            <span class="metric-value">{t2_corrected:.4f} °C</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Absolute difference</span>
            <span class="metric-value">{delta:.4f} °C</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Agreement limit</span>
            <span class="metric-value">{custom_limit:.2f} °C</span>
        </div>
        """
        st.markdown(details_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Download for thermometer check too
        thermo_text = (
            f"THERMOMETER AGREEMENT CHECK\n"
            f"{datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"{'='*36}\n"
            f"Thermo 1: {t1_reading:.2f} + {t1_corr:.2f} = {t1_corrected:.4f} °C\n"
            f"Thermo 2: {t2_reading:.2f} + {t2_corr:.2f} = {t2_corrected:.4f} °C\n"
            f"|ΔT| = {delta:.4f} °C  |  Limit = {custom_limit:.2f} °C\n"
            f"Result: {'PASS' if passes else 'FAIL'}\n"
            f"{'='*36}\n"
        )
        st.download_button(
            label="⬇  Download Result",
            data=thermo_text,
            file_name=f"thermo_check_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — HISTORY
# ═══════════════════════════════════════════════════════════════════════════════
with tab_history:
    if not st.session_state.history:
        st.markdown("""
        <div style="text-align:center; color:#6e7681; padding: 3rem 0; font-family: 'DM Mono', monospace; font-size: 0.82rem;">
            No calculations yet this session.<br>Run a calculation to see history here.
        </div>
        """, unsafe_allow_html=True)
    else:
        import pandas as pd
        df = pd.DataFrame(st.session_state.history)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Export full session
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        st.download_button(
            label="⬇  Export Session as CSV",
            data=csv_buf.getvalue(),
            file_name=f"precision_session_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

        if st.button("Clear History", use_container_width=True):
            st.session_state.history = []
            st.rerun()
