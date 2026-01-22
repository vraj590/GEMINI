"""
Gemini Service - 3-Agent Orchestration System
Handles all interactions with Google's Gemini API
"""

import os
import json
import base64
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
from io import BytesIO

load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class GeminiService:
    """
    Service class for interacting with Gemini API
    Implements the 3-agent system: Perception, Coach, Verifier
    """
    
    def __init__(self):
        self.flash_model_name = os.getenv("GEMINI_FLASH_MODEL", "gemini-2.0-flash-exp")
        self.pro_model_name = os.getenv("GEMINI_PRO_MODEL", "gemini-2.0-flash-exp")
        
        # Initialize models
        self.flash_model = genai.GenerativeModel(self.flash_model_name)
        self.pro_model = genai.GenerativeModel(self.pro_model_name)
    
    def _decode_base64_image(self, base64_str: str) -> Image.Image:
        """Helper to decode base64 image string"""
        # Remove data URI prefix if present
        if "," in base64_str:
            base64_str = base64_str.split(",")[1]
        
        image_data = base64.b64decode(base64_str)
        return Image.open(BytesIO(image_data))
    
    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """Extract JSON from Gemini response, handling markdown code blocks"""
        text = response_text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON from Gemini response: {e}\nResponse: {text}")
    
    async def agent_a_perception(
        self,
        current_frame_base64: str,
        rolling_context: List[Dict[str, Any]],
        task_goal: str,
        current_step_focus: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Agent A: Perception Agent
        Fast frame-to-frame understanding and state delta detection
        Uses Gemini Flash for speed
        """
        
        # Prepare context summary from rolling buffer
        context_summary = ""
        if rolling_context:
            context_summary = "Previous observations:\n"
            for i, obs in enumerate(rolling_context[-3:]):  # Last 3 observations
                context_summary += f"{i+1}. {obs.get('scene_summary', 'N/A')}\n"
                if obs.get('state_estimate'):
                    context_summary += f"   State: {obs['state_estimate']}\n"
        
        prompt = f"""You are a perception agent analyzing video frames of a real-world task.

Task Goal: {task_goal}
Current Step Focus: {current_step_focus or "Initial observation"}

{context_summary}

Analyze the current frame and provide:
1. What objects and elements are visible (buttons, dials, LEDs, doors, etc.)
2. Current state of key objects (positions, settings, status)
3. What changed since the last observation (state delta)
4. Any text you can read (labels, settings, numbers)
5. What you're uncertain about or can't see clearly

Output ONLY valid JSON with this exact structure:
{{
    "scene_summary": "Brief description of what's visible",
    "salient_objects": ["dial", "button", "door", "etc"],
    "readable_text": "Any text visible in the frame",
    "state_estimate": {{
        "dial": "current setting",
        "door": "open/closed",
        "button_led": "on/off"
    }},
    "state_delta": {{
        "dial": "changed from X to Y",
        "door": "no change"
    }},
    "uncertainties": ["what you can't see clearly"]
}}

Be specific and factual. Only report what you can actually see."""

        try:
            # Decode and prepare image
            image = self._decode_base64_image(current_frame_base64)
            
            # Generate response with image
            response = self.flash_model.generate_content([prompt, image])
            
            # Extract JSON from response
            perception_data = self._extract_json_from_response(response.text)
            
            return perception_data
            
        except Exception as e:
            # Return safe fallback
            return {
                "scene_summary": "Error processing frame",
                "salient_objects": [],
                "readable_text": None,
                "state_estimate": {},
                "state_delta": {},
                "uncertainties": [f"Processing error: {str(e)}"]
            }
    
    async def agent_b_coach(
        self,
        task_goal: str,
        plan_state: Dict[str, Any],
        observations: List[Dict[str, Any]],
        user_answers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Agent B: Coach/Planner Agent
        Decides next steps and provides coaching
        Uses Gemini Pro for planning
        """
        
        # Prepare context
        completed_steps = plan_state.get("completed", [])
        current_steps = plan_state.get("steps", [])
        
        observations_summary = ""
        if observations:
            latest = observations[-1]
            observations_summary = f"""
Latest observation:
- Scene: {latest.get('scene_summary', 'N/A')}
- State: {latest.get('state_estimate', {})}
- Changes: {latest.get('state_delta', {})}
"""
        
        user_context = ""
        if user_answers:
            user_context = f"\nUser provided answers: {json.dumps(user_answers, indent=2)}"
        
        prompt = f"""You are a coaching agent guiding someone through: {task_goal}

Progress so far:
- Completed steps: {len(completed_steps)}
- Total steps planned: {len(current_steps)}

{observations_summary}
{user_context}

Your job is to decide the NEXT SINGLE micro-step and provide clear coaching.

Consider:
1. What should they do next to make progress?
2. Do you need to ask them any clarifying questions (max 2)?
3. Does this step require visual verification?
4. Are there any safety concerns?

Output ONLY valid JSON with this structure:
{{
    "status": "needs_input" | "in_progress" | "verify_step" | "complete",
    "next_step": {{
        "title": "Brief step name",
        "instruction": "Clear, actionable instruction"
    }},
    "why_this_step": "Brief explanation of why this step is important",
    "ask_user": ["question 1?", "question 2?"],
    "requires_verification": true/false,
    "verification_request": "What evidence to show (e.g., 'Show me the dial')",
    "safety_warnings": ["warning if applicable"],
    "fallback_options": ["option A", "option B"]
}}

Be concise, clear, and encouraging. Break complex tasks into tiny steps."""

        try:
            response = self.pro_model.generate_content(prompt)
            coach_data = self._extract_json_from_response(response.text)
            return coach_data
            
        except Exception as e:
            # Safe fallback
            return {
                "status": "needs_input",
                "next_step": {
                    "title": "Continue task",
                    "instruction": "Show me the current state of your setup"
                },
                "why_this_step": "Need to see current state to provide guidance",
                "ask_user": [],
                "requires_verification": False,
                "verification_request": None,
                "safety_warnings": [],
                "fallback_options": []
            }
    
    async def agent_c_verifier(
        self,
        step_title: str,
        step_instruction: str,
        evidence_frame_base64: str,
        latest_perception: Dict[str, Any],
        previous_failures: List[str] = None
    ) -> Dict[str, Any]:
        """
        Agent C: Verifier Agent
        Checks if step was completed correctly based on evidence
        Uses Gemini Pro for evaluation
        """
        
        failure_context = ""
        if previous_failures:
            failure_context = f"\nPrevious verification failures: {previous_failures}"
        
        prompt = f"""You are a verification agent checking if a step was completed correctly.

Step to verify:
Title: {step_title}
Instruction: {step_instruction}

Latest perception from evidence:
- Scene: {latest_perception.get('scene_summary', 'N/A')}
- State: {latest_perception.get('state_estimate', {})}
- Uncertainties: {latest_perception.get('uncertainties', [])}
{failure_context}

Your job: Determine if the step was completed correctly based on the evidence.

Output ONLY valid JSON:
{{
    "verdict": "pass" | "fail" | "unclear",
    "reason": "Specific reason for your verdict",
    "correction": "What they should do to fix it (if fail)",
    "request_new_evidence": "What angle/view to capture (if unclear)",
    "update_step_state": true/false
}}

Be specific about what you see. If unclear, ask for better evidence."""

        try:
            image = self._decode_base64_image(evidence_frame_base64)
            response = self.pro_model.generate_content([prompt, image])
            verifier_data = self._extract_json_from_response(response.text)
            return verifier_data
            
        except Exception as e:
            return {
                "verdict": "unclear",
                "reason": f"Error processing evidence: {str(e)}",
                "correction": None,
                "request_new_evidence": "Please capture a clearer image",
                "update_step_state": False
            }

# Create singleton instance
gemini_service = GeminiService()
