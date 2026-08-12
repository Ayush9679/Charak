import { apiClient } from "./client";
import { HealthCheckResponse } from "./types";

export async function checkHealth(signal?: AbortSignal): Promise<HealthCheckResponse> {
  return apiClient.get<HealthCheckResponse>("/health", {
    timeoutMs: 5000, // 5 seconds fast health check
    signal,
  });
}
