# LLM Cost Optimizer

Upload your LLM provider bill and get AI-powered cost-saving recommendations powered by Groq (Llama 3.3 70B).

## Features

- Upload OpenAI, Anthropic, or any LLM CSV bill
- Auto-detects provider from content
- Spending breakdown by model with visual bars
- AI recommendations — specific model alternatives with savings estimates
- History of previous analyses
- Drag and drop upload

## Tech Stack

- **Backend** — Python, Flask, SQLAlchemy, SQLite
- **AI** — Groq API (Llama 3.3 70B)
- **Frontend** — Vanilla JS, custom CSS

## Setup

1. Clone the repo
2. `python -m venv venv` then activate
3. `pip install -r requirements.txt`
4. Add `GROQ_API_KEY=your_key` to `.env`
5. `python app.py`
6. Open `http://localhost:5007`

## Sample Bill CSV

```csv
date,model,usage,cost
2024-01-01,gpt-4,100,2.50
2024-01-02,gpt-3.5-turbo,1000,0.75
2024-01-03,gpt-4,50,1.25
```

## Screenshots

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/1baebbad-df98-41e0-9e60-2f46343285f4" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/003de8eb-5ff0-450e-8223-1802cd9636dc" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/3fa3af4c-7ea8-4cbb-97a2-8ddb8f5c5436" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/fda11d21-dad9-4332-8f7c-04956d3ab8a2" />
