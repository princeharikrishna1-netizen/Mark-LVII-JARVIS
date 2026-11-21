import asyncio

TOOL = {
    "name": "ai_council_deliberate",
    "description": "Evaluates a complex question or decision using 3 independent personas: Researcher, Analyst, and Security AI, then synthesizes a combined verdict.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query": {"type": "STRING", "description": "The problem, architecture choice, or question to deliberate on"}
        },
        "required": ["query"]
    }
}

def run(params: dict = None, **kwargs) -> str:
    query = str((params or {}).get("query", "")).strip()
    if not query:
        return "AI Council: Please provide a topic or question to deliberate."
    try:
        from core import gemini
        prompt = (
            f"You are the JARVIS AI Council. Deliberate on this query from 3 distinct experts, then give a unified final verdict:\n"
            f"Query: {query}\n\n"
            "1. [RESEARCHER]: Facts, best practices, and technical feasibility.\n"
            "2. [ANALYST]: Performance trade-offs, cost/time efficiency, and edge cases.\n"
            "3. [SECURITY AI]: Risks, data privacy, and failure modes.\n"
            "4. [COMBINED COUNCIL VERDICT]: Actionable 2-sentence recommendation for Hari."
        )
        return gemini.text(prompt, gemini.SMART, None, 25_000) or "AI Council deliberation unavailable."
    except Exception as e:
        return f"AI Council error: {e}"

PLUGIN = TOOL

