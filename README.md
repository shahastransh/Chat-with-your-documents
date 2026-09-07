# Chat With Your Document (RAG Application)

A full-stack Retrieval-Augmented Generation (RAG) application that allows users to upload documents (PDF/DOCX) and ask questions about their contents in real-time. The system chunks the text, generates embeddings via serverless cloud APIs, and uses Groq's high-speed LLMs to synthesize accurate, context-aware answers.

## Features

* **Document Processing:** Natively parses and chunks PDF and DOCX files.
* **Free & Fast AI:** Leverages Groq's API for lightning-fast inference using active models like `openai/gpt-oss-120b` and `qwen/qwen3-32b`.
* **Automatic Fallback:** Gracefully cycles through a sequence of active LLMs if a specific model experiences downtime.
* **Serverless Embeddings:** Uses Hugging Face's Free Inference API (`all-MiniLM-L6-v2`) to generate embeddings in the cloud. This keeps the backend memory footprint extremely low, making it perfect for free-tier hosting on Render.
* **In-Memory Vector Search:** Utilizes ChromaDB for rapid similarity search without requiring an external database connection.

## Tech Stack

| Component | Technology | Deployment |
| :--- | :--- | :--- |
| **Frontend** | Next.js (App Router), React, Tailwind CSS | Vercel |
| **Backend** | FastAPI, Uvicorn, Python | Render (Web Service) |
| **Orchestration** | LangChain | N/A |
| **LLM Provider** | Groq API | N/A |
| **Embeddings** | Hugging Face Inference API | N/A |
| **Vector Store** | ChromaDB | N/A |

## Environment Variables

To run this project, you will need to add the following environment variables. 

**Backend (`.env` in root directory):**
* `GROQ_API_KEY` - Your free API key from Groq Console.
* `HF_TOKEN` - Your free Hugging Face Access Token (requires "Make calls to Inference Providers" permission).

**Frontend (`.env.local` in `/frontend` directory):**
* `NEXT_PUBLIC_API_URL` - The URL of your FastAPI backend (e.g., `http://127.0.0.1:8000` for local dev, or your production Render URL without a trailing slash).

## Local Development Setup

### 1. Backend Setup
Open your first terminal and run the following commands:

```bash
# Navigate to project root
cd "chat with you document"

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup
Open a second terminal and run the following commands:

```bash
# Navigate to the frontend directory
cd "chat with you document/frontend"

# Install dependencies
npm install

# Start the development server
npm run dev
```