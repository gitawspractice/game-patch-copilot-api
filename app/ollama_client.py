import ollama

SYSTEM_PROMPT = """You are a helpful assistant that summarizes game patch notes.
Given raw patch text, produce a short, clear summary highlighting:
- Major balance changes
- New features / content
- Bug fixes
- Quality-of-life changes

Use bullet points and keep it concise.
NEVER output exact numbers, ranges, or stat blocks like '50/60/70/80/90' or '10 → 8'.
Describe changes in plain language (e.g. 'early game weaker, late game stronger')."""

def call_ollama(prompt: str) -> str:
    response = ollama.chat(
        model="llama3.1:8b-instruct-q8_0",  # adjust to your model from `ollama list`
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return response.message.content