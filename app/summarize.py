from typing import Dict, Any, List
import os
import json as json_lib
import httpx

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
    return f"[LLM response for prompt of length {len(prompt)}]"

def _parse_json_from_llm(text: str) -> Dict[str, Any]:
    return json_lib.loads(text)

def build_tldr_prompt(game: Dict[str, Any], text: str, custom_instructions: str | None) -> str:
    focus = ", ".join(game["focus_areas"])
    base = (
        f"You are an expert for {game['name']}. "
        f"Summarize the following patch notes into 5–8 bullet points focusing on changes that affect {focus}. "
        f"Use this guidance: {game['llm_instructions']}. "
        "Output only bullets, one per line, no extra text.\n\nPatch notes:\n"
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

    game = get_game_profile(game_id)
    if not game:
        game = get_game_profile("generic")

    tldr_prompt = build_tldr_prompt(game, text, custom_instructions)
    tldr_raw = _call_llm(tldr_prompt)
    tl_dr = [line.strip("- ").strip() for line in tldr_raw.splitlines() if line.strip()]

    cat_prompt = build_categorize_prompt(game, text)
    cat_raw = _call_llm(cat_prompt)
    categorized = _parse_json_from_llm(cat_raw)

    recheck_prompt = build_recheck_prompt(game, text)
    recheck_raw = _call_llm(recheck_prompt)
    recheck = _parse_json_from_llm(recheck_raw)
    things_to_recheck = recheck.get("things_to_recheck", [])
    meta_impact_notes = recheck.get("meta_impact_notes", [])

    score_prompt = build_impact_score_prompt(game, text)
    score_raw = _call_llm(score_prompt)
    score_data = _parse_json_from_llm(score_raw)
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