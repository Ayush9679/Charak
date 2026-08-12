"""
Document Extractor - Phase 6
Handles medical document extraction:
- Validates MIME type and file size
- Detects document type (PRESCRIPTION, LAB_REPORT, etc.)
- Extracts structured PrescriptionExtraction from images using Groq Vision
- Extracts text from PDF files using PyMuPDF
- Privacy-safe: never logs patient names or raw prescriptions
- Always cleans up temporary files
"""

import json
import base64
import os
import tempfile
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict

ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/webp", "application/pdf"
}
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10MB

DOCUMENT_TYPE_KEYWORDS = {
    "PRESCRIPTION": [
        "rx", "prescription", "prescribed", "tablet", "capsule", "mg", "ml",
        "twice daily", "once daily", "bd", "od", "sos", "take", "dose", "dosage",
        "syrup", "ointment", "drops", "injection", "doctor", "dr.", "physician",
    ],
    "LAB_REPORT": [
        "lab report", "laboratory", "blood test", "cbc", "complete blood count",
        "haemoglobin", "hemoglobin", "platelet", "wbc", "rbc", "serum", "plasma",
        "test result", "normal range", "reference range", "urine analysis",
        "creatinine", "bilirubin", "cholesterol", "glucose", "hba1c",
    ],
    "MEDICAL_REPORT": [
        "medical report", "clinical report", "discharge summary", "diagnosis",
        "investigation", "findings", "impression", "radiology", "ecg", "echo",
        "x-ray", "mri", "ct scan", "ultrasound", "biopsy", "pathology",
    ],
    "DISCHARGE_SUMMARY": [
        "discharge summary", "discharge date", "admitted", "admission date",
        "treating physician", "ward", "primary diagnosis", "treatment given",
        "follow up", "follow-up",
    ],
}


@dataclass
class MedicationExtraction:
    name: Optional[str] = None
    strength: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None
    confidence: str = "LOW"
    reason: Optional[str] = None


@dataclass
class PrescriptionExtraction:
    document_type: str = "UNKNOWN"
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    hospital_or_clinic: Optional[str] = None
    date: Optional[str] = None
    medications: List[MedicationExtraction] = field(default_factory=list)
    diagnoses_or_conditions: List[str] = field(default_factory=list)
    lab_tests: List[str] = field(default_factory=list)
    follow_up: Optional[str] = None
    raw_extracted_text: Optional[str] = None
    uncertain_fields: List[str] = field(default_factory=list)
    confidence_notes: List[str] = field(default_factory=list)
    extraction_method: str = "VISION"
    safety_notice: str = (
        "This extraction is for informational purposes only. "
        "CHANAKYA does not provide medical advice. Consult your healthcare provider "
        "regarding any medications, diagnoses, or instructions in this document."
    )


def validate_file(content: bytes, mime_type: str) -> Optional[str]:
    """Returns an error message if the file fails validation, else None."""
    if len(content) > MAX_FILE_BYTES:
        return f"File size {len(content) // (1024*1024):.1f}MB exceeds the 10MB limit."
    normalized_mime = mime_type.lower().split(";")[0].strip()
    if normalized_mime not in ALLOWED_MIME_TYPES:
        return (
            f"Unsupported file type '{mime_type}'. "
            "Allowed types: JPEG, PNG, WEBP, PDF."
        )
    return None


def detect_document_type(text: str) -> str:
    """
    Deterministically detect document type from extracted text.
    Uses keyword scoring. Returns the highest-scoring type.
    """
    if not text:
        return "UNKNOWN"
    lower = text.lower()
    scores: Dict[str, int] = {t: 0 for t in DOCUMENT_TYPE_KEYWORDS}
    for doc_type, keywords in DOCUMENT_TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                scores[doc_type] += 1
    best_type = max(scores, key=lambda t: scores[t])
    if scores[best_type] == 0:
        return "OTHER_MEDICAL_DOCUMENT"
    return best_type


def extract_text_from_pdf(pdf_bytes: bytes) -> Optional[str]:
    """
    Extract text from a PDF file using PyMuPDF.
    Returns None if PyMuPDF is not available or extraction fails.
    """
    try:
        import fitz  # type: ignore[import]
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(pdf_bytes)
                tmp_path = tmp.name
            doc = fitz.open(tmp_path)
            pages_text = []
            for page_num in range(min(len(doc), 10)):  # max 10 pages
                page = doc.load_page(page_num)
                pages_text.append(page.get_text())
            doc.close()
            full_text = "\n".join(pages_text).strip()
            return full_text if full_text else None
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
    except ImportError:
        print("[DOCUMENT_EXTRACTOR] PyMuPDF (fitz) not available for PDF extraction.")
        return None
    except Exception as e:
        print(f"[DOCUMENT_EXTRACTOR] PDF extraction error: {e}")
        return None


