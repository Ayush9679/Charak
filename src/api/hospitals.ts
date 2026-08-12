import { apiClient } from "./client";
import { Doctor, Hospital } from "./types";

export interface FetchHospitalsOptions {
  page?: number | undefined;
  limit?: number | undefined;
  specialty?: string | undefined;
  location?: string | undefined;
  insurance?: string | undefined;
  signal?: AbortSignal | undefined;
}

export async function fetchHospitals(options: FetchHospitalsOptions = {}): Promise<Hospital[]> {
  const query = new URLSearchParams();
  if (options.page) query.set("page", options.page.toString());
  if (options.limit) query.set("limit", options.limit.toString());
  if (options.specialty) query.set("specialty", options.specialty);
  if (options.location) query.set("location", options.location);
  if (options.insurance) query.set("insurance", options.insurance);

  const queryString = query.toString() ? `?${query.toString()}` : "";
  return apiClient.get<Hospital[]>(`/hospitals${queryString}`, {
    timeoutMs: 15000,
    signal: options.signal,
  });
}

export async function fetchHospitalById(id: string, signal?: AbortSignal): Promise<Hospital> {
  return apiClient.get<Hospital>(`/hospitals/${id}`, {
    timeoutMs: 10000,
    signal,
  });
}

export async function fetchDoctors(specialty?: string, signal?: AbortSignal): Promise<Doctor[]> {
  const query = specialty ? `?specialty=${encodeURIComponent(specialty)}` : "";
  return apiClient.get<Doctor[]>(`/doctors${query}`, {
    timeoutMs: 10000,
    signal,
  });
}
