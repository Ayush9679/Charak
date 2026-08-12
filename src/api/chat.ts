import { apiClient } from "./client";
import { ChatResponse } from "./types";

export interface SendChatMessagePayload {
  message: string;
  conversation_id?: string | undefined;
  context?: Record<string, any> | undefined;
}

export async function sendChatMessage(
  payload: SendChatMessagePayload,
  signal?: AbortSignal
): Promise<ChatResponse> {
  return apiClient.post<ChatResponse>("/chat", payload, {
    timeoutMs: 30000, // 30 seconds for Currado chat text
    signal,
  });
}

export async function sendChatImage(
  formData: FormData,
  signal?: AbortSignal
): Promise<ChatResponse> {
  return apiClient.upload<ChatResponse>("/chat/image", formData, {
    timeoutMs: 45000, // 45 seconds for vision analysis
    signal,
  });
}

export async function fetchCurradoHospitals(
  params: {
    lat?: number | null;
    lng?: number | null;
    specialty?: string;
    emergency_required?: boolean;
    radius_km?: number;
  },
  signal?: AbortSignal
) {
  const queryParams = new URLSearchParams();
  if (params.lat !== undefined && params.lat !== null) queryParams.set("latitude", params.lat.toString());
  if (params.lng !== undefined && params.lng !== null) queryParams.set("longitude", params.lng.toString());
  if (params.specialty) queryParams.set("specialty", params.specialty);
  if (params.emergency_required) queryParams.set("emergency_required", "true");
  if (params.radius_km) queryParams.set("radius_km", params.radius_km.toString());

  const url = `/hospitals/nearby${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
  return apiClient.get<any[]>(url, {
    timeoutMs: 15000,
    signal,
  });
}
