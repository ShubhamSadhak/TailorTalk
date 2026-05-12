# Google Drive Conversational AI Agent

An AI-powered conversational assistant that helps users search, filter, and discover files inside Google Drive using natural language.

## Features

- Conversational AI search
- Smart file discovery by name, type, content, and dates
- Natural follow-up questions

## Tech Stack

- Backend: FastAPI, LangChain
- Frontend: Streamlit
- AI: Gemini
- API: Google Drive API

## Installation

### Prerequisites

- Python 3.10+ 64-bit
- Google Cloud project with Drive API enabled
- Gemini API key

If `pip install` tries to compile `numpy` from source on Windows, the dependency set is usually too old for your Python version. This repo is configured to work better with Python 3.13 by using a newer Streamlit release.

### Backend setup

```powershell
cd backend
python -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Create `backend/.env` with:

```env
GEMINI_API_KEY=your_key_here
GOOGLE_APPLICATION_CREDENTIALS=..\credentials\credentials.json
```

Run the backend:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### Frontend setup

```powershell
cd ..\frontend
python -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run the frontend:

```powershell
.\venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Using `python -m streamlit` is more reliable on Windows than calling `streamlit` directly, because it does not depend on the launcher script being on `PATH`.