def _build_vision_extraction_prompt(user_note: str = "") -> str:
    return f"""You are a medical document extraction assistant.
Analyze this medical document image and extract structured information.

User note: "{user_note}"

CRITICAL SAFETY RULES:
1. Extract ONLY what is clearly readable in the document. Do NOT guess or hallucinate.
2. If a field is unreadable, set it to null and note it in uncertain_fields.
3. Do NOT add medication names that are not explicitly visible.
4. Handwritten text that is unclear must be marked as LOW confidence.
5. Never modify dosages. Never recommend medications.
6. Do NOT generate diagnoses not explicitly stated in the document.
7. NEVER generate, estimate, or output any pricing or costs.

Return ONLY valid JSON matching this exact schema:
{{
  "document_type": "PRESCRIPTION" | "LAB_REPORT" | "MEDICAL_REPORT" | "DISCHARGE_SUMMARY" | "OTHER_MEDICAL_DOCUMENT" | "UNKNOWN",
  "patient_name": null,
  "doctor_name": null,
  "hospital_or_clinic": null,
  "date": null,
  "medications": [
    {{
      "name": "Medication name as written",
      "strength": null,
      "dosage": null,
      "frequency": null,
      "duration": null,
      "instructions": null,
      "confidence": "HIGH" | "MEDIUM" | "LOW",
      "reason": null
    }}
  ],
  "diagnoses_or_conditions": [],
  "lab_tests": [],
  "follow_up": null,
  "raw_extracted_text": "Raw text extracted from the document",
  "uncertain_fields": ["List any fields that were unclear or unreadable"],
  "confidence_notes": ["Any notes about extraction quality"]
}}
Return ONLY the JSON object. No markdown, no explanation."""


