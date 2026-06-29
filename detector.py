import json
import os
import re
import string
from statistics import mean, variance

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


LIKELY_AI_LABEL = (
    "Likely AI-generated: This content shows strong automated signals of AI "
    "generation. This label is based on automated analysis and may be appealed "
    "by the creator."
)
LIKELY_HUMAN_LABEL = (
    "Likely human-written: This content shows strong signals of human authorship. "
    "Automated analysis found low evidence of AI generation."
)
UNCERTAIN_LABEL = (
    "Uncertain: The system could not confidently determine whether this content "
    "was AI-generated or human-written. This result should be interpreted with caution."
)


def _clamp_score(score):
    try:
        numeric_score = float(score)
    except (TypeError, ValueError):
        return 0.5
    return max(0.0, min(1.0, numeric_score))


def _extract_json(raw_text):
    match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in LLM response.")
    return json.loads(match.group(0))


def llm_detection_signal(text: str) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {
            "score": 0.5,
            "label": "uncertain",
            "reason": "LLM signal unavailable because GROQ_API_KEY is not configured.",
        }

    prompt = f"""
You are an AI authorship classifier for a creative writing platform.
Classify whether the submitted text appears AI-generated or human-written.

Return only valid JSON with these keys:
- score: number from 0.0 to 1.0, where 0.0 is very likely human-written and 1.0 is very likely AI-generated
- label: one of "likely_ai", "likely_human", or "uncertain"
- reason: one brief plain-language explanation

Text:
\"\"\"{text[:4000]}\"\"\"
"""

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You return compact JSON and do not include markdown.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=250,
        )
        raw_content = response.choices[0].message.content or "{}"
        parsed = _extract_json(raw_content)
        score = _clamp_score(parsed.get("score", 0.5))
        label = parsed.get("label") if parsed.get("label") in {
            "likely_ai",
            "likely_human",
            "uncertain",
        } else classify_attribution(score)

        return {
            "score": score,
            "label": label,
            "reason": parsed.get("reason", "LLM classifier returned a score."),
        }
    except Exception as exc:
        return {
            "score": 0.5,
            "label": "uncertain",
            "reason": f"LLM signal unavailable; using neutral fallback. Details: {exc}",
        }


def stylometric_signal(text: str) -> dict:
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    words = re.findall(r"\b[\w']+\b", text.lower())
    word_count = len(words)
    sentence_count = len(sentences)
    sentence_lengths = [len(re.findall(r"\b[\w']+\b", sentence)) for sentence in sentences]

    avg_sentence_length = mean(sentence_lengths) if sentence_lengths else 0
    sentence_length_variance = variance(sentence_lengths) if len(sentence_lengths) > 1 else 0
    unique_words = len(set(words))
    type_token_ratio = unique_words / word_count if word_count else 0
    punctuation_count = sum(1 for char in text if char in string.punctuation)
    punctuation_density = punctuation_count / max(len(text), 1)
    repeated_word_ratio = 1 - type_token_ratio if word_count else 0

    ai_points = 0
    reasons = []

    if word_count < 30:
        ai_points += 1
        reasons.append("short text makes authorship harder to verify")
    if 12 <= avg_sentence_length <= 25:
        ai_points += 1
        reasons.append("average sentence length is polished and medium-sized")
    if sentence_count >= 3 and sentence_length_variance < 18:
        ai_points += 2
        reasons.append("sentence lengths are unusually consistent")
    elif sentence_length_variance > 80:
        ai_points -= 1
        reasons.append("sentence lengths vary in a more human-like way")
    if word_count >= 50 and type_token_ratio < 0.48:
        ai_points += 1
        reasons.append("lexical diversity is relatively low")
    elif type_token_ratio > 0.72:
        ai_points -= 1
        reasons.append("lexical diversity is relatively high")
    if 0.015 <= punctuation_density <= 0.055:
        ai_points += 1
        reasons.append("punctuation density is tidy and consistent")
    elif punctuation_density > 0.075:
        ai_points -= 1
        reasons.append("punctuation use is more varied or informal")
    if repeated_word_ratio > 0.58:
        ai_points += 1
        reasons.append("word repetition is somewhat high")

    score = _clamp_score(0.5 + (ai_points * 0.08))
    features = {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_sentence_length": round(avg_sentence_length, 2),
        "sentence_length_variance": round(sentence_length_variance, 2),
        "type_token_ratio": round(type_token_ratio, 2),
        "punctuation_density": round(punctuation_density, 3),
        "repeated_word_ratio": round(repeated_word_ratio, 2),
    }

    if not reasons:
        reasons.append("stylometric features were mixed, so the heuristic stayed near neutral")

    return {
        "score": round(score, 2),
        "features": features,
        "reason": "; ".join(reasons),
    }


def combine_scores(llm_score: float, stylometric_score: float) -> float:
    return round((0.65 * _clamp_score(llm_score)) + (0.35 * _clamp_score(stylometric_score)), 2)


def classify_attribution(final_score: float) -> str:
    if final_score >= 0.75:
        return "likely_ai"
    if final_score <= 0.35:
        return "likely_human"
    return "uncertain"


def generate_transparency_label(attribution: str, confidence: float) -> str:
    if attribution == "likely_ai":
        return LIKELY_AI_LABEL
    if attribution == "likely_human":
        return LIKELY_HUMAN_LABEL
    return UNCERTAIN_LABEL
