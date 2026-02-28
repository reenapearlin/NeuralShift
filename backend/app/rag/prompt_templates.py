"""Centralized prompt templates for the Legal AI RAG module."""

from langchain.prompts import PromptTemplate


SUMMARY_PROMPT = PromptTemplate(
    input_variables=["case_text"],
    template=(
        "You are a legal drafting assistant.\n"
        "Read the provided case text and produce a concise summary in formal legal tone.\n\n"
        "Strict rules:\n"
        "1. Output only these four section headings in this exact order:\n"
        "   Facts\n"
        "   Legal Issue\n"
        "   Court Reasoning\n"
        "   Final Judgment\n"
        "2. Do NOT include prefaces, disclaimers, or assistant commentary.\n"
        "3. Do NOT mention being an AI or assistant.\n"
        "4. Do NOT add practical advice or personal opinions.\n"
        "5. Keep content factual and derived only from the case text.\n\n"
        "Case Text:\n{case_text}\n"
    ),
)
"""Purpose: Produce strict, formal summary output with required legal sections only."""


STRUCTURED_REPORT_PROMPT = PromptTemplate(
    input_variables=["case_text"],
    template=(
        "You are a legal information extraction engine.\n"
        "Extract the required fields from the case text.\n\n"
        "Output requirements:\n"
        "1. Return ONLY valid JSON.\n"
        "2. No markdown, no code fences, no explanations, no extra text.\n"
        "3. Use exactly these keys and no additional keys:\n"
        '   "case_title", "court", "legal_issue", "relevant_sections",\n'
        '   "limitation_analysis", "penalty", "judgement", "key_principles"\n'
        '4. Value types:\n'
        '   - "relevant_sections": array of strings\n'
        '   - "key_principles": array of strings\n'
        "   - all other fields: string\n"
        '5. If a field is not found, use "Not Specified".\n'
        '6. If list fields are not found, use ["Not Specified"].\n\n'
        '7. "court" must be the actual court/forum name explicitly present in the case text only.\n'
        '   Never use website/source names, URLs, or platform labels as court.\n\n'
        "Return JSON in this exact schema:\n"
        "{{\n"
        '  "case_title": "string",\n'
        '  "court": "string",\n'
        '  "legal_issue": "string",\n'
        '  "relevant_sections": ["string"],\n'
        '  "limitation_analysis": "string",\n'
        '  "penalty": "string",\n'
        '  "judgement": "string",\n'
        '  "key_principles": ["string"]\n'
        "}}\n\n"
        "Case Text:\n{case_text}\n"
    ),
)
"""Purpose: Enforce strict JSON-only structured legal report generation."""


KEYWORD_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["case_text"],
    template=(
        "You are a legal terminology extraction engine.\n"
        "Extract only valid legal terminologies from the case text.\n\n"
        "Strict output rules:\n"
        "1. Return ONLY a valid Python list of strings.\n"
        '2. Output format must be exactly like: ["Term1", "Term2", "Term3"].\n'
        "3. Maximum 12 terms.\n"
        "4. Remove duplicates.\n"
        "5. No explanation, no markdown, no extra text.\n\n"
        "Include ONLY terms that are legal in nature, such as:\n"
        "- Statutory references (e.g., Section 138 NI Act)\n"
        "- Legal doctrines\n"
        "- Offence names\n"
        "- Procedural legal terms\n"
        "- Judicial principles\n"
        "- Legal presumptions\n"
        "- Limitation period references\n"
        "- Burden of proof concepts\n"
        "- Legally enforceable debt\n"
        "- Dishonour of cheque\n\n"
        "Exclude ALL non-legal/noise content, including:\n"
        "- Page numbers\n"
        "- Dates\n"
        "- URLs and website references (e.g., Indian Kanoon, http, https, www)\n"
        "- Case numbers\n"
        "- Names of parties/persons/entities\n"
        "- Generic words (e.g., however, thus, digitally)\n"
        "- Formatting artifacts\n\n"
        "If a term is not a legal doctrine, statutory reference, or legal principle, do NOT include it.\n\n"
        "Case Text:\n{case_text}\n"
    ),
)
"""Purpose: Extract clean legal keywords only, while filtering common noise."""


__all__ = [
    "SUMMARY_PROMPT",
    "STRUCTURED_REPORT_PROMPT",
    "KEYWORD_EXTRACTION_PROMPT",
]
