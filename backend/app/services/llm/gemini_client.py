"""
Gemini LLM integration.

Per the architecture spec: Gemini must never answer from its own
assumptions alone — it is only allowed to summarize/explain/communicate
information that RAG already retrieved from the medical knowledge base.
That contract is enforced by construction here: `generate_grounded_reply`
always takes `retrieved_context` and builds a system prompt that instructs
the model to answer *only* from that context, and to say so explicitly
when the context doesn't cover the question.

Fallback behavior: if GEMINI_API_KEY is unset, or the API call fails for
any reason (no network, quota, etc.), we fall back to a deterministic
template response built directly from the retrieved context. This keeps
the whole pipeline functional end-to-end even with zero external
dependencies — just without natural-language polish.
"""
from __future__ import annotations

from app.core.config import settings

SYSTEM_INSTRUCTION = """You are MedVision AI, an educational medical information assistant.
You can respond in the user's language (Uzbek, Russian, English, etc.).

STRICT RULES YOU MUST FOLLOW:
1. Answer ONLY using the "RETRIEVED KNOWLEDGE BASE CONTEXT" provided below. Do not invent facts.
2. If the retrieved context does not contain enough information to answer the question,
   clearly say so instead of guessing.
3. You are NOT a licensed doctor and must never claim to provide a definitive diagnosis.
   Always frame disease/condition names as "possible" or "may be associated with".
4. For anything resembling an emergency (chest pain, difficulty breathing, severe bleeding,
   stroke symptoms, suicidal ideation, etc.), tell the user to seek emergency care immediately.
5. Keep answers clear, warm, and easy for a non-medical person to understand.
6. Respond in the same language as the user's question.
7. End every substantive answer with a short reminder that this is AI-generated educational
   information and not a replacement for a licensed physician.
"""


def _build_prompt(user_message: str, retrieved_context: list[dict], conversation_history: list[dict]) -> str:
    if retrieved_context:
        context_block = "\n\n".join(
            f"[{i+1}] ({c['source_type']}: {c['title']})\n{c['snippet']}" for i, c in enumerate(retrieved_context)
        )
    else:
        context_block = "(No relevant information was found in the knowledge base for this query.)"

    history_block = ""
    if conversation_history:
        history_lines = [f"{turn['role'].upper()}: {turn['content']}" for turn in conversation_history[-6:]]
        history_block = "CONVERSATION SO FAR:\n" + "\n".join(history_lines) + "\n\n"

    return (
        f"{history_block}"
        f"RETRIEVED KNOWLEDGE BASE CONTEXT:\n{context_block}\n\n"
        f"USER QUESTION:\n{user_message}\n\n"
        "Respond following all the rules in your system instructions."
    )


def _fallback_template_reply(user_message: str, retrieved_context: list[dict]) -> str:
    """Deterministic, context-grounded answer used when Gemini is unavailable."""
    if not retrieved_context:
        return (
            "I couldn't find specific information about that in the medical knowledge base yet, "
            "so I don't want to guess. Could you describe your symptoms in a bit more detail, or "
            "ask your question a different way? And as always, this is general educational "
            "information, not a substitute for seeing a licensed doctor."
        )

    lines = [
        "Based on what's currently in the medical knowledge base, here's what may be relevant:",
        "",
    ]
    for item in retrieved_context[:3]:
        lines.append(f"• **{item['title']}** ({item['source_type']}): {item['snippet']}")
    lines.append("")
    lines.append(
        "This is general educational information generated from the knowledge base, not a "
        "personalized diagnosis. Please consult a licensed doctor for an accurate evaluation, "
        "especially if symptoms are severe or worsening."
    )
    return "\n".join(lines)


def generate_grounded_reply(
    user_message: str,
    retrieved_context: list[dict],
    conversation_history: list[dict] | None = None,
) -> tuple[str, bool]:
    """
    Returns (reply_text, used_fallback).
    used_fallback=True means Gemini was unavailable and the template fallback was used.
    """
    conversation_history = conversation_history or []

    if not settings.GEMINI_API_KEY:
        return _fallback_template_reply(user_message, retrieved_context), True

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        prompt = _build_prompt(user_message, retrieved_context, conversation_history)

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.3,
                max_output_tokens=1024,
            ),
        )
        text = (response.text or "").strip()
        if not text:
            return _fallback_template_reply(user_message, retrieved_context), True
        return text, False
    except Exception:
        # Network unavailable, invalid key, quota exceeded, etc. — degrade gracefully.
        return _fallback_template_reply(user_message, retrieved_context), True
