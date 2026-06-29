# Provenance Guard

## Project Overview

Provenance Guard is a minimal Flask backend API for a creative writing platform. It is not a frontend app. The API classifies submitted text as likely AI-generated, likely human-written, or uncertain using two distinct detection signals, then returns a confidence score and a plain-language transparency label.

## Features

- POST /submit accepts text and creator_id
- Multi-signal detection pipeline
- Confidence scoring with uncertainty
- User-facing transparency labels
- POST /appeal
- Rate limiting
- Structured audit log
- GET /log

## Architecture Overview

Submission flow:

User submits text
-> POST /submit
-> LLM detection signal
-> Stylometric detection signal
-> Combined confidence score
-> Transparency label
-> Audit log
-> JSON response

Appeal flow:

Creator submits appeal
-> POST /appeal
-> Lookup content_id
-> Save creator reasoning
-> Update status to under_review
-> Audit log updated
-> Confirmation response

## Detection Signals

Signal 1 is an LLM-based classifier using the Groq API and the llama-3.3-70b-versatile model. It reviews the submitted writing and returns a structured AI-likeness score, label, and reason.

Signal 2 is a pure Python stylometric heuristic. It uses word count, sentence count, average sentence length, sentence length variance, type-token ratio, punctuation density, and repeated word ratio. This is distinct from the LLM signal because it relies only on measurable text statistics.

POST /submit runs both signals for every valid submission.

## Confidence Scoring

The final score is a weighted average:

```text
final_score = 0.65 * llm_score + 0.35 * stylometric_score
```

Thresholds:

- >= 0.75 = likely_ai
- <= 0.35 = likely_human
- otherwise = uncertain

The high-confidence AI threshold is intentionally high because false positives are harmful on a creative writing platform.

## Transparency Labels

Likely AI-generated: This content shows strong automated signals of AI generation. This label is based on automated analysis and may be appealed by the creator.

Likely human-written: This content shows strong signals of human authorship. Automated analysis found low evidence of AI generation.

Uncertain: The system could not confidently determine whether this content was AI-generated or human-written. This result should be interpreted with caution.

## Appeals Workflow

Creators can call POST /appeal with a content_id and creator_reasoning. The system finds the matching audit log entry, updates its status to under_review, adds the appeal reasoning, and records an appeal timestamp. Automated reclassification or human review assignment is not included in this MVP.

## Rate Limiting

POST /submit is limited to 10 submissions per minute and 100 per day.

I chose 10 submissions per minute and 100 per day because this allows normal creators to test drafts while preventing spam or automated abuse.

## Audit Log

Every classification decision is written to audit_log.json locally. GET /log shows recent audit log entries for grading and demo visibility.

audit_log.json is generated locally when the app runs and is ignored by git. The grader can generate it by running the provided curl examples or demo_requests.sh. Example entry:

```json
{
  "attribution": "uncertain",
  "confidence": 0.45,
  "content_id": "fd1ed31b-657a-4703-942c-0df8056da4c0",
  "creator_id": "demo-borderline",
  "llm_label": "uncertain",
  "llm_reason": "text has a formal tone and complex sentence structure, but lacks overly repetitive or formulaic language patterns typical of AI generation",
  "llm_score": 0.42,
  "status": "classified",
  "stylometric_features": {
    "avg_sentence_length": 20,
    "punctuation_density": 0.017,
    "repeated_word_ratio": 0.1,
    "sentence_count": 2,
    "sentence_length_variance": 98,
    "type_token_ratio": 0.9,
    "word_count": 40
  },
  "stylometric_reason": "average sentence length is polished and medium-sized; sentence lengths vary in a more human-like way; lexical diversity is relatively high; punctuation density is tidy and consistent",
  "stylometric_score": 0.5,
  "text_preview": "The relationship between monetary policy and asset prices is complicated because central banks influence borrowing costs, but investors also react to expectatio",
  "timestamp": "2026-06-29T20:41:16.926242+00:00",
  "transparency_label": "Uncertain: The system could not confidently determine whether this content was AI-generated or human-written. This result should be interpreted with caution."
}
```

Appealed entries keep the original classification fields and add appeal data:

```json
{
  "appeal_reasoning": "I wrote this myself and can provide earlier drafts.",
  "appeal_timestamp": "2026-06-29T20:44:08.988037+00:00",
  "content_id": "fb941f3f-5e7c-4a86-96c5-41d68ea1df05",
  "creator_id": "demo-human",
  "attribution": "likely_human",
  "confidence": 0.27,
  "status": "under_review"
}
```

## Example Requests

POST /submit:

```bash
curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "Artificial intelligence represents a transformative paradigm shift in modern society, reshaping how individuals communicate, create, and solve complex problems across industries.", "creator_id": "test-user-1"}'
```

GET /log:

```bash
curl http://127.0.0.1:5000/log
```

POST /appeal:

```bash
curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "PASTE_CONTENT_ID_HERE", "creator_reasoning": "I wrote this myself and can provide earlier drafts."}'
```

## Example Test Results

Actual demo output from the likely AI-style submission:

```json
{
  "attribution": "likely_ai",
  "confidence": 0.78,
  "transparency_label": "Likely AI-generated: This content shows strong automated signals of AI generation. This label is based on automated analysis and may be appealed by the creator.",
  "signals": {
    "llm_score": 0.8,
    "stylometric_score": 0.74
  },
  "status": "classified"
}
```

Actual demo output from the casual human-like submission:

```json
{
  "attribution": "likely_human",
  "confidence": 0.27,
  "transparency_label": "Likely human-written: This content shows strong signals of human authorship. Automated analysis found low evidence of AI generation.",
  "signals": {
    "llm_score": 0.1,
    "stylometric_score": 0.58
  },
  "status": "classified"
}
```

Actual demo output from the borderline formal submission:

```json
{
  "attribution": "uncertain",
  "confidence": 0.45,
  "transparency_label": "Uncertain: The system could not confidently determine whether this content was AI-generated or human-written. This result should be interpreted with caution.",
  "signals": {
    "llm_score": 0.42,
    "stylometric_score": 0.5
  },
  "status": "classified"
}
```

Actual attribution and confidence scores can vary because they depend on the Groq model response and the text being submitted. If GROQ_API_KEY is not configured or the API is unavailable, the LLM signal falls back to 0.5 so the app remains demoable.

## Known Limitations

- AI detection is not perfect.
- Formal human writing may be mislabeled.
- Short texts are harder to classify.
- Stylometric heuristics are simple and not production-grade.
- The appeal system stores the appeal but does not perform human review automatically.

## Spec Reflection

The planning spec helped guide implementation by making the required routes, scoring formula, labels, and audit fields explicit before coding.

The implementation diverged from a more complex production plan by using a JSON file instead of a database. This keeps the project grading-ready and easy to run locally.

## AI Usage

AI helped generate the Flask endpoint skeleton and connect the submit, log, and appeal routes.

AI helped design the scoring thresholds and README wording. I reviewed and edited the generated code to match the assignment requirements.

## Walkthrough Video

A short walkthrough video showing the backend API, `/submit`, `/log`, and `/appeal` workflow is available here:

[Watch the walkthrough video](https://drive.google.com/file/d/1WnKVaJBoaLH34fZWOMBkM3f2xoyn06M3/view?usp=sharing)
