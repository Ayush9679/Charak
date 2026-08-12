import { APIErrorResponse } from "./types";

const getBaseUrl = (): string => {
  const envUrl = import.meta.env["VITE_API_BASE_URL"] as string | undefined;
  // Production requests stay same-origin and are forwarded by the deployment
  // proxy. The development fallback intentionally targets only the local API.
  if (!envUrl) return import.meta.env.DEV ? "http://127.0.0.1:8000" : "/api";
  return envUrl.replace(/\/+$/, "");
};

const BASE_URL = getBaseUrl();

export interface RequestOptions {
  timeoutMs?: number | undefined;
  headers?: Record<string, string> | undefined;
  signal?: AbortSignal | undefined;
}

export class APIError extends Error {
  code: string;
  status?: number | undefined;
  details?: unknown;

  constructor(message: string, code: string = "API_ERROR", status?: number | undefined, details?: unknown) {
    super(message);
    this.name = "APIError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

async function request<T>(
  path: string,
  method: string,
  body?: unknown,
  options: RequestOptions = {}
): Promise<T> {
  const timeoutMs = options.timeoutMs ?? 20000; // Default 20s
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  const fullUrl = `${BASE_URL}${cleanPath}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  // Combine caller signal and timeout controller if needed
  if (options.signal) {
    options.signal.addEventListener("abort", () => controller.abort());
  }

  const isFormData = body instanceof FormData;
  const headers: Record<string, string> = {
    ...options.headers,
  };

  if (!isFormData && body !== undefined && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  if (import.meta.env.DEV) {
    console.log(`[CHANAKYA API] ${method} ${fullUrl}`);
  }

  const startTime = Date.now();

  try {
    const fetchInit: RequestInit = {
      method,
      headers,
      signal: controller.signal,
    };
    if (isFormData) {
      fetchInit.body = body as FormData;
    } else if (body !== undefined) {
      fetchInit.body = JSON.stringify(body);
    }

    const response = await fetch(fullUrl, fetchInit);

    clearTimeout(timeoutId);

    const duration = Date.now() - startTime;
    if (import.meta.env.DEV) {
      console.log(`[CHANAKYA API] ${method} ${fullUrl} ${response.status} (${duration}ms)`);
    }

    if (!response.ok) {
      let errorData: APIErrorResponse | null = null;
      try {
        errorData = await response.json();
      } catch {
        // Non-JSON response error
      }

      const code = errorData?.code || getErrorCodeForStatus(response.status);
      const message = errorData?.message || getErrorMessageForStatus(response.status);
      throw new APIError(message, code, response.status, errorData?.details);
    }

    // Handle empty 204 response
    if (response.status === 204) {
      return {} as T;
    }

    return (await response.json()) as T;
  } catch (err: unknown) {
    clearTimeout(timeoutId);

    if (err instanceof APIError) {
      throw err;
    }

    if (err instanceof DOMException && err.name === "AbortError") {
      if (import.meta.env.DEV) {
        console.error(`[CHANAKYA API ERROR] ${method} ${fullUrl} - TIMEOUT (${timeoutMs}ms)`);
      }
      throw new APIError(
        "The server took too long to respond. Please try again.",
        "REQUEST_TIMEOUT"
      );
    }

    if (import.meta.env.DEV) {
      console.error(`[CHANAKYA API ERROR] ${method} ${fullUrl} - NETWORK_ERROR`, err);
    }

    throw new APIError(
      BASE_URL === "/api"
        ? "Unable to reach the CHANAKYA backend through /api. Please try again."
        : "Unable to reach the CHANAKYA backend. Please ensure the backend is running.",
      "NETWORK_ERROR"
    );
  }
}

function getErrorCodeForStatus(status: number): string {
  switch (status) {
    case 404:
      return "NOT_FOUND";
    case 422:
      return "INVALID_REQUEST";
    case 429:
      return "RATE_LIMITED";
    case 500:
      return "SERVER_ERROR";
    case 503:
      return "SERVICE_UNAVAILABLE";
    default:
      return "HTTP_ERROR";
  }
}

function getErrorMessageForStatus(status: number): string {
  switch (status) {
    case 404:
      return "Requested resource was not found.";
    case 422:
      return "Invalid request data.";
    case 429:
      return "Too many requests. Please wait a moment.";
    case 500:
      return "Internal server error occurred.";
    case 503:
      return "Service is temporarily unavailable.";
    default:
      return `Request failed with status ${status}.`;
  }
}

export const apiClient = {
  get: <T>(path: string, options?: RequestOptions) => request<T>(path, "GET", undefined, options),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, "POST", body, options),
  delete: <T>(path: string, options?: RequestOptions) => request<T>(path, "DELETE", undefined, options),
  upload: <T>(path: string, formData: FormData, options?: RequestOptions) =>
    request<T>(path, "POST", formData, options),
};
