export type DataTier = "verified" | "aggregated" | "integrated";

export type Hospital = {
  id: string;
  name: string;
  area: string;
  city: string;
  distanceKm: number;
  travelMin: number;
  suitability: number;
  specialtyMatch: number;
  specialties: string[];
  emergency: boolean;
  insurance: string[];
  estimatedCost: string | null;
  availability: { integrated: boolean; beds?: number; icu?: number };
  doctors: { name: string; specialty: string; experience: string }[];
  rating: number;
  reviews: number;
  accreditation: string[];
  facilities: string[];
  departments: string[];
  tier: DataTier;
  reasons: string[];
  about: string;
};

export const hospitals: Hospital[] = [];

export const specialtySignals = [
  { label: "Cardiology", confidence: 0.92 },
  { label: "Emergency Medicine", confidence: 0.78 },
  { label: "Pulmonology", confidence: 0.41 },
];

export const pipelineStages = [
  { key: "input", label: "Symptom & report intake", detail: "Structuring your description" },
  { key: "nlp", label: "Medical NLP", detail: "Extracting clinical entities" },
  { key: "specialty", label: "Specialty detection", detail: "Mapping to medical specialties" },
  { key: "urgency", label: "Urgency assessment", detail: "Categorising care timeline" },
  { key: "discovery", label: "Hospital discovery", detail: "Scanning verified facilities nearby" },
  { key: "ranking", label: "AI ranking", detail: "Weighing suitability factors" },
  { key: "results", label: "Recommendations", detail: "Preparing your shortlist" },
];

export const DISCLAIMER =
  "AI assists healthcare navigation. It does not replace medical professionals or provide definitive medical diagnoses.";

export const tierMeta: Record<DataTier, { label: string; dot: string }> = {
  verified: { label: "Verified public data", dot: "bg-success" },
  aggregated: { label: "Verified aggregated data", dot: "bg-warning" },
  integrated: { label: "Hospital integration", dot: "bg-teal" },
};

export function getHospital(id: string) {
  return hospitals.find((h) => h.id === id);
}