async def extract_from_image_via_groq(
    image_b64: str,
    mime_type: str,
    user_note: str,
    groq_client_instance,
) -> PrescriptionExtraction:
    """
    Use Groq Vision to extract structured data from a medical image.
    Falls back to a safe "unreadable" response on failure.
    """
    import httpx
    from app.core.config import settings

    if not groq_client_instance.is_configured():
        return PrescriptionExtraction(
            document_type="UNKNOWN",
            confidence_notes=["Vision AI not configured. Set GROQ_API_KEY to enable document extraction."],
        )

    prompt = _build_vision_extraction_prompt(user_note)

    # Normalize MIME for Groq
    image_mime = mime_type.lower().split(";")[0].strip()
    if image_mime not in {"image/jpeg", "image/jpg", "image/png", "image/webp"}:
        image_mime = "image/jpeg"

    payload = {
        "model": groq_client_instance.vision_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{image_mime};base64,{image_b64}"
                        },
                    },
                ],
            }
        ],
        "temperature": 0.1,
        "max_tokens": 2048,
    }

    headers = {
        "Authorization": f"Bearer {groq_client_instance.api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=settings.GROQ_VISION_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{groq_client_instance.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            if response.status_code == 200:
                data = response.json()
                raw_content = data["choices"][0]["message"]["content"]
                # Strip any markdown code fences
                clean = raw_content.strip()
                if clean.startswith("```"):
                    lines = clean.split("\n")
                    clean = "\n".join(lines[1:-1]) if len(lines) > 2 else clean
                parsed = json.loads(clean)
                meds = []
                for m in parsed.get("medications", []):
                    meds.append(MedicationExtraction(
                        name=m.get("name"),
                        strength=m.get("strength"),
                        dosage=m.get("dosage"),
                        frequency=m.get("frequency"),
                        duration=m.get("duration"),
                        instructions=m.get("instructions"),
                        confidence=m.get("confidence", "LOW"),
                        reason=m.get("reason"),
                    ))
                return PrescriptionExtraction(
                    document_type=parsed.get("document_type", "UNKNOWN"),
                    patient_name=parsed.get("patient_name"),
                    doctor_name=parsed.get("doctor_name"),
                    hospital_or_clinic=parsed.get("hospital_or_clinic"),
                    date=parsed.get("date"),
                    medications=meds,
                    diagnoses_or_conditions=parsed.get("diagnoses_or_conditions", []),
                    lab_tests=parsed.get("lab_tests", []),
                    follow_up=parsed.get("follow_up"),
                    raw_extracted_text=parsed.get("raw_extracted_text"),
                    uncertain_fields=parsed.get("uncertain_fields", []),
                    confidence_notes=parsed.get("confidence_notes", []),
                    extraction_method="GROQ_VISION",
                )
            else:
                print(f"[DOCUMENT_EXTRACTOR] Groq Vision error {response.status_code}: {response.text[:200]}")
    except json.JSONDecodeError as e:
        print(f"[DOCUMENT_EXTRACTOR] JSON parse error: {e}")
    except Exception as e:
        print(f"[DOCUMENT_EXTRACTOR] Vision extraction exception: {e}")

    return PrescriptionExtraction(
        document_type="UNKNOWN",
        uncertain_fields=["all"],
        confidence_notes=["Some prescription text could not be read confidently. Please consult your healthcare provider."],
        extraction_method="VISION_FAILED",
    )


async def extract_from_pdf_via_text(
    pdf_bytes: bytes,
    groq_client_instance,
) -> PrescriptionExtraction:
    """
    Extract from a PDF: first try text extraction (PyMuPDF), 
    then fall back to rendering page 1 as image for Vision.
    """
    extracted_text = extract_text_from_pdf(pdf_bytes)

    if extracted_text and len(extracted_text.strip()) > 50:
        # Text-based PDF — use LLM to structure the text
        doc_type = detect_document_type(extracted_text)
        # Truncate text to avoid token limits
        text_truncated = extracted_text[:4000]
        extraction = await _structure_text_via_groq(
            text_truncated, doc_type, groq_client_instance
        )
        extraction.extraction_method = "PDF_TEXT_EXTRACTION"
        return extraction
    else:
        # Scanned/image PDF — render page 1 as image and use Vision
        try:
            import fitz  # type: ignore[import]
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp.write(pdf_bytes)
                    tmp_path = tmp.name
                doc = fitz.open(tmp_path)
                page = doc.load_page(0)
                pix = page.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("jpeg")
                doc.close()
                image_b64 = base64.b64encode(img_bytes).decode("utf-8")
                result = await extract_from_image_via_groq(
                    image_b64, "image/jpeg", "Scanned PDF page", groq_client_instance
                )
                result.extraction_method = "PDF_SCANNED_VISION"
                return result
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
        except ImportError:
            return PrescriptionExtraction(
                document_type="UNKNOWN",
                confidence_notes=[
                    "PDF processing requires PyMuPDF. "
                    "Run: pip install pymupdf"
                ],
            )
        except Exception as e:
            print(f"[DOCUMENT_EXTRACTOR] Scanned PDF rendering error: {e}")
            return PrescriptionExtraction(
                document_type="UNKNOWN",
                uncertain_fields=["all"],
                confidence_notes=["Unable to process this scanned PDF."],
            )


async def _structure_text_via_groq(
    text: str,
    doc_type: str,
    groq_client_instance,
) -> PrescriptionExtraction:
    """Structure already-extracted text via Groq text completion."""
    import httpx
    from app.core.config import settings

    if not groq_client_instance.is_configured():
        return PrescriptionExtraction(
            document_type=doc_type,
            raw_extracted_text=text,
            confidence_notes=["Vision AI not configured."],
        )

    prompt = f"""You are a medical document structuring assistant.
Structure the following extracted text from a {doc_type} into JSON.

CRITICAL SAFETY RULES:
1. Extract ONLY what is present in the text. Do NOT hallucinate.
2. If a field is missing or ambiguous, set it to null.
3. Never recommend or modify medications.
4. Never generate diagnoses not explicitly in the text.
5. Mark unclear items with confidence: "LOW".
6. NEVER generate any pricing or costs.

Extracted text:
\"\"\"
{text}
\"\"\"

Return ONLY valid JSON:
{{
  "document_type": "{doc_type}",
  "patient_name": null,
  "doctor_name": null,
  "hospital_or_clinic": null,
  "date": null,
  "medications": [{{"name": null, "strength": null, "dosage": null, "frequency": null, "duration": null, "instructions": null, "confidence": "HIGH"}}],
  "diagnoses_or_conditions": [],
  "lab_tests": [],
  "follow_up": null,
  "uncertain_fields": [],
  "confidence_notes": []
}}"""

    headers = {
        "Authorization": f"Bearer {groq_client_instance.api_key}",
        "Content-Type": "application/json",
    }
    payload_dict = {
        "model": groq_client_instance.model,
        "messages": [
            {"role": "system", "content": "You are a medical document structuring system that outputs JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }

    try:
        async with httpx.AsyncClient(timeout=settings.GROQ_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{groq_client_instance.base_url}/chat/completions",
                headers=headers,
                json=payload_dict,
            )
            if response.status_code == 200:
                data = response.json()
                parsed = json.loads(data["choices"][0]["message"]["content"])
                meds = []
                for m in parsed.get("medications", []):
                    if m.get("name"):
                        meds.append(MedicationExtraction(
                            name=m.get("name"),
                            strength=m.get("strength"),
                            dosage=m.get("dosage"),
                            frequency=m.get("frequency"),
                            duration=m.get("duration"),
                            instructions=m.get("instructions"),
                            confidence=m.get("confidence", "MEDIUM"),
                        ))
                return PrescriptionExtraction(
                    document_type=parsed.get("document_type", doc_type),
                    patient_name=parsed.get("patient_name"),
                    doctor_name=parsed.get("doctor_name"),
                    hospital_or_clinic=parsed.get("hospital_or_clinic"),
                    date=parsed.get("date"),
                    medications=meds,
                    diagnoses_or_conditions=parsed.get("diagnoses_or_conditions", []),
                    lab_tests=parsed.get("lab_tests", []),
                    follow_up=parsed.get("follow_up"),
                    raw_extracted_text=text,
                    uncertain_fields=parsed.get("uncertain_fields", []),
                    confidence_notes=parsed.get("confidence_notes", []),
                )
    except Exception as e:
        print(f"[DOCUMENT_EXTRACTOR] Text structuring error: {e}")

    return PrescriptionExtraction(
        document_type=doc_type,
        raw_extracted_text=text,
        confidence_notes=["Text extracted but structuring failed. Raw text preserved."],
    )


def prescription_to_summary(extraction: PrescriptionExtraction) -> str:
    """Build a human-readable Currado response from a PrescriptionExtraction."""
    lines = []

    type_labels = {
        "PRESCRIPTION": "prescription",
        "LAB_REPORT": "lab report",
        "MEDICAL_REPORT": "medical report",
        "DISCHARGE_SUMMARY": "discharge summary",
        "OTHER_MEDICAL_DOCUMENT": "medical document",
        "UNKNOWN": "document",
    }
    doc_label = type_labels.get(extraction.document_type, "document")
    lines.append(f"I've analyzed this {doc_label}. Here's what I found:\n")

    if extraction.doctor_name:
        lines.append(f"**Doctor:** {extraction.doctor_name}")
    if extraction.hospital_or_clinic:
        lines.append(f"**Clinic/Hospital:** {extraction.hospital_or_clinic}")
    if extraction.date:
        lines.append(f"**Date:** {extraction.date}")

    if extraction.medications:
        lines.append("\n**Medications listed in this document:**")
        for med in extraction.medications:
            med_line = f"• {med.name or '[Unreadable]'}"
            if med.strength:
                med_line += f" {med.strength}"
            if med.dosage:
                med_line += f" — {med.dosage}"
            if med.frequency:
                med_line += f", {med.frequency}"
            if med.duration:
                med_line += f" for {med.duration}"
            if med.confidence == "LOW":
                med_line += " *(may be inaccurate — handwriting unclear)*"
            lines.append(med_line)

    if extraction.diagnoses_or_conditions:
        lines.append("\n**Conditions mentioned:**")
        for cond in extraction.diagnoses_or_conditions:
            lines.append(f"• {cond}")

    if extraction.lab_tests:
        lines.append("\n**Lab tests ordered:**")
        for test in extraction.lab_tests:
            lines.append(f"• {test}")

    if extraction.follow_up:
        lines.append(f"\n**Follow-up:** {extraction.follow_up}")

    if extraction.uncertain_fields:
        lines.append(f"\n⚠️ *Some fields were unclear: {', '.join(extraction.uncertain_fields)}*")

    lines.append(
        "\n\n*This extraction is for informational purposes only. "
        "CHANAKYA does not provide medical advice. Please consult your healthcare provider "
        "regarding any medications or instructions in this document.*"
    )

    return "\n".join(lines)
