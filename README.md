# Tyboo Studio

A visual workflow builder for AI agents and RAG (Retrieval-Augmented Generation).

## 🚀 Getting Started

Follow these steps to set up and run the project on a new machine.

### 1. Prerequisites
- **Python 3.10+**: [Download here](https://www.python.org/downloads/)
- **Node.js**: [Download here](https://nodejs.org/)
- **Git**: [Download here](https://git-scm.com/)

### 2. Backend Setup
Navigate to the root directory and set up the Python environment:

```powershell
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the **root** category with the following keys:

```env
OPENAI_API_KEY=your_openai_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
REDIS_URL=redis://localhost:6379  # optional
```

### 4. Run the Backend
Start the FastAPI server (Port 8000 is default):

```powershell
.\venv\Scripts\activate
python -m uvicorn backend.app.api.main:app --host 0.0.0.0 --port 8000
```

### 5. Frontend (Studio) Setup
Navigate to the `studio` folder:

```powershell
cd studio

# Install dependencies
npm install

# Start the frontend
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🛠 Features
- **Visual Workflow**: Drag and drop nodes to build AI agents.
- **Advanced RAG**: Intelligent document ingestion with vision-based image/table extraction.
- **Smart DB**: Direct connection to NocoDB and TybotFlow SmartDB.
- **Memory**: Integrated history management using Redis or Local storage.

## 📁 Project Structure
- `/backend`: FastAPI server and node logic.
- `/studio`: Vite + React frontend.
- `/docs`: Documentation and assets.
- `requirements.txt`: Python dependencies.
