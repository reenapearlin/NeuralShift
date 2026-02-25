"""Prompt templates used across the RAG module."""

from langchain.prompts import PromptTemplate


SUMMARY_PROMPT = PromptTemplate(
    input_variables=["case_text"],
    template=(
        "You are a legal assistant specializing in Section 138 of the "
        "Negotiable Instruments Act (India).\n\n"
        "Read the case text and produce a concise, well-structured summary "
        "with exactly these sections:\n"
        "1. Facts\n"
        "2. Legal Issue\n"
        "3. Court Reasoning\n"
        "4. Final Judgment\n\n"
        "Keep the summary factual and legally precise. Do not add assumptions.\n\n"
        "Case Text:\n{case_text}"
    ),
)


STRUCTURED_REPORT_PROMPT = PromptTemplate(
    input_variables=["case_text"],
    template=(
        "You are a legal analyst.\n"
        "Analyze the following case text and return ONLY a strict JSON object.\n"
        "Do not include markdown, code fences, explanations, or extra keys.\n\n"
        "The JSON must contain exactly these keys:\n"
        "case_title\n"
        "court\n"
        "legal_issue\n"
        "relevant_sections\n"
        "limitation_analysis\n"
        "penalty\n"
        "judgement\n"
        "key_principles\n\n"
        "Rules:\n"
        '- "relevant_sections" must be a JSON array of strings.\n'
        '- "key_principles" must be a JSON array of strings.\n'
        '- If any value is unavailable, use an empty string or empty array.\n\n'
        "Case Text:\n{case_text}"
    ),
)


KEYWORD_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["case_text"],
    template=(
        "You are a legal text analyzer.\n"
        "Extract important legal terminologies from the following case text.\n"
        "Return ONLY a valid Python list of strings.\n"
        "Do not include any explanation, markdown, or extra text.\n"
        "Include concise, non-duplicate legal terms only.\n\n"
        "Case Text:\n{case_text}"
    ),
)


__all__ = [
    "SUMMARY_PROMPT",
    "STRUCTURED_REPORT_PROMPT",
    "KEYWORD_EXTRACTION_PROMPT",
]
