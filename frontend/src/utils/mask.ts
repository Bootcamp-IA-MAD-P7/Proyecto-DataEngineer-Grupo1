import type { PersonSearchResult } from "../types/api";

export function maskTail(s: string, keep = 3): string {
  const clean = s.trim();
  if (clean.length <= keep) return "*".repeat(clean.length);
  return "*".repeat(clean.length - keep) + clean.slice(-keep);
}
export const maskPassport = (s: string) => maskTail(s, 3);
export const maskPhone = (s: string) => maskTail(s, 3);
export function maskEmail(s: string): string {
  const [local, domain] = s.split("@");
  if (!local || !domain) return maskTail(s, 2);
  return `${local[0]}***@${domain}`;
}
export function maskIp(s: string): string {
  const parts = s.split(".");
  return parts.length === 4 ? `${parts[0]}.${parts[1]}.x.x`
    : "*".repeat(s.length);
}
export function domainCompleteness(p: PersonSearchResult): number {
  const has = [
    Boolean(p.first_name && p.last_name),
    Boolean(p.email || p.telephone_number),
    p.locations.length > 0,
    p.professional_profiles.length > 0,
  ];
  return has.filter(Boolean).length;
}
