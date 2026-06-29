# Provenance Guard Planning

## Architecture

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

Signal 1 is LLM-based classification using Groq. It asks a hosted language model to evaluate whether the writing appears AI-generated, human-written, or uncertain. This captures semantic and stylistic coherence, generic phrasing, and patterns that are hard to express with simple statistics.

Signal 2 is stylometric heuristics written in pure Python. It captures structural and statistical properties such as sentence length variance, punctuation density, lexical diversity, repeated word ratio, word count, and sentence count.

Limitations:

- LLM classification can be wrong or biased by style.
- Stylometric heuristics can misclassify formal human writing, poetry, or short texts.

## Uncertainty Representation

The system uses a 0.0-1.0 AI-likeness score. 0.0 means very likely human. 1.0 means very likely AI. Scores between 0.36 and 0.74 are labeled uncertain. High-confidence AI requires >= 0.75 because false positives are harmful on a creative writing platform.

## Transparency Label Design

Likely AI-generated: This content shows strong automated signals of AI generation. This label is based on automated analysis and may be appealed by the creator.

Likely human-written: This content shows strong signals of human authorship. Automated analysis found low evidence of AI generation.

Uncertain: The system could not confidently determine whether this content was AI-generated or human-written. This result should be interpreted with caution.

## Appeals Workflow

Creators can submit an appeal with content_id and creator_reasoning. The system updates the matching audit log entry to under_review and logs the appeal reasoning and timestamp. Automated reclassification is out of scope for this version.

## Anticipated Edge Cases

1. Formal human writing may look AI-like.
2. Lightly edited AI output may fall into uncertain.
3. Poetry or very short text may produce unreliable stylometric scores.

## AI Tool Plan

AI assistance was used to generate the Flask app skeleton, implement detection functions, draft README and planning structure, and review code for missing required features. The generated work was reviewed and adjusted for the project requirements.
