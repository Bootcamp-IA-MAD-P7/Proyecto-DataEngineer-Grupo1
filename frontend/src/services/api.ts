import type {
  StatisticsResult, PersonSearchResult,
} from "../types/api";

export class ApiUnavailableError extends Error {}
export class ApiRequestError extends Error {
  constructor(public status: number, message: string) { super(message); }
}
const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8123";

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, { signal });
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") throw e;
    throw new ApiUnavailableError("Cannot reach the API.");
  }
  if (res.status === 503) throw new ApiUnavailableError("API reports unavailable.");
  if (!res.ok) {
    let detail = `API error ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch { /* keep default */ }
    throw new ApiRequestError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export interface IdentityFilters { id?: number; passport?: string;
  first_name?: string; last_name?: string; }
export interface LocationFilters { city?: string; address?: string;
  job?: string; company?: string; }

function qs(params: Record<string, string | number | undefined>,
            limit: number, offset: number): string {
  const sp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== "" &&
        !(typeof v === "number" && Number.isNaN(v))) sp.set(k, String(v));
  });
  sp.set("limit", String(Math.min(Math.max(limit, 1), 100)));
  sp.set("offset", String(Math.max(offset, 0)));
  return sp.toString();
}

export const getHealth = (signal?: AbortSignal) =>
  request<{ status: string }>("/health", signal);
export const getStatistics = (signal?: AbortSignal) =>
  request<StatisticsResult>("/statistics", signal);
export const searchPeople = (f: IdentityFilters, limit = 20, offset = 0,
  signal?: AbortSignal) =>
  request<PersonSearchResult[]>(
    `/people/search?${qs({ ...f }, limit, offset)}`, signal);
export const searchByLocationProfession = (f: LocationFilters, limit = 20,
  offset = 0, signal?: AbortSignal) =>
  request<PersonSearchResult[]>(
    `/people/search/by-location-profession?${qs({ ...f }, limit, offset)}`,
    signal);

export async function getPersonById(id: number,
  signal?: AbortSignal): Promise<PersonSearchResult | null> {
  const rows = await searchPeople({ id }, 1, 0, signal);
  return rows.length > 0 ? rows[0]! : null;
}

export async function searchAll(identity: IdentityFilters,
  location: LocationFilters, limit = 20, offset = 0,
  signal?: AbortSignal): Promise<PersonSearchResult[]> {
  const [a, b] = await Promise.all([
    searchPeople(identity, limit, offset, signal),
    searchByLocationProfession(location, limit, offset, signal),
  ]);
  const idsA = new Set(a.map((p) => p.id));
  return b.filter((p) => idsA.has(p.id));
}
