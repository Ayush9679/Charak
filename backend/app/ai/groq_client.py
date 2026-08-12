import json
import httpx
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.ai.triage import triage_engine

class GroqClient:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.vision_model = settings.GROQ_VISION_MODEL
        self.base_url = "https://api.groq.com/openai/v1"

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def analyze_symptoms(self, symptoms: str, location: str = "Noida") -> Dict[str, Any]:
        """
        Analyzes symptoms using Groq or falls back to deterministic safety triage.
        Reconciles LLM output against safety triage engine.
        """
        det_res = triage_engine.deterministic_triage(symptoms)

        if not self.is_configured():
            return det_res

        prompt = f"""You are CHANAKYA AI Medical Navigation Triage Engine.
Analyze the following patient input and return ONLY a valid JSON object.
Patient symptoms/description: "{symptoms}"
Location: "{location}"

CRITICAL SAFETY & NAVIGATION DIRECTIVES:
1. You are a healthcare navigation tool, NOT a diagnostic doctor. NEVER claim a definitive diagnosis (e.g. NEVER say "You have X" or "87% chance of Y").
2. User statements like "I have X" are user-reported claims, NOT verified clinical diagnoses.
3. If user claims an unknown or unrecognized term (e.g. "dragon blood syndrome", "XYZ-9000"), set "possible_conditions" to [] and state that the term is not recognized in standard medical dictionaries.
4. Identify "possible_conditions" as educational possibilities to discuss with a clinician. Use controlled labels only: "More consistent with", "Possible", "Less consistent with", "Needs clinical evaluation". Do NOT use numerical probabilities.
5. If input is vague or non-specific (e.g. "I feel weird", "tired"), set "possible_conditions" to [] and state that more clinical information is needed.
6. Extract emergency red_flags if present.
7. HARD FIREWALL: NEVER generate, estimate, predict, or output hospital pricing, consultation fees, treatment costs, or financial ranges under any circumstances. Pricing is strictly managed by authoritative provider integrations.

Return JSON matching this exact structure:
{{
  "urgency_category": "ROUTINE" | "MODERATE" | "URGENT" | "EMERGENCY",
  "urgency_summary": "Short 1-sentence assessment summary",
  "clinical_summary": "Educational summary of findings. Emphasize that these are potential explanations for discussion with a clinician.",
  "primary_specialty": "Main medical specialty required (e.g. Cardiology, Orthopedics, Neurology, Gastroenterology, Pulmonology, General Medicine)",
  "secondary_specialties": ["Secondary specialty 1"],
  "possible_conditions": [
    {{
      "name": "Condition or symptom pattern name (e.g. Tension-type headache pattern, Musculoskeletal knee strain)",
      "relevance": "Possible",
      "explanation": "Why reported symptoms may be consistent with this pattern",
      "supporting_symptoms": ["reported symptom 1"],
      "missing_information": ["duration"],
      "confidence_label": "Possible"
    }}
  ],
  "red_flags": ["Critical warning signs detected if any"],
  "extracted_signals": ["Extracted key symptom terms"]
}}
Return ONLY raw JSON without markdown formatting.
"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a specialized medical navigation triage system that outputs JSON only."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }

        try:
            async with httpx.AsyncClient(timeout=settings.GROQ_TIMEOUT_SECONDS) as client:
                response = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    return triage_engine.reconcile_llm_response(symptoms, parsed)
                else:
                    print(f"[GROQ ERROR] Status {response.status_code}: {response.text}")
                    return det_res
        except Exception as e:
            print(f"[GROQ EXCEPTION] {e}")
            return det_res

    async def currado_chat(
        self,
        message: str,
        history: List[Dict[str, str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Currado Healthcare Assistant text response generation.
        """
        if not self.is_configured():
            return self._deterministic_currado_fallback(message, context)

        sys_content = """You are Currado 👋, CHANAKYA's interactive healthcare navigation assistant.
Your goal is to guide patients to appropriate medical specialties and nearby hospitals based on their user input.

CRITICAL MEDICAL SAFETY RULES:
1. Always respond directly to what the user wrote. Never repeat static initial greetings.
2. You are NOT a doctor. You must NEVER claim a definitive diagnosis or prescribe medication.
3. If the user mentions unknown or invented terms (e.g. "dragon blood syndrome", "XYZ disease"), clearly state that it is not recognized as a standard medical condition. Do NOT invent definitions or treatments.
4. User statements ("I have X") are user claims, NOT confirmed clinical facts.
5. If red flags or severe symptoms (e.g. severe chest pain, severe head trauma, extreme breathlessness) are mentioned, clearly advise immediate emergency care.
6. Keep answers concise, empathetic, and clear (2-4 sentences max).

Output JSON format:
{
  "response": "Currado's helpful reply text addressing the specific user message",
  "urgency": "ROUTINE" | "MODERATE" | "URGENT" | "EMERGENCY",
  "specialties": ["Specialty name"],
  "red_flags": [],
  "suggested_action": {
    "type": "NAVIGATE_SPECIALTY",
    "label": "Find General Medicine Hospitals",
    "specialty": "General Medicine",
    "route": "/hospitals?specialty=General Medicine"
  }
}
If no specific action is needed, set suggested_action to null. Output JSON ONLY."""

        if context:
            sys_content += f"\n\nActive Patient Assessment Context:\n{json.dumps(context)}"

        messages = [{"role": "system", "content": sys_content}]

        if history:
            for item in history[-10:]:
                role = "user" if item.get("sender") == "user" else "assistant"
                messages.append({"role": role, "content": item.get("message", "")})

        messages.append({"role": "user", "content": message})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "response_format": {"type": "json_object"}
        }

        try:
            async with httpx.AsyncClient(timeout=settings.GROQ_TIMEOUT_SECONDS) as client:
                response = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
                else:
                    return self._deterministic_currado_fallback(message, context)
        except Exception as e:
            print(f"[GROQ CHAT EXCEPTION] {e}")
            return self._deterministic_currado_fallback(message, context)

    async def currado_image_chat(self, message: str, image_base64: str) -> Dict[str, Any]:
        """
        Currado Vision medical report/image analysis.
        """
        if not self.is_configured():
            return {
                "response": "I've received your document/image. To enable deep AI report parsing, please configure the GROQ_API_KEY in backend/.env. In the meantime, I can guide you based on your written symptoms.",
                "urgency": "ROUTINE",
                "specialties": [],
                "red_flags": [],
                "suggested_action": None
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        prompt = f"Analyze this uploaded medical document or image. User notes: '{message}'. Extract key clinical findings relevant for hospital specialty navigation. Do NOT diagnose. Output JSON with fields 'response', 'urgency', 'specialties', 'red_flags', 'suggested_action'."

        payload = {
            "model": self.vision_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }

        try:
            async with httpx.AsyncClient(timeout=settings.GROQ_VISION_TIMEOUT_SECONDS) as client:
                response = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
                else:
                    return self._deterministic_currado_fallback(message or "Uploaded image")
        except Exception as e:
            print(f"[GROQ VISION EXCEPTION] {e}")
            return self._deterministic_currado_fallback(message or "Uploaded image")

    def _deterministic_currado_fallback(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Deterministic, safety-first Currado response fallback.
        NEVER returns the static initial greeting as a response to a user message.
        """
        lower = message.lower().strip()
        classified = triage_engine.classify_user_input(message)
        unknowns = classified["unknown_claims"]

        # 1. Check for unknown or invented disease claims (e.g. "dragon blood syndrome")
        if unknowns:
            term = unknowns[0]
            return {
                "response": f"I don't recognize '{term}' as a standard medical condition. If this is a documented diagnosis you've received, consider sharing details from your medical record or discussing it with a clinician.",
                "urgency": "ROUTINE",
                "specialties": ["General Medicine"],
                "red_flags": [],
                "suggested_action": {
                    "type": "NAVIGATE_SPECIALTY",
                    "label": "Explore General Medicine Centers",
                    "specialty": "General Medicine",
                    "route": "/hospitals?specialty=General Medicine"
                }
            }

        # 2. Check for emergency red flags
        red_flag_res = triage_engine.check_deterministic_red_flags(message)
        if red_flag_res:
            return {
                "response": "⚠️ Critical warning: Your reported symptoms contain emergency indicators (such as severe chest pain or breathlessness). Please seek immediate emergency medical care or call 102/108.",
                "urgency": "EMERGENCY",
                "specialties": ["Emergency Medicine", "Cardiology"],
                "red_flags": red_flag_res["red_flags"],
                "suggested_action": {
                    "type": "EMERGENCY_ALERT",
                    "label": "Find Emergency Hospitals Immediately",
                    "specialty": "Emergency Medicine",
                    "route": "/hospitals?emergency=true"
                }
            }

        # 3. Handle query about prior assessment results
        if any(w in lower for w in ["analysis", "assessment", "find", "results", "what did"]):
            if context and context.get("primary_specialty"):
                spec = context.get("primary_specialty", "General Medicine")
                urg = context.get("urgency_category", "ROUTINE")
                return {
                    "response": f"Based on your recent symptom intake, your primary recommended specialty is {spec} ({urg} urgency). I can help you find verified hospitals nearby with active {spec} departments.",
                    "urgency": urg,
                    "specialties": [spec],
                    "red_flags": context.get("red_flags", []),
                    "suggested_action": {
                        "type": "NAVIGATE_SPECIALTY",
                        "label": f"Find {spec} Hospitals",
                        "specialty": spec,
                        "route": f"/hospitals?specialty={spec}"
                    }
                }

        # 4. Handle Fever + Vomiting / Stomach
        if "fever" in lower and any(w in lower for w in ["vomit", "stomach", "nausea", "abdominal"]):
            return {
                "response": "Fever accompanied by vomiting or abdominal pain can indicate an acute gastrointestinal or febrile condition. Maintaining hydration is essential. A General Medicine or Gastroenterology specialist can evaluate your symptoms.",
                "urgency": "MODERATE",
                "specialties": ["General Medicine", "Gastroenterology"],
                "red_flags": [],
                "suggested_action": {
                    "type": "NAVIGATE_SPECIALTY",
                    "label": "View Gastroenterology Facilities",
                    "specialty": "Gastroenterology",
                    "route": "/hospitals?specialty=Gastroenterology"
                }
            }

        # 5. Handle Fever alone
        if "fever" in lower or "temperature" in lower:
            return {
                "response": "Fever can stem from several causes, including viral or bacterial infections. To help determine the appropriate care path, it helps to monitor how high the fever is and whether you have additional symptoms like cough, rash, or body pain.",
                "urgency": "MODERATE",
                "specialties": ["General Medicine"],
                "red_flags": [],
                "suggested_action": {
                    "type": "NAVIGATE_SPECIALTY",
                    "label": "Explore General Medicine Centers",
                    "specialty": "General Medicine",
                    "route": "/hospitals?specialty=General Medicine"
                }
            }

        # 6. Handle Stomach / Abdomen
        if any(w in lower for w in ["stomach", "abdomen", "gastric", "pain"]):
            return {
                "response": "Stomach or abdominal pain can stem from various causes. A Gastroenterology specialist can evaluate the exact location and duration. Would you like to check nearby facilities with gastroenterology departments?",
                "urgency": "MODERATE",
                "specialties": ["Gastroenterology"],
                "red_flags": [],
                "suggested_action": {
                    "type": "NAVIGATE_SPECIALTY",
                    "label": "Explore Gastroenterology Centers",
                    "specialty": "Gastroenterology",
                    "route": "/hospitals?specialty=Gastroenterology"
                }
            }

        # 7. General fallback for any other message
        return {
            "response": f"I hear your question regarding '{message}'. As your healthcare navigation assistant, I can help you identify appropriate medical specialties and locate verified nearby hospitals. Could you share more details about your symptoms?",
            "urgency": "ROUTINE",
            "specialties": ["General Medicine"],
            "red_flags": [],
            "suggested_action": {
                "type": "NAVIGATE_SPECIALTY",
                "label": "Explore Healthcare Facilities",
                "specialty": "General Medicine",
                "route": "/hospitals"
            }
        }

groq_client = GroqClient()

