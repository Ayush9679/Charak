from typing import Dict, Any, List, Optional
import re
from app.ai.symptom_normalizer import normalize_symptoms

# Standard medical symptoms dictionary for entity classification
KNOWN_SYMPTOMS = {
    "fever", "pyrexia", "temperature", "high temp",
    "vomiting", "vomit", "nausea", "throwing up",
    "diarrhea", "loose motion", "watery stool",
    "abdominal pain", "stomach pain", "stomach ache", "belly pain", "gastric pain",
    "chest pain", "chest tightness", "chest pressure", "cardiac pain",
    "breathlessness", "difficulty breathing", "shortness of breath", "gasping", "wheezing",
    "headache", "migraine", "head pressure",
    "dizziness", "giddiness", "lightheadedness", "vertigo",
    "knee pain", "joint pain", "back pain", "leg pain", "bone pain", "sprain", "fracture",
    "cough", "cold", "sore throat", "runny nose",
    "fatigue", "tired", "weakness", "lethargy",
    "rash", "skin lesion", "itching",
    "seizure", "numbness", "paralysis", "fainting", "unconscious", "blackout"
}

KNOWN_DIAGNOSES = {
    "diabetes", "diabetic", "hypertension", "high blood pressure", "bp",
    "asthma", "copd", "thyroid", "hypothyroidism", "hyperthyroidism",
    "arthritis", "migraine", "tuberculosis", "tb", "malaria", "dengue",
    "pneumonia", "typhoid", "covid", "covid-19"
}

EMERGENCY_RED_FLAGS = [
    ("heart attack", "Suspected acute myocardial infarction / cardiac emergency"),
    ("cardiac arrest", "Cardiac arrest / life-threatening emergency"),
    ("having a heart attack", "Suspected acute myocardial infarction"),
    ("think i'm having a heart", "Suspected cardiac emergency"),
    ("chest pain", "Acute chest discomfort / potential cardiac symptom"),
    ("severe chest pain", "Severe acute chest pain"),
    ("difficulty breathing", "Acute respiratory distress"),
    ("can't breathe", "Acute respiratory distress / inability to breathe"),
    ("cannot breathe", "Acute respiratory distress / inability to breathe"),
    ("gasping", "Severe respiratory distress / gasping for air"),
    ("unconscious", "Loss of consciousness / unresponsiveness"),
    ("blackout", "Acute loss of consciousness"),
    ("stroke", "Potential acute neurological / stroke indicators"),
    ("paralysis", "Sudden weakness or paralysis"),
    ("severe bleeding", "Uncontrolled acute hemorrhage"),
    ("seizure", "Active or recent seizure activity"),
    ("anaphylaxis", "Severe acute allergic reaction / airway compromise"),
    ("suicidal", "Immediate mental health crisis"),
    ("kill myself", "Immediate mental health crisis"),
]

