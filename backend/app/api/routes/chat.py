"""
Chat routes — Phase 6
Provides:
- POST /chat: Intent detection → auto-triage for symptom/emergency messages
- POST /chat/image: Structured document extraction via DocumentExtractor
- POST /chat/hospitals: Fetch hospitals using conversation analysis context

Intent classification:
  EMERGENCY_SYMPTOM  → immediate emergency triage + hospital search
  SYMPTOM_REPORT     → auto-triage + hospital search
  HOSPITAL_SEARCH    → use stored analysis context to find hospitals
  DOCUMENT_FOLLOWUP  → reference previously extracted document data
  GENERAL_HEALTH_QUESTION → standard Currado chat response
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import base64
import re
import json

from app.db.database import get_db
from app.models.hospital import ChatHistoryRecord
from app.schemas.schemas import (
    ChatRequestSchema,
    ChatResponseSchema,
    DocumentChatResponseSchema,
    SuggestedActionSchema,
    PrescriptionExtractionSchema,
    MedicationExtractionSchema,
)
from app.ai.groq_client import groq_client
from app.ai.triage import triage_engine
from app.ai.document_extractor import (
    validate_file,
    extract_from_image_via_groq,
    extract_from_pdf_via_text,
    prescription_to_summary,
    PrescriptionExtraction,
)
from app.services.clinical_analysis_service import clinical_analysis_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Intent Detection
# ---------------------------------------------------------------------------

EMERGENCY_KEYWORDS = [
    "heart attack", "cardiac arrest", "having a heart attack", "can't breathe",
    "cannot breathe", "stroke", "anaphylaxis", "unconscious", "gasping",
    "severe chest pain", "not breathing", "dying", "kill myself", "suicidal",
    "severe bleeding",
]

SYMPTOM_KEYWORDS = [
    "i have", "i am having", "i feel", "i've been", "i've had", "i had",
    "suffering from", "experiencing", "my", "started", "pain", "ache",
    "fever", "vomit", "nausea", "headache", "dizzy", "cough", "rash",
    "tired", "fatigue", "ftigue", "fatige", "weak", "breathless",
    "stomach", "chest", "throat", "runny", "swollen", "bleeding",
    "itchy", "burning", "numbness", "tingling",
]

HOSPITAL_SEARCH_KEYWORDS = [
    "find hospital", "show hospital", "find clinic", "nearby hospital",
    "hospital near", "where should i go", "find a doctor", "book appointment",
    "which hospital", "emergency hospital", "find specialist", "nearest hospital",
    "hospital for", "cardiologist", "orthopedic", "neurologist",
]


def detect_intent(message: str) -> str:
    """
    Classify the user message into a primary intent category.
    Emergency detection is deterministic and takes highest priority.
    """
    lower = message.lower().strip()

    # 1. Deterministic emergency check (highest priority)
    red_flags = triage_engine.check_deterministic_red_flags(message)
    if red_flags:
        return "EMERGENCY_SYMPTOM"

    # 2. Explicit symptom report
    symptom_score = sum(1 for kw in SYMPTOM_KEYWORDS if kw in lower)
    if symptom_score >= 2:
        return "SYMPTOM_REPORT"

    # 3. Hospital search intent
    if any(kw in lower for kw in HOSPITAL_SEARCH_KEYWORDS):
        return "HOSPITAL_SEARCH"

    # 4. Single symptom word with "I have" or similar
    if re.search(r"\b(i have|i am|i feel|i've|i had|having|feeling)\b", lower):
        return "SYMPTOM_REPORT"

    return "GENERAL_HEALTH_QUESTION"


def _extraction_to_schema(extraction: PrescriptionExtraction) -> PrescriptionExtractionSchema:
    """Convert PrescriptionExtraction dataclass to Pydantic schema."""
    meds = [
        MedicationExtractionSchema(
            name=m.name,
            strength=m.strength,
            dosage=m.dosage,
            frequency=m.frequency,
            duration=m.duration,
            instructions=m.instructions,
            confidence=m.confidence,
            reason=m.reason,
        )
        for m in extraction.medications
    ]
    return PrescriptionExtractionSchema(
        document_type=extraction.document_type,
        patient_name=extraction.patient_name,
        doctor_name=extraction.doctor_name,
        hospital_or_clinic=extraction.hospital_or_clinic,
        date=extraction.date,
        medications=meds,
        diagnoses_or_conditions=extraction.diagnoses_or_conditions,
        lab_tests=extraction.lab_tests,
        follow_up=extraction.follow_up,
        uncertain_fields=extraction.uncertain_fields,
        confidence_notes=extraction.confidence_notes,
        extraction_method=extraction.extraction_method,
        safety_notice=extraction.safety_notice,
    )


# ---------------------------------------------------------------------------
# POST /chat
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponseSchema)
async def currado_chat_endpoint(
    payload: ChatRequestSchema,
    db: Session = Depends(get_db),
):
    conv_id = payload.conversation_id or str(uuid.uuid4())

    # Fetch past conversation context (last 10 messages)
    history_records = (
        db.query(ChatHistoryRecord)
        .filter(ChatHistoryRecord.conversation_id == conv_id)
        .order_by(ChatHistoryRecord.created_at.asc())
        .all()
    )
    history = [{"sender": r.sender, "message": r.message} for r in history_records]

    # Save user message
    user_rec = ChatHistoryRecord(
        conversation_id=conv_id,
        sender="user",
        message=payload.message,
    )
    db.add(user_rec)
    db.commit()

    # Detect intent
    intent = detect_intent(payload.message)

    # Retrieve previous analysis context from session history
    prev_analysis_context = payload.context or {}
    for hr in reversed(history_records):
        if hr.sender == "currado" and hr.analysis_context:
            try:
                prev_analysis_context = json.loads(hr.analysis_context)
                break
            except Exception:
                pass

    response_text = ""
    urgency = "ROUTINE"
    specialties = []
    red_flags = []
    action_schema = None
    analysis_id = None
    hospitals_result = None

    # ── EMERGENCY_SYMPTOM ──────────────────────────────────────────────────
    if intent == "EMERGENCY_SYMPTOM":
        # Immediate deterministic safety response — do NOT wait for LLM
        response_text = (
            "⚠️ Your message contains emergency warning signs. "
            "Symptoms such as severe chest pain, heart attack, stroke, or inability to breathe "
            "require IMMEDIATE emergency medical attention.\n\n"
            "Please call 102 or 108 RIGHT NOW, or have someone take you to the nearest emergency department. "
            "Do not wait for online guidance."
        )
        urgency = "EMERGENCY"
        specialties = ["Emergency Medicine", "Cardiology"]

        det = triage_engine.check_deterministic_red_flags(payload.message)
        red_flags = det.get("red_flags", []) if det else []

        # Run full clinical analysis to get hospital context
        lat = payload.context.get("latitude") if payload.context else None
        lng = payload.context.get("longitude") if payload.context else None

        result = await clinical_analysis_service.analyze(
            symptoms=payload.message,
            latitude=lat,
            longitude=lng,
            db=db,
            include_hospitals=(lat is not None and lng is not None),
        )
        analysis_id = result.get("analysis_id")
        hospitals_result = result.get("hospitals") or None

        action_schema = SuggestedActionSchema(
            type="FIND_EMERGENCY_HOSPITALS",
            label="Find Nearby Emergency Hospitals",
            specialty="Emergency Medicine",
            emergency_required=True,
            payload={
                "specialty": "Emergency Medicine",
                "emergency_required": True,
                "latitude": lat,
                "longitude": lng,
                "analysis_id": analysis_id,
            },
        )

    # ── SYMPTOM_REPORT ─────────────────────────────────────────────────────
    elif intent == "SYMPTOM_REPORT":
        lat = payload.context.get("latitude") if payload.context else None
        lng = payload.context.get("longitude") if payload.context else None

        result = await clinical_analysis_service.analyze(
            symptoms=payload.message,
            latitude=lat,
            longitude=lng,
            db=db,
            include_hospitals=True,
        )
        analysis_id = result.get("analysis_id")
        urgency = result.get("urgency_category", "ROUTINE")
        specialties = ([result.get("primary_specialty")] if result.get("primary_specialty") else [])
        red_flags = result.get("red_flags", [])
        hospitals_result = result.get("hospitals") or None

        # Generate Currado narrative from analysis
        ai_result = await groq_client.currado_chat(
            payload.message,
            history,
            {
                "primary_specialty": result.get("primary_specialty"),
                "urgency_category": urgency,
                "urgency_summary": result.get("urgency_summary"),
                "clinical_summary": result.get("clinical_summary"),
                "red_flags": red_flags,
                "normalized_symptoms": result.get("normalized_symptoms", []),
            },
        )
        response_text = ai_result.get("response", "I've analyzed your symptoms.")

        action_schema = SuggestedActionSchema(
            type="FIND_HOSPITALS",
            label=f"Find Nearby {result.get('primary_specialty', 'General Medicine')} Hospitals",
            specialty=result.get("primary_specialty", "General Medicine"),
            emergency_required=False,
            payload={
                "specialty": result.get("primary_specialty", "General Medicine"),
                "emergency_required": False,
                "latitude": lat,
                "longitude": lng,
                "analysis_id": analysis_id,
            },
        )

    # ── HOSPITAL_SEARCH ────────────────────────────────────────────────────
    elif intent == "HOSPITAL_SEARCH":
        lat = payload.context.get("latitude") if payload.context else None
        lng = payload.context.get("longitude") if payload.context else None
        specialty = (
            prev_analysis_context.get("primary_specialty")
            or (payload.context.get("primary_specialty") if payload.context else None)
            or "General Medicine"
        )

        result = await clinical_analysis_service.analyze(
            symptoms=f"Find hospitals for {specialty}",
            latitude=lat,
            longitude=lng,
            db=db,
            include_hospitals=True,
        )
        analysis_id = result.get("analysis_id")
        hospitals_result = result.get("hospitals") or None

        if hospitals_result:
            response_text = f"I found {len(hospitals_result)} nearby facilities matching {specialty}."
        elif lat is None:
            response_text = (
                "To find nearby hospitals, I need your location. "
                "Please allow location access so I can show you the closest verified facilities."
            )
        else:
            response_text = f"No verified hospitals found nearby for {specialty}."

        action_schema = SuggestedActionSchema(
            type="FIND_HOSPITALS",
            label=f"Find {specialty} Hospitals",
            specialty=specialty,
            emergency_required=False,
            payload={"specialty": specialty, "latitude": lat, "longitude": lng},
        )
        urgency = prev_analysis_context.get("urgency_category", "ROUTINE")
        specialties = [specialty]

    # ── GENERAL_HEALTH_QUESTION ────────────────────────────────────────────
    else:
        ai_result = await groq_client.currado_chat(payload.message, history, payload.context)

        response_text = ai_result.get("response", "I'm here to help navigate your healthcare options.")
        urgency = ai_result.get("urgency", "ROUTINE")
        specialties = ai_result.get("specialties", [])
        red_flags = ai_result.get("red_flags", [])

        raw_action = ai_result.get("suggested_action")
        if isinstance(raw_action, dict) and raw_action.get("type"):
            action_schema = SuggestedActionSchema(
                type=raw_action.get("type"),
                label=raw_action.get("label", "View Hospitals"),
                specialty=raw_action.get("specialty"),
                route=raw_action.get("route"),
            )

    # Save Currado reply with analysis context for future messages
    analysis_ctx_json = None
    if analysis_id:
        analysis_ctx_json = json.dumps({
            "analysis_id": analysis_id,
            "primary_specialty": specialties[0] if specialties else None,
            "urgency_category": urgency,
            "red_flags": red_flags,
        })

    bot_rec = ChatHistoryRecord(
        conversation_id=conv_id,
        sender="currado",
        message=response_text,
        urgency=urgency,
        specialties=specialties,
        analysis_context=analysis_ctx_json,
        intent_type=intent,
    )
    db.add(bot_rec)
    db.commit()

    return ChatResponseSchema(
        conversation_id=conv_id,
        response=response_text,
        urgency=urgency,
        specialties=specialties,
        red_flags=red_flags,
        suggested_action=action_schema,
        analysis_id=analysis_id,
        intent_type=intent,
        hospitals=hospitals_result,
    )


# ---------------------------------------------------------------------------
# POST /chat/image
# ---------------------------------------------------------------------------

@router.post("/chat/image")
async def currado_image_chat_endpoint(
    image: UploadFile = File(...),
    message: Optional[str] = Form(""),
    conversation_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    conv_id = conversation_id or str(uuid.uuid4())
    contents = await image.read()

    # Determine MIME
    mime_type = image.content_type or "application/octet-stream"

    # Validate file
    validation_error = validate_file(contents, mime_type)
    if validation_error:
        raise HTTPException(status_code=400, detail=validation_error)

    # Log user upload record (no patient data in message)
    user_rec = ChatHistoryRecord(
        conversation_id=conv_id,
        sender="user",
        message=f"[Medical Document Uploaded: {image.filename or 'document'}]",
    )
    db.add(user_rec)
    db.commit()

    # Extract content based on file type
    extraction: PrescriptionExtraction
    if mime_type == "application/pdf":
        extraction = await extract_from_pdf_via_text(contents, groq_client)
    else:
        image_b64 = base64.b64encode(contents).decode("utf-8")
        extraction = await extract_from_image_via_groq(
            image_b64, mime_type, message or "", groq_client
        )

    # Build human-readable summary
    response_text = prescription_to_summary(extraction)

    # Convert to schema
    extraction_schema = _extraction_to_schema(extraction)

    # Build dynamic action buttons based on extraction content
    action_schema = None
    triage_context = None

    if extraction.diagnoses_or_conditions:
        # Build a hospital search action from the documented conditions
        condition_text = ", ".join(extraction.diagnoses_or_conditions[:2])
        triage_context = {"conditions_from_document": extraction.diagnoses_or_conditions}
        action_schema = SuggestedActionSchema(
            type="FIND_HOSPITALS",
            label=f"Find Hospitals for {extraction.diagnoses_or_conditions[0]}",
            specialty="General Medicine",
            emergency_required=False,
            payload={"context_from_document": condition_text},
        )

    # Save bot response
    bot_rec = ChatHistoryRecord(
        conversation_id=conv_id,
        sender="currado",
        message=response_text,
        urgency="ROUTINE",
        specialties=[],
        intent_type="DOCUMENT_UPLOAD",
    )
    db.add(bot_rec)
    db.commit()

    # Return the structured document response
    return {
        "conversation_id": conv_id,
        "response": response_text,
        "urgency": "ROUTINE",
        "specialties": [],
        "red_flags": [],
        "suggested_action": action_schema.model_dump() if action_schema else None,
        "analysis_id": None,
        "intent_type": "DOCUMENT_UPLOAD",
        "document_type": extraction.document_type,
        "prescription_extraction": extraction_schema.model_dump(),
        "hospitals": None,
    }
