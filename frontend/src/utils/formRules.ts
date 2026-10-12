const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const CREDENTIAL_RE =
  /(?:^|[^a-z])(?:password_hash|password-hash|private_key|private-key|api_key|api-key|password|secret|token|credential)(?![a-z])/i;

export function hasText(value: string | null | undefined): boolean {
  return Boolean(value && value.trim());
}

export function isEmail(value: string): boolean {
  return EMAIL_RE.test(value.trim());
}

export function containsCredential(value: string | null | undefined): boolean {
  return CREDENTIAL_RE.test(value || "");
}

export function endBeforeStart(start: string | null | undefined, end: string | null | undefined): boolean {
  if (!start || !end) return false;
  return end < start;
}

export function amountScale(value: string | null | undefined): bigint | null {
  const text = (value || "").trim();
  if (!/^-?\d+(\.\d+)?$/.test(text)) return null;
  const negative = text.startsWith("-");
  const raw = negative ? text.slice(1) : text;
  const [whole, fraction = ""] = raw.split(".");
  const scaled = BigInt(whole || "0") * 10000n + BigInt((fraction + "0000").slice(0, 4));
  return negative ? -scaled : scaled;
}
