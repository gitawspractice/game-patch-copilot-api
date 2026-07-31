from typing import Dict, Any, List
import os
import json as json_lib
import httpx
import re


LLM_API_URL = os.getenv("LLM_API_URL", "")


def _call_llm(prompt: str) -> str:
    if LLM_API_URL:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                LLM_API_URL,
                json={"prompt": prompt},
            )
            resp.raise_for_status()
            return resp.json().get("text", "")
    # Fallback dummy response for local dev without LLM
    return f"[LLM response for prompt of length {len(prompt)}]"


def _parse_json_from_llm(text: str, fallback: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if text is None:
        return None
    try:
        return json_lib.loads(text)
    except Exception:
        # If LLM output is not valid JSON (e.g., dummy text), use fallback
        return fallback


def build_tldr_prompt(game: Dict[str, Any], text: str, custom_instructions: str | None) -> str:
    focus = ", ".join(game["focus_areas"])
    base = (
        f"You are an expert for {game['name']}. "
        f"Summarize the following patch notes into **5–8 concise bullet points** focusing on the most impactful changes for {focus}. "
        f"Use this guidance: {game['llm_instructions']}. "
        "Rules:\n"
        "- Choose only the single most important changes for players (champion balance, key items/runes, major systems).\n"
        "- If a change is minor or only affects a niche case, skip it unless it’s one of the top ~8 changes overall.\n"
        "- Group minor bug fixes into a single bullet like 'Various bug fixes for champions and items' unless one is especially notable.\n"
        "- Describe each change in plain language (e.g. 'early game weaker, late game stronger', 'cooldown reduced slightly', 'damage increased at later ranks').\n"
        "- NEVER output exact numbers, ranges, or stat blocks like '50/60/70/80/90' or '10 → 8'.\n"
        "- Do NOT include meta commentary like 'current meta', 'more competitive', 'stronger in competitive play', or 'more frustrating to play against'.\n"
        "- Keep each bullet to one or two short sentences. Be brief and direct.\n"
        "- Output only the bullets, one per line. Do NOT add any intro sentence, headers, or extra sections.\n"
        "\nPatch notes:\n"
    )
    if custom_instructions:
        base += f"Additional instructions: {custom_instructions}\n\n"
    return base + text


def build_categorize_prompt(game: Dict[str, Any], text: str) -> str:
    return (
        "Classify each change into: buffs, nerfs, bug fixes, new content, quality-of-life. "
        "Return ONLY valid JSON in this shape: { \"buffs\": [], \"nerfs\": [], \"bug_fixes\": [], \"new_content\": [], \"qol\": [] }.\n\nPatch notes:\n"
    ) + text


def build_recheck_prompt(game: Dict[str, Any], text: str) -> str:
    focus = ", ".join(game["focus_areas"])
    return (
        f"From these patch notes, list the top things players should recheck in their builds/strategies for {game['name']}. "
        f"Include {focus}. Return ONLY valid JSON: {{ \"things_to_recheck\": [], \"meta_impact_notes\": [] }}.\n\nPatch notes:\n"
    ) + text


def build_impact_score_prompt(game: Dict[str, Any], text: str) -> str:
    return (
        f"Rate this patch's overall impact on the {game['name']} meta from 1 (minor fixes) to 5 (major meta shift). "
        "Return ONLY valid JSON: { \"score\": <int>, \"reason\": \"<string>\" }.\n\nPatch notes:\n"
    ) + text


def summarize_patch(game_id: str, text: str, custom_instructions: str | None):
    from .games import get_game_profile

    # Quick guard: if input looks like a test or not real patch notes
    if not text or len(text.strip()) < 80:
        return {
            "tl_dr": ["This doesn't look like real patch notes. Please paste the full patch text from the official source."],
            "categorized": {"buffs": [], "nerfs": [], "bug_fixes": [], "new_content": [], "qol": []},
            "things_to_recheck": [],
            "meta_impact_notes": [],
            "impact_score": 1,
            "impact_reason": "Input too short or not recognizably patch notes.",
        }

    game = get_game_profile(game_id)
    if not game:
        game = get_game_profile("generic")

    # TL;DR (free-form bullets, no JSON parsing)
    tldr_prompt = build_tldr_prompt(game, text, custom_instructions)
    tldr_raw = _call_llm(tldr_prompt)
    tl_dr = [line.strip("- ").strip() for line in tldr_raw.splitlines() if line.strip()]

    # Categorized
    cat_prompt = build_categorize_prompt(game, text)
    cat_raw = _call_llm(cat_prompt)
    categorized = _parse_json_from_llm(
        cat_raw,
        fallback={"buffs": [], "nerfs": [], "bug_fixes": [], "new_content": [], "qol": []},
    )

    # Things to recheck
    recheck_prompt = build_recheck_prompt(game, text)
    recheck_raw = _call_llm(recheck_prompt)
    recheck = _parse_json_from_llm(
        recheck_raw,
        fallback={"things_to_recheck": [], "meta_impact_notes": []},
    )
    things_to_recheck = recheck.get("things_to_recheck", [])
    meta_impact_notes = recheck.get("meta_impact_notes", [])

    # Impact score
    score_prompt = build_impact_score_prompt(game, text)
    score_raw = _call_llm(score_prompt)

    # Try to parse as JSON first
    score_data = _parse_json_from_llm(
        score_raw,
        fallback=None,
    )

    if score_data is None:
        # Fallback: extract score and reason from plain text
        score_match = re.search(r"\bscore\s*[:\-=]\s*(\d)", score_raw, re.IGNORECASE)
        reason_match = re.search(r"reason\s*[:\-=]\s*(.+?)(?:\n|$)", score_raw, re.IGNORECASE)

        score = int(score_match.group(1)) if score_match else 3
        reason = reason_match.group(1).strip() if reason_match else "Impact score based on patch changes."

        score_data = {"score": score, "reason": reason}

    impact_score = int(score_data.get("score", 3))
    impact_reason = str(score_data.get("reason", ""))

    return {
        "tl_dr": tl_dr,
        "categorized": categorized,
        "things_to_recheck": things_to_recheck,
        "meta_impact_notes": meta_impact_notes,
        "impact_score": impact_score,
        "impact_reason": impact_reason,
    }