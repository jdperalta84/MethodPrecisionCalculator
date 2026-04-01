import os
from pathlib import Path
from modules import ollama_client


PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "reviewer_prompt.md"

MOCK_OUTPUT = {
    "Root Cause Assessment": (
        "Root cause is identified as analyst error during sample preparation — "
        "specifically, incorrect reagent volume dispensed. This is credible and "
        "traceable to the batch record, but no explanation is given for why the "
        "procedure was not followed. Consider whether training or procedural clarity "
        "is the deeper issue."
    ),
    "Corrective Action Assessment": (
        "The corrective action (re-training the analyst on the SOP) is reasonable "
        "but generic. There is no mention of whether the SOP itself was reviewed for "
        "ambiguity. If the procedure is unclear, re-training alone will not prevent recurrence."
    ),
    "Evidence Review": (
        "Batch records and the out-of-specification (OOS) result are referenced. "
        "Training records are noted as attached. The OOS investigation report should "
        "also be included if one was completed — it is not mentioned here."
    ),
    "Gaps / Recommendations": (
        "1. No effectiveness check defined — add a specific verification step with a due date.\n"
        "2. SOP review not documented. Confirm whether the SOP was reviewed as part of this CAR.\n"
        "3. No mention of whether other analysts performed the same procedure during the same period."
    ),
    "Approval Comment": (
        "This CAR addresses the immediate issue but needs two additions before approval: "
        "a documented SOP review outcome and a defined effectiveness check. Return to originator "
        "to add these items. The root cause and corrective action are otherwise acceptable."
    ),
}


def load_prompt_template() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Prompt file not found: {PROMPT_PATH}")


def build_prompt(
    report_type: str,
    report_content: str,
    supporting_evidence: str,
    review_style: str,
    include_recommendations: bool,
) -> str:
    template = load_prompt_template()
    return template.format(
        report_type=report_type,
        report_content=report_content,
        supporting_evidence=supporting_evidence,
        review_style=review_style,
        include_recommendations="Yes" if include_recommendations else "No",
    )


def parse_sections(raw_text: str) -> dict:
    """
    Parse Ollama output into labeled sections.
    Expects bold headings like **Root Cause Assessment** in the response.
    Falls back to returning the full text under a single key if parsing fails.
    """
    section_keys = [
        "Root Cause Assessment",
        "Corrective Action Assessment",
        "Evidence Review",
        "Gaps / Recommendations",
        "Approval Comment",
    ]
    result = {k: "" for k in section_keys}
    current = None

    for line in raw_text.splitlines():
        stripped = line.strip().strip("*").strip()
        if stripped in section_keys:
            current = stripped
            continue
        if current:
            result[current] = (result[current] + "\n" + line).strip()

    # If nothing parsed, dump everything into first section
    if all(v == "" for v in result.values()):
        result["Root Cause Assessment"] = raw_text.strip()

    return result


def run_review(
    report_type: str,
    report_content: str,
    supporting_evidence: str,
    review_style: str,
    include_recommendations: bool,
    model: str = "llama3",
    use_mock: bool = False,
) -> tuple[dict, bool]:
    """
    Returns (sections_dict, used_mock).
    Falls back to mock output if Ollama is unavailable or use_mock is True.
    """
    if use_mock or not ollama_client.is_ollama_available():
        return MOCK_OUTPUT, True

    prompt = build_prompt(
        report_type=report_type,
        report_content=report_content,
        supporting_evidence=supporting_evidence,
        review_style=review_style,
        include_recommendations=include_recommendations,
    )
    raw = ollama_client.run_prompt(prompt, model=model)
    sections = parse_sections(raw)
    return sections, False
