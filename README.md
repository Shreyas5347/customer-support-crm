# Datastraw Support CRM

A modern customer relationship management (CRM) tool tailored for support teams. Built with a React + Vite frontend and a Python FastAPI backend.

## Project Structure

```
datastraw-support-crm/
├── backend/          # FastAPI backend
│   ├── app/          # Application logic (routes, models, schemas, services)
│   ├── requirements.txt # Python dependencies
│   └── .env.example  # Example backend environment variables
├── frontend/         # React + Vite frontend
│   ├── src/          # React components and API calls
│   ├── package.json  # Node.js dependencies
│   └── .env.example  # Example frontend environment variables
├── .env.example      # Root reference for all environment variables
├── render.yaml       # Render deployment configuration
├── .gitignore        # Git ignore rules
└── README.md         # This file
```

## Getting Started

### Prerequisites
- Node.js (v18+)
- Python (v3.11+)

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the `backend` directory based on the `.env.example` and configure your keys:
   ```bash
   cp .env.example .env
   ```
5. Start the backend server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Create a `.env` file in the `frontend` directory based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
4. Start the development server:
   ```bash
   npm run dev
   ```

## Deployment

This project uses `render.yaml` to seamlessly deploy the backend as a Web Service on Render. The frontend is configured for deployment on platforms like Vercel or Render.
