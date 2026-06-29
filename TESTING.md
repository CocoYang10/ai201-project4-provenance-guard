# Testing Checklist

- Server starts with python app.py.
- POST /submit returns content_id, attribution, confidence, transparency_label, signals, and status.
- GET /log returns structured audit entries.
- POST /appeal updates status to under_review.
- Rate limiting is configured on /submit.
- README.md and planning.md are present.
- .env, .venv, **pycache**, and *.pyc are ignored.

## Manual Demo Commands

```bash
source .venv/bin/activate
python app.py
```

In a second terminal:

```bash
./demo_requests.sh
```
