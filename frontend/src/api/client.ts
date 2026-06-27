import { getCurrentLanguage } from "../i18n";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

const BASE_URL = import.meta.env.VITE_API_URL ?? "";

export interface RequestOptions extends RequestInit {
  timeoutMs?: number;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { timeoutMs = 30000, ...fetchOptions } = options;
  const headers = new Headers(fetchOptions.headers);
  headers.set("Accept-Language", getCurrentLanguage());

  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${BASE_URL}${path}`, {
      ...fetchOptions,
      headers,
      signal: controller.signal,
    });
    if (!response.ok) {
      let detail = response.statusText;
      try {
        const body = await response.json();
        detail = body.detail ?? detail;
      } catch {
        // ignore
      }
      throw new ApiError(detail, response.status);
    }
    if (response.status === 204) {
      return undefined as T;
    }
    return response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError(
        "Request timed out. The server may be busy or not running — check that the backend is started on port 8002.",
        0
      );
    }
    if (error instanceof TypeError) {
      throw new ApiError(
        "Cannot reach the server. Make sure the backend is running (uvicorn on port 8002).",
        0
      );
    }
    throw error;
  } finally {
    window.clearTimeout(timer);
  }
}

export const apiClient = { request };
