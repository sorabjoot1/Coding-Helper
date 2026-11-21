# Coding Helper

AI coding assistant for generating, explaining, debugging, and optimizing code across multiple languages.

## Features

- Generate complete runnable solutions
- Explain code in simple language
- Detect errors and suggest fixes
- Debug and optimize user-provided code
- Conversation history per session
- Multi-language support

## Setup

```powershell
cd Coding_Helper
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Set in `.env`:

```
OPENROUTER_API_KEY=sk-or-v1-your-real-key
```

## Run

```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 8003 --reload
```

Open: [http://127.0.0.1:8003](http://127.0.0.1:8003)

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/assist` | Run coding assistant |
| POST | `/api/session` | Create session |
| GET/DELETE | `/api/history/{id}` | History management |

Port default: **8003**
