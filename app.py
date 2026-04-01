import streamlit as st
from modules.reviewer import run_review

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CAR/PAR Reviewer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar settings ──────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Settings")

    model_name = st.text_input(
        "Ollama Model",
        value="llama3",
        help="Name of the local Ollama model to use (e.g. llama3, mistral).",
    )

    review_style = st.selectbox(
        "Review Style",
        options=["Standard", "Concise", "Detailed"],
        index=0,
    )

    include_recommendations = st.toggle(
        "Include Recommendations",
        value=True,
        help="Include a Gaps / Recommendations section in the output.",
    )

    st.divider()
    st.caption(
        "If Ollama is not running locally, the app will use demo output so you "
        "can still preview the layout and workflow."
    )

# ── Main layout ───────────────────────────────────────────────────────────────
st.title("CAR / PAR Reviewer")
st.caption("QA review assistant for oil and gas laboratory corrective and preventive action reports.")

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    report_type = st.selectbox(
        "Report Type",
        options=["CAR — Corrective Action Report", "PAR — Preventive Action Report"],
        index=0,
    )

    report_content = st.text_area(
        "Report Content",
        height=280,
        placeholder=(
            "Paste the full text of the CAR or PAR here.\n\n"
            "Include: description of nonconformance, root cause, corrective/preventive actions, "
            "responsible parties, and due dates."
        ),
    )

with col_right:
    supporting_evidence = st.text_area(
        "Supporting Evidence / Notes",
        height=280,
        placeholder=(
            "Paste any supporting context here.\n\n"
            "Examples: batch record summaries, OOS investigation notes, training records, "
            "audit findings, or reviewer observations."
        ),
    )

st.divider()
run_btn = st.button("Run Review", type="primary", use_container_width=True)

# ── Review output ─────────────────────────────────────────────────────────────
if run_btn:
    if not report_content.strip():
        st.warning("Add some report content before running the review.")
        st.stop()

    short_type = report_type.split("—")[0].strip()  # "CAR" or "PAR"

    with st.spinner("Running review…"):
        sections, used_mock = run_review(
            report_type=short_type,
            report_content=report_content,
            supporting_evidence=supporting_evidence,
            review_style=review_style,
            include_recommendations=include_recommendations,
            model=model_name,
        )

    if used_mock:
        st.info(
            "Ollama is not available — showing demo output. "
            "Start Ollama locally to get a real AI-generated review.",
            icon="ℹ️",
        )

    st.subheader("Review Results")

    section_order = [
        "Root Cause Assessment",
        "Corrective Action Assessment",
        "Evidence Review",
    ]
    if include_recommendations:
        section_order.append("Gaps / Recommendations")
    section_order.append("Approval Comment")

    for section in section_order:
        text = sections.get(section, "").strip()
        if not text:
            continue
        with st.expander(f"**{section}**", expanded=True):
            st.markdown(text)
