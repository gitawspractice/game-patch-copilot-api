# Game Patch Copilot API

Backend for a multi-game patch notes summarizer.

## Local dev

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Test:

```bash
curl http://localhost:8000/health
```

## Deploy to Render

See notes in repo.