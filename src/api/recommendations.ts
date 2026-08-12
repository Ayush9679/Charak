import { apiClient } from "./client";
import { RecommendationResponse, SymptomInput } from "./types";

export async function createRecommendation(
  payload: SymptomInput,
  signal?: AbortSignal
): Promise<RecommendationResponse> {
  return apiClient.post<RecommendationResponse>("/recommendations", payload, {
    timeoutMs: 30000, // 30 seconds maximum for AI recommendation pipeline
    signal,
  });
}
