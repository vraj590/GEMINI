# RealityCheck Coach Backend Environment Variables

# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Model Selection
GEMINI_FLASH_MODEL=gemini-3.0-flash  # Agent A - Perception
GEMINI_PRO_MODEL=gemini-3.0-pro      # Agent B & C - Coach/Verifier

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:5173  # Add your frontend URLs

# Session Configuration
MAX_OBSERVATIONS_PER_SESSION=100
ROLLING_CONTEXT_SIZE=5

# Rate Limiting (Optional)
RATE_LIMIT_ENABLED=False
MAX_REQUESTS_PER_MINUTE=60

# Storage (Phase 2+)
# REDIS_URL=redis://localhost:6379
# DATABASE_URL=postgresql://user:pass@localhost/realitycheck
