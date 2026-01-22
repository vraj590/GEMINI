# RealityCheck Coach - Backend

Live camera + voice tutor using Gemini as an orchestrated 3-agent system for real-world task coaching.

## 🚀 Quick Start (Phase 1)

### 1. Prerequisites
```bash
# Python 3.10 or higher
python --version

# Virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your Gemini API key
# Get your key from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_actual_key_here
```

### 4. Run the Server
```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
python main.py
```

### 5. Test the API
```bash
# In a new terminal
curl http://localhost:8000/

# Or open in browser
open http://localhost:8000/docs  # Interactive API documentation
```

## 📁 Project Structure

```
backend/
├── main.py                 # FastAPI app with all endpoints
├── gemini_service.py       # 3-agent Gemini orchestration
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── test_api.py            # Test suite
└── README.md              # This file
```

## 🔑 API Endpoints

### 1. Start Session
```bash
POST /session/start
{
  "goal": "Wash clothes - delicates",
  "language": "english"
}
```

### 2. Push Frame (Quasi-live)
```bash
POST /session/{session_id}/frame
{
  "image_base64": "data:image/png;base64,...",
  "transcript": "optional audio transcript"
}
```

### 3. Answer Question
```bash
POST /session/{session_id}/answer
{
  "question_id": "q1",
  "answer": "cotton"
}
```

### 4. Verify Step
```bash
POST /session/{session_id}/verify
{
  "step_id": "step_1",
  "evidence_image_base64": "data:image/png;base64,..."
}
```

### 5. Get Report
```bash
GET /session/{session_id}/report
```

### 6. Resume Session
```bash
POST /session/{session_id}/resume
```

## 🧪 Testing

```bash
# Run all tests
pytest test_api.py -v

# Run specific test class
pytest test_api.py::TestSessionFlow -v

# Run with coverage
pytest test_api.py --cov=main --cov-report=html
```

## 🏗️ Architecture

### 3-Agent System

**Agent A - Perception (Gemini Flash)**
- Fast frame-to-frame understanding
- State delta detection
- Object and text recognition
- Outputs: `scene_summary`, `state_estimate`, `state_delta`

**Agent B - Coach/Planner (Gemini Pro)**
- Decides next micro-step
- Generates coaching instructions
- Asks clarifying questions
- Outputs: `next_step`, `verification_request`, `safety_warnings`

**Agent C - Verifier (Gemini Pro)**
- Evidence-based verification
- Pass/fail/unclear verdicts
- Correction instructions
- Outputs: `verdict`, `reason`, `correction`

### Data Flow
```
Frontend → Push Frame → Agent A (Perception)
                          ↓
                     Agent B (Coach)
                          ↓
                   Coach Update → Frontend
                          ↓
Frontend → Evidence → Agent C (Verifier)
                          ↓
                   Verification → Update State
```

## 🔧 Development Guide

### Adding Mock Responses (Phase 1)
The current implementation uses mock responses in `GeminiOrchestrator`. To integrate real Gemini:

1. Uncomment Gemini imports in `main.py`
2. Implement real API calls in `gemini_service.py`
3. Add error handling and retries
4. Test with `test_api.py`

### Schema Validation
All agent outputs use Pydantic models for validation:
- `PerceptionOutput`
- `CoachOutput`
- `VerifierOutput`

### Session Storage
Phase 1 uses in-memory dictionary. For production:
```python
# Phase 2: Add Redis
import redis
redis_client = redis.Redis(host='localhost', port=6379)

# Phase 3: Add PostgreSQL
from sqlalchemy import create_engine
engine = create_engine(DATABASE_URL)
```

## 📊 Frontend Integration

### CORS Configuration
Update `allow_origins` in `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
)
```

### Example Frontend Call
```javascript
// Start session
const response = await fetch('http://localhost:8000/session/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    goal: 'Wash clothes - delicates',
    language: 'english'
  })
});
const { session_id, coach_update } = await response.json();

// Push frame every 1-2 seconds
const canvas = document.createElement('canvas');
const ctx = canvas.getContext('2d');
canvas.width = video.videoWidth;
canvas.height = video.videoHeight;
ctx.drawImage(video, 0, 0);
const image_base64 = canvas.toDataURL('image/jpeg');

await fetch(`http://localhost:8000/session/${session_id}/frame`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ image_base64 })
});
```

## 🐛 Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Gemini API Status
```bash
curl -H "x-goog-api-key: YOUR_KEY" \
  https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent
```

### Common Issues

**1. Import Error: google.generativeai**
```bash
pip install google-generativeai
```

**2. Session Not Found**
- Sessions are stored in-memory
- Server restart clears all sessions
- Use persistent storage (Redis/DB) for production

**3. Invalid JSON from Gemini**
- Check `_extract_json_from_response()` in `gemini_service.py`
- Gemini may return markdown code blocks
- Implement retry logic with different prompts

## 📈 Phase 2+ Roadmap

- [ ] Redis session storage
- [ ] Rate limiting middleware
- [ ] WebSocket support for true live streaming
- [ ] Database schema for artifacts
- [ ] Multi-language support (Hindi)
- [ ] Confidence scoring for Agent outputs
- [ ] Retry logic with exponential backoff
- [ ] Monitoring and logging (Prometheus/Grafana)

## 🤝 Contributing

1. Create feature branch from `backend-orchestrator`
2. Write tests for new features
3. Update API documentation
4. Submit PR with description

## 📝 License

Gemini 3 Hackathon Project - January 2026
