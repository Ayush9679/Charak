import type { RecommendationResponse } from "@/api/types";

export type AnalysisInput = {
  symptoms: string;
  diagnosis: string;
  reportName: string | null;
  location: string;
  latitude: number | null;
  longitude: number | null;
  budget: string;
  insurance: string;
  distance: number;
};

const KEY = "charak.analysis";
const RESULT_KEY = "charak.recommendation_result";

export const defaultInput: AnalysisInput = {
  symptoms: "",
  diagnosis: "",
  reportName: null,
  location: "",
  latitude: null,
  longitude: null,
  budget: "No preference",
  insurance: "Ayushman Bharat",
  distance: 15,
};

export function saveAnalysis(input: AnalysisInput) {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(KEY, JSON.stringify(input));
}

export function loadAnalysis(): AnalysisInput {
  if (typeof window === "undefined") return defaultInput;
  try {
    const raw = window.sessionStorage.getItem(KEY);
    return raw ? { ...defaultInput, ...JSON.parse(raw) } : defaultInput;
  } catch {
    return defaultInput;
  }
}

export function saveRecommendationResult(result: RecommendationResponse) {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(RESULT_KEY, JSON.stringify(result));
}

export function loadRecommendationResult(): RecommendationResponse | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem(RESULT_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function clearRecommendationResult() {
  if (typeof window === "undefined") return;
  window.sessionStorage.removeItem(RESULT_KEY);
}