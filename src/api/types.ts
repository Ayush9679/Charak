export interface AvailabilityInfo {
  beds_available: number;
  icu_available: number;
  total_beds: number;
  total_icu: number;
  last_updated: string;
  status: "AVAILABLE" | "UNAVAILABLE";
}

export interface HospitalPricing {
  min: number | null;
  max: number | null;
  currency: string;
  status: "VERIFIED" | "DEMO" | "UNAVAILABLE" | "STALE" | "PROVIDER_UNAVAILABLE";
  source_type?: "verified" | "demo" | "unavailable";
  source: string | null;
  source_url?: string | null;
  last_verified_at?: string | null;
}

export interface TreatmentPrice {
  treatment: string;
  min_price: number;
  max_price: number;
  currency: string;
  source_type: "verified" | "demo" | "unavailable";
}

export interface DoctorPricing {
  min: number | null;
  max: number | null;
  currency: string;
  status: "VERIFIED" | "UNAVAILABLE" | "STALE" | "PROVIDER_UNAVAILABLE";
  source: string | null;
}

export interface Doctor {
  id: string;
  name: string;
  specialty: string;
  qualification: string;
  experience_years: number;
  consultation_fee?: number | null;
  pricing?: DoctorPricing;
  available_today: boolean;
  rating: number;
}

export interface Hospital {
  id: string;
  name: string;
  hfr_id: string;
  address: string;
  city: string;
  state: string;
  lat: number;
  lng: number;
  distance_km?: number | null | undefined;
  travel_time_mins?: number | null | undefined;
  specialties: string[];
  emergency_ready: boolean;
  insurance_supported: string[];
  estimated_cost_range?: string | null;
  pricing?: HospitalPricing;
  treatment_pricing?: TreatmentPrice[];
  data_provenance: "PUBLIC_REGISTRY" | "PUBLISHED_AGGREGATED" | "HOSPITAL_INTEGRATION" | "EXTERNAL_DISCOVERY" | string;
  availability?: AvailabilityInfo | undefined;
  doctors?: Doctor[] | undefined;
  rating: number;
  suitability?: number | undefined;
  recommendation_reasons?: string[] | undefined;
}

export interface SymptomInput {
  symptoms: string;
  location?: string | undefined;
  latitude?: number | null | undefined;
  longitude?: number | null | undefined;
  distance?: number | undefined;
  insurance?: string | undefined;
  budget_level?: string | undefined;
  report_file?: string | undefined;
}

export interface PossibleCondition {
  name: string;
  relevance?: string | undefined;
  explanation: string;
  supporting_symptoms?: string[] | undefined;
  missing_information?: string[] | undefined;
  confidence_label?: string | undefined;
}

export interface RecommendationResponse {
  id: string;
  urgency_category: "ROUTINE" | "MODERATE" | "URGENT" | "EMERGENCY";
  urgency_summary: string;
  clinical_summary?: string | undefined;
  primary_specialty: string;
  secondary_specialties: string[];
  possible_conditions?: PossibleCondition[] | undefined;
  red_flags: string[];
  extracted_signals: string[];
  hospitals: Hospital[];
  hospital_data_status: "AVAILABLE" | "UNAVAILABLE";
  disclaimer: string;
  processed_at: string;
}

export interface MedicationExtraction {
  name: string | null;
  strength: string | null;
  dosage: string | null;
  frequency: string | null;
  duration: string | null;
  instructions: string | null;
  confidence: string;
  reason?: string | null;
}

export interface PrescriptionExtraction {
  document_type: string;
  patient_name?: string | null;
  doctor_name?: string | null;
  hospital_or_clinic?: string | null;
  date?: string | null;
  medications: MedicationExtraction[];
  diagnoses_or_conditions: string[];
  lab_tests: string[];
  follow_up?: string | null;
  uncertain_fields: string[];
  confidence_notes: string[];
  extraction_method?: string;
  safety_notice?: string;
}

export interface SuggestedAction {
  type: "NAVIGATE_SPECIALTY" | "EMERGENCY_ALERT" | "FIND_HOSPITALS" | "FIND_EMERGENCY_HOSPITALS" | string;
  label: string;
  specialty?: string | undefined;
  route?: string | undefined;
  emergency_required?: boolean | undefined;
  payload?: Record<string, any> | undefined;
}

export interface ChatMessage {
  id: string;
  sender: "user" | "currado";
  text: string;
  timestamp: string;
  urgency?: string | undefined;
  specialties?: string[] | undefined;
  red_flags?: string[] | undefined;
  suggested_action?: SuggestedAction | undefined;
  image_url?: string | undefined;
  analysis_id?: string | undefined;
  intent_type?: string | undefined;
  hospitals?: Hospital[] | undefined;
  prescription_extraction?: PrescriptionExtraction | undefined;
  document_type?: string | undefined;
}

export interface SendChatMessagePayload {
  message: string;
  conversation_id?: string | undefined;
  context?: Record<string, any> | undefined;
}

export interface ChatResponse {
  conversation_id: string;
  response: string;
  urgency: string;
  specialties: string[];
  red_flags: string[];
  suggested_action?: SuggestedAction | undefined;
  analysis_id?: string | undefined;
  intent_type?: string | undefined;
  hospitals?: Hospital[] | undefined;
  extraction?: Record<string, any> | undefined;
  prescription_extraction?: PrescriptionExtraction | undefined;
  document_type?: string | undefined;
}

export interface HealthCheckResponse {
  status: "ok" | "degraded" | "error";
  service: string;
  timestamp: string;
  database: "connected" | "disconnected";
  groq: "configured" | "unconfigured" | "error";
  providers: {
    hospital_data: "available" | "unavailable";
    doctor_data: "available" | "unavailable";
    availability_data: "available" | "unavailable";
  };
}

export interface APIErrorResponse {
  code: string;
  message: string;
  details?: unknown;
}
