# PE Intelligence

AI-powered Private Equity portfolio intelligence platform

## Features

- Real-time Portfolio Analytics
- AI-Powered Predictions
- Advanced Filtering
- Automated Enrichment
- Interactive Dashboards
- Full Test Coverage (30+ tests)

## Tech Stack

Backend: FastAPI, SQLAlchemy, JWT, pytest
Frontend: React 18, TypeScript, Vite, TailwindCSS, Vitest

## Quick Start

Installation:
  git clone https://github.com/jlemieux66/pe-intelligence.git
  cd pe-intelligence
  pipenv install --dev
  cd frontend-react && npm install && cd ..
  cp .env.example .env

Running:
  Terminal 1: pipenv run uvicorn backend.api_v2:app --reload --port 8000
  Terminal 2: cd frontend-react && npm run dev

Testing:
  pipenv run pytest -v --cov
  cd frontend-react && npm test

## OpenHands

Install: pip install openhands
Setup: openhands init && openhands connect github

## License

MIT License
