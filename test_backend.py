"""
Test suite for RealityCheck Coach API
Run with: pytest test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from main import app, sessions_store
import base64
from io import BytesIO
from PIL import Image

client = TestClient(app)

# Helper function to create test image
def create_test_image_base64():
    """Create a simple test image as base64"""
    img = Image.new('RGB', (100, 100), color='red')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

@pytest.fixture
def test_session():
    """Create a test session and clean up after"""
    response = client.post("/session/start", json={
        "goal": "Wash clothes - delicates",
        "language": "english"
    })
    session_id = response.json()["session_id"]
    yield session_id
    # Cleanup
    if session_id in sessions_store:
        del sessions_store[session_id]

class TestBasicEndpoints:
    """Test basic API functionality"""
    
    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "RealityCheck Coach API" in response.json()["message"]
    
    def test_start_session(self):
        response = client.post("/session/start", json={
            "goal": "Wash clothes - delicates",
            "language": "english"
        })
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "coach_update" in data
        assert data["coach_update"]["status"] in ["needs_input", "in_progress"]
    
    def test_start_session_missing_goal(self):
        response = client.post("/session/start", json={
            "language": "english"
        })
        assert response.status_code == 422  # Validation error

class TestSessionFlow:
    """Test complete session workflow"""
    
    def test_push_frame(self, test_session):
        image_base64 = create_test_image_base64()
        
        response = client.post(
            f"/session/{test_session}/frame",
            json={"image_base64": image_base64}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "coach_update" in data
        assert "perception_summary" in data
    
    def test_push_frame_without_image(self, test_session):
        response = client.post(
            f"/session/{test_session}/frame",
            json={}
        )
        assert response.status_code == 400
    
    def test_get_session_status(self, test_session):
        response = client.get(f"/session/{test_session}/status")
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "goal" in data
        assert "progress" in data
    
    def test_answer_question(self, test_session):
        response = client.post(
            f"/session/{test_session}/answer",
            json={
                "question_id": "q1",
                "answer": "cotton"
            }
        )
        assert response.status_code == 200
        assert "coach_update" in response.json()
    
    def test_get_report(self, test_session):
        response = client.get(f"/session/{test_session}/report")
        assert response.status_code == 200
        data = response.json()
        assert "artifacts" in data
        assert "checklist" in data["artifacts"]
        assert "corrections_log" in data["artifacts"]
    
    def test_resume_session(self, test_session):
        response = client.post(f"/session/{test_session}/resume")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

class TestErrorHandling:
    """Test error cases"""
    
    def test_nonexistent_session(self):
        fake_id = "nonexistent-session-id"
        response = client.get(f"/session/{fake_id}/status")
        assert response.status_code == 404
    
    def test_verify_nonexistent_step(self, test_session):
        image_base64 = create_test_image_base64()
        
        response = client.post(
            f"/session/{test_session}/verify",
            json={
                "step_id": "fake-step-id",
                "evidence_image_base64": image_base64
            }
        )
        assert response.status_code == 404

class TestDataValidation:
    """Test Pydantic model validation"""
    
    def test_session_status_enum(self):
        from main import SessionStatus
        assert "needs_input" in [s.value for s in SessionStatus]
        assert "in_progress" in [s.value for s in SessionStatus]
        assert "verify_step" in [s.value for s in SessionStatus]
        assert "complete" in [s.value for s in SessionStatus]
    
    def test_perception_output_model(self):
        from main import PerceptionOutput
        
        # Valid data
        perception = PerceptionOutput(
            scene_summary="Test scene",
            salient_objects=["dial", "button"],
            state_estimate={"dial": "Normal"},
            state_delta={"dial": "changed"}
        )
        assert perception.scene_summary == "Test scene"
        assert len(perception.salient_objects) == 2

# Integration test for full flow
@pytest.mark.asyncio
async def test_full_coaching_flow():
    """Test a complete coaching session flow"""
    
    # 1. Start session
    response = client.post("/session/start", json={
        "goal": "Wash clothes - delicates",
        "language": "english"
    })
    assert response.status_code == 200
    session_id = response.json()["session_id"]
    
    try:
        # 2. Push a few frames
        image_base64 = create_test_image_base64()
        for _ in range(3):
            response = client.post(
                f"/session/{session_id}/frame",
                json={"image_base64": image_base64}
            )
            assert response.status_code == 200
        
        # 3. Check status
        response = client.get(f"/session/{session_id}/status")
        assert response.status_code == 200
        
        # 4. Get report
        response = client.get(f"/session/{session_id}/report")
        assert response.status_code == 200
        
    finally:
        # Cleanup
        if session_id in sessions_store:
            del sessions_store[session_id]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