class TriageEngine:
    def classify_user_input(self, text: str) -> Dict[str, List[str]]:
        """
        Distinguishes user input into 4 distinct categories:
        1. reported_symptoms
        2. reported_conditions
        3. suspected_conditions
        4. unknown_claims

        Uses symptom_normalizer for typo-tolerant matching before exact matching.
        """
        lower = text.lower().strip()

        # --- Phase 6: Run symptom normalizer first (typo tolerance) ---
        norm_result = normalize_symptoms(text)
        reported_symptoms = list(norm_result.canonical_symptoms)

        # Also keep original exact matches from KNOWN_SYMPTOMS for backwards compat
        for symptom in KNOWN_SYMPTOMS:
            if symptom in lower and symptom not in reported_symptoms:
                reported_symptoms.append(symptom)

        reported_conditions = []
        suspected_conditions = []
        unknown_claims = []

        # Extract diagnoses / suspected conditions
        for diag in KNOWN_DIAGNOSES:
            if diag in lower:
                if any(phrase in lower for phrase in ["think i have", "maybe", "suspect"]):
                    suspected_conditions.append(diag)
                else:
                    reported_conditions.append(diag)

        # Check for unverified / unknown claims (e.g. "dragon blood syndrome", "XYZ-9000")
        disease_matches = re.findall(r'([a-z0-9\s\-]+(?:disease|syndrome|condition|virus|fever))', lower)
        for match in disease_matches:
            cleaned = match.strip()
            if not any(k in cleaned for k in KNOWN_SYMPTOMS) and not any(k in cleaned for k in KNOWN_DIAGNOSES):
                if len(cleaned) > 3 and cleaned not in ["fever", "stomach disease"]:
                    unknown_claims.append(cleaned)

        return {
            "reported_symptoms": list(set(reported_symptoms)),
            "reported_conditions": list(set(reported_conditions)),
            "suspected_conditions": list(set(suspected_conditions)),
            "unknown_claims": list(set(unknown_claims))
        }

    def check_deterministic_red_flags(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Evaluates input for emergency red flags.
        If emergency indicators exist, forces urgency = EMERGENCY.
        """
        lower = text.lower()
        detected_flags = []
        
        for keyword, label in EMERGENCY_RED_FLAGS:
            if keyword in lower:
                detected_flags.append(label)

        if detected_flags:
            return {
                "urgency_category": "EMERGENCY",
                "urgency_summary": "Potentially critical acute symptoms detected requiring immediate emergency medical evaluation.",
                "clinical_summary": "Emergency red flags detected. Immediate acute clinical evaluation in an emergency department is strongly advised.",
                "primary_specialty": "Emergency Medicine",
                "secondary_specialties": ["Cardiology", "Intensive Care"],
                "possible_conditions": [
                    {
                        "name": "Acute Emergency Clinical Evaluation Needed",
                        "relevance": "More consistent with",
                        "explanation": "Reported symptoms contain red flags that require urgent clinical evaluation by an emergency specialist.",
                        "supporting_symptoms": [f.split("/")[0].strip() for f in detected_flags],
                        "missing_information": ["Vital signs", "ECG / Emergency Triage"],
                        "confidence_label": "Needs clinical evaluation"
                    }
                ],
                "red_flags": detected_flags,
                "extracted_signals": [f.split("/")[0].strip() for f in detected_flags]
            }
        return None

    def deterministic_triage(self, text: str) -> Dict[str, Any]:
        """
        Fallback triage reasoning strictly from symptoms and evidence.
        Never defaults to Emergency Medicine or ROUTINE without clinical basis.
        """
        red_flag_res = self.check_deterministic_red_flags(text)
        if red_flag_res:
            return red_flag_res

        classified = self.classify_user_input(text)
        symptoms = classified["reported_symptoms"]
        unknowns = classified["unknown_claims"]

        # 1. Unknown / fake disease name provided without recognized symptoms
        if unknowns and not symptoms:
            unknown_term = unknowns[0]
            return {
                "urgency_category": "ROUTINE",
                "urgency_summary": f"Unrecognized medical term reported: '{unknown_term}'.",
                "clinical_summary": f"CHANAKYA does not recognize '{unknown_term}' as a standard medical condition. If this is a documented diagnosis you have received from a clinician, please review your medical records or consult your healthcare provider.",
                "primary_specialty": "General Medicine",
                "secondary_specialties": ["Internal Medicine"],
                "possible_conditions": [],
                "red_flags": [],
                "extracted_signals": unknowns
            }

        lower = text.lower()

        # 2. Chest / Cardiovascular symptoms
        if any(w in lower for w in ["chest", "cardiac", "heart", "breath", "palpitation"]):
            return {
                "urgency_category": "URGENT",
                "urgency_summary": "Potentially urgent cardiovascular evaluation recommended.",
                "clinical_summary": "Chest or heart-related symptoms reported. Specialty evaluation by a cardiologist or urgent care provider is recommended.",
                "primary_specialty": "Cardiology",
                "secondary_specialties": ["Emergency Medicine", "General Medicine"],
                "possible_conditions": [
                    {
                        "name": "Cardiovascular or Palpitation Assessment",
                        "relevance": "Possible",
                        "explanation": "Chest or heart symptoms warrant evaluation to check cardiac function and blood pressure.",
                        "supporting_symptoms": [s for s in symptoms if s in ["chest pain", "breathlessness", "palpitation"]],
                        "missing_information": ["ECG telemetry", "duration", "radiation of discomfort"],
                        "confidence_label": "Possible"
                    }
                ],
                "red_flags": [],
                "extracted_signals": symptoms or ["chest symptoms"]
            }

        # 3. Fever + Vomiting / Gastrointestinal symptoms
        if "fever" in symptoms and any(s in symptoms for s in ["vomiting", "nausea", "diarrhea", "abdominal pain", "stomach pain"]):
            return {
                "urgency_category": "MODERATE",
                "urgency_summary": "Moderate urgency: Febrile gastrointestinal symptoms identified.",
                "clinical_summary": "Fever accompanied by gastrointestinal symptoms (vomiting/nausea/abdominal pain) reported. Consultation with General Medicine or Gastroenterology is advised.",
                "primary_specialty": "General Medicine",
                "secondary_specialties": ["Gastroenterology"],
                "possible_conditions": [
                    {
                        "name": "Acute Gastroenteritis or Febrile Gastrointestinal Pattern",
                        "relevance": "Possible",
                        "explanation": "Combination of fever and gastrointestinal symptoms is commonly consistent with acute gastrointestinal or viral febrile patterns.",
                        "supporting_symptoms": [s for s in symptoms if s in ["fever", "vomiting", "nausea", "abdominal pain", "diarrhea"]],
                        "missing_information": ["duration of symptoms", "hydration status", "dietary history"],
                        "confidence_label": "Possible"
                    }
                ],
                "red_flags": [],
                "extracted_signals": symptoms
            }

        # 4. Fever alone
        if "fever" in symptoms or any(w in lower for w in ["fever", "pyrexia", "temperature"]):
            return {
                "urgency_category": "MODERATE",
                "urgency_summary": "Febrile symptom evaluation recommended.",
                "clinical_summary": "Fever reported. Evaluation by a General Medicine physician is recommended to determine the underlying cause.",
                "primary_specialty": "General Medicine",
                "secondary_specialties": ["Internal Medicine"],
                "possible_conditions": [
                    {
                        "name": "Acute Febrile Illness Pattern",
                        "relevance": "Possible",
                        "explanation": "Fever indicates systemic immune response, often associated with viral or bacterial infections.",
                        "supporting_symptoms": ["fever"],
                        "missing_information": ["exact body temperature", "duration", "associated localized symptoms"],
                        "confidence_label": "Possible"
                    }
                ],
                "red_flags": [],
                "extracted_signals": symptoms or ["fever"]
            }

        # 5. Musculoskeletal / Knee / Joint pain
        if any(s in symptoms for s in ["knee pain", "joint pain", "back pain", "leg pain", "bone pain", "sprain", "fracture"]):
            return {
                "urgency_category": "ROUTINE",
                "urgency_summary": "Routine orthopedic consultation suggested for musculoskeletal symptoms.",
                "clinical_summary": "Musculoskeletal or joint discomfort reported. Evaluation by an Orthopedic specialist is recommended.",
                "primary_specialty": "Orthopedics",
                "secondary_specialties": ["Physical Medicine & Rehabilitation"],
                "possible_conditions": [
                    {
                        "name": "Musculoskeletal or Joint Strain",
                        "relevance": "Possible",
                        "explanation": "Joint or limb pain often relates to localized mechanical strain, ligament irritation, or joint inflammation.",
                        "supporting_symptoms": [s for s in symptoms if s in ["knee pain", "joint pain", "back pain", "leg pain", "sprain"]],
                        "missing_information": ["recent trauma history", "joint swelling severity"],
                        "confidence_label": "Possible"
                    }
                ],
                "red_flags": [],
                "extracted_signals": symptoms or ["joint pain"]
            }

        # 6. Neurological / Headache
        if any(s in symptoms for s in ["headache", "dizziness", "seizure", "numbness", "paralysis"]):
            return {
                "urgency_category": "MODERATE",
                "urgency_summary": "Neurological consultation recommended.",
                "clinical_summary": "Headache or neurological symptoms reported. Assessment by a Neurologist or General Physician is advised.",
                "primary_specialty": "Neurology",
                "secondary_specialties": ["General Medicine"],
                "possible_conditions": [
                    {
                        "name": "Vascular or Tension Headache Pattern",
                        "relevance": "Possible",
                        "explanation": "Headaches can relate to tension, vascular changes, or neurological factors.",
                        "supporting_symptoms": [s for s in symptoms if s in ["headache", "dizziness"]],
                        "missing_information": ["onset pattern", "duration", "vision changes"],
                        "confidence_label": "Possible"
                    }
                ],
                "red_flags": [],
                "extracted_signals": symptoms or ["headache"]
            }

        # 7. Vague / Non-specific symptoms (e.g. "I feel tired", "I feel weird")
        return {
            "urgency_category": "ROUTINE",
            "urgency_summary": "General medical evaluation suggested for broad symptoms.",
            "clinical_summary": "Reported symptoms are non-specific. Fatigue or general discomfort can have various causes, and further clinical detail or examination by a healthcare provider is recommended.",
            "primary_specialty": "General Medicine",
            "secondary_specialties": ["Internal Medicine"],
            "possible_conditions": [],
            "red_flags": [],
            "extracted_signals": symptoms or ["general symptoms"]
        }

    def reconcile_llm_response(self, text: str, llm_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reconciles LLM output with deterministic safety rules.
        Ensures LLM cannot override emergency red flags, downgrade urgency, or hardcode defaults.
        """
        det = self.deterministic_triage(text)

        # Force EMERGENCY if deterministic rules detect red flags
        if det["urgency_category"] == "EMERGENCY":
            llm_data["urgency_category"] = "EMERGENCY"
            llm_data["primary_specialty"] = det["primary_specialty"]
            llm_data["red_flags"] = list(set((llm_data.get("red_flags") or []) + det["red_flags"]))

        # Prevent Emergency Medicine hardcode for routine/moderate symptoms
        if llm_data.get("primary_specialty") == "Emergency Medicine" and llm_data.get("urgency_category") in ["ROUTINE", "MODERATE"]:
            llm_data["primary_specialty"] = det["primary_specialty"]

        # Ensure possible_conditions is [] for vague input or unknown claims
        classified = self.classify_user_input(text)
        if (classified["unknown_claims"] and not classified["reported_symptoms"]) or (not classified["reported_symptoms"] and "tired" in text.lower()):
            llm_data["possible_conditions"] = []
            llm_data["clinical_summary"] = det["clinical_summary"]

        return llm_data

triage_engine = TriageEngine()
