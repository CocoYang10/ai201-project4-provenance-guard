#!/usr/bin/env bash

BASE_URL="http://127.0.0.1:5000"

echo "1. Likely AI-style submission"
curl -X POST "$BASE_URL/submit" \
  -H "Content-Type: application/json" \
  -d '{"text": "Artificial intelligence represents a transformative paradigm shift in modern creative ecosystems, enabling writers to synthesize ideas, optimize narrative structures, and generate polished prose with unprecedented efficiency across diverse publishing contexts.", "creator_id": "demo-ai-style"}'

echo
echo
echo "2. Casual human-like submission"
curl -X POST "$BASE_URL/submit" \
  -H "Content-Type: application/json" \
  -d '{"text": "I wrote this after dinner and it still feels kind of lopsided. The first paragraph is too dramatic, but I like the part where the character forgets why she walked into the room.", "creator_id": "demo-human-style"}'

echo
echo
echo "3. Borderline formal submission"
curl -X POST "$BASE_URL/submit" \
  -H "Content-Type: application/json" \
  -d '{"text": "The narrator presents memory as a fragile instrument, one that records emotional truth more reliably than factual sequence. This creates a restrained but persuasive meditation on grief, responsibility, and self-invention.", "creator_id": "demo-borderline-formal"}'

echo
echo
echo "4. Recent audit log entries"
curl "$BASE_URL/log"

echo
echo
echo "5. Appeal placeholder. Replace PASTE_CONTENT_ID_HERE with a real content_id from a submit response:"
echo "curl -X POST \"$BASE_URL/appeal\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"content_id\": \"PASTE_CONTENT_ID_HERE\", \"creator_reasoning\": \"I wrote this myself and can provide earlier drafts.\"}'"

echo
