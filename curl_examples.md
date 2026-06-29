# Curl Examples

## Step 1: Start the Server

In the first terminal:

```bash
source .venv/bin/activate
python app.py
```

## Step 2: Submit Writing

In a second terminal, call POST /submit:

```bash
curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "Artificial intelligence represents a transformative paradigm shift in modern society, reshaping how individuals communicate, create, and solve complex problems across industries.", "creator_id": "test-user-1"}'
```

## Step 3: View the Audit Log

Call GET /log:

```bash
curl http://127.0.0.1:5000/log
```

## Step 4: Copy a content_id

Copy a real content_id from the POST /submit response or from the GET /log response.

## Step 5: Submit an Appeal

Replace PASTE_CONTENT_ID_HERE with the real content_id:

```bash
curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "PASTE_CONTENT_ID_HERE", "creator_reasoning": "I wrote this myself and can provide earlier drafts."}'
```

## Step 6: Confirm Appeal Status

Call GET /log again and confirm the appealed entry has status under_review:

```bash
curl http://127.0.0.1:5000/log
```
