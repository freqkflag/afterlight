/**
 * Client-side vault crypto (Web Crypto).
 * Master password never leaves the browser.
 */

const PBKDF2_ITERATIONS = 310_000;
const DEK_BYTES = 32;
const DEK_SESSION_KEY = "afterlight_dek_session";

function toBase64(bytes: ArrayBuffer | Uint8Array): string {
  const arr = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  let binary = "";
  for (let i = 0; i < arr.length; i++) binary += String.fromCharCode(arr[i]!);
  return btoa(binary);
}

function fromBase64(value: string): Uint8Array<ArrayBuffer> {
  const binary = atob(value);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

function asBufferSource(bytes: Uint8Array): BufferSource {
  return bytes as BufferSource;
}

async function deriveKek(
  password: string,
  saltB64: string,
): Promise<CryptoKey> {
  const baseKey = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(password),
    "PBKDF2",
    false,
    ["deriveKey"],
  );
  return crypto.subtle.deriveKey(
    {
      name: "PBKDF2",
      salt: asBufferSource(fromBase64(saltB64)),
      iterations: PBKDF2_ITERATIONS,
      hash: "SHA-256",
    },
    baseKey,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"],
  );
}

async function importAesKey(
  raw: Uint8Array,
  extractable = false,
): Promise<CryptoKey> {
  return crypto.subtle.importKey(
    "raw",
    asBufferSource(raw),
    { name: "AES-GCM" },
    extractable,
    ["encrypt", "decrypt"],
  );
}

export async function createKeyBundle(
  masterPassword: string,
  saltB64: string,
): Promise<{ bundleJson: string; dek: CryptoKey }> {
  const kek = await deriveKek(masterPassword, saltB64);
  const dekBytes = crypto.getRandomValues(new Uint8Array(DEK_BYTES));
  const nonce = crypto.getRandomValues(new Uint8Array(12));
  const wrapped = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv: nonce },
    kek,
    dekBytes,
  );
  const bundleJson = JSON.stringify({
    version: 1,
    alg: "AES-GCM",
    kdf: "PBKDF2-SHA256",
    iterations: PBKDF2_ITERATIONS,
    nonce: toBase64(nonce),
    wrapped_dek: toBase64(wrapped),
  });
  const dek = await importAesKey(dekBytes, true);
  return { bundleJson, dek };
}

export async function unlockDek(
  masterPassword: string,
  saltB64: string,
  bundleJson: string,
): Promise<CryptoKey> {
  const bundle = JSON.parse(bundleJson) as {
    nonce: string;
    wrapped_dek: string;
  };
  const kek = await deriveKek(masterPassword, saltB64);
  const raw = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: asBufferSource(fromBase64(bundle.nonce)) },
    kek,
    asBufferSource(fromBase64(bundle.wrapped_dek)),
  );
  return importAesKey(new Uint8Array(raw), true);
}

export async function encryptSecret(
  dek: CryptoKey,
  plaintext: string,
): Promise<{ encrypted_data: string; nonce: string }> {
  const nonce = crypto.getRandomValues(new Uint8Array(12));
  const cipher = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv: nonce },
    dek,
    new TextEncoder().encode(plaintext),
  );
  return { encrypted_data: toBase64(cipher), nonce: toBase64(nonce) };
}

export async function decryptSecret(
  dek: CryptoKey,
  encryptedData: string,
  nonce: string,
): Promise<string> {
  const plain = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: asBufferSource(fromBase64(nonce)) },
    dek,
    asBufferSource(fromBase64(encryptedData)),
  );
  return new TextDecoder().decode(plain);
}

export async function cacheDek(dek: CryptoKey): Promise<void> {
  const raw = await crypto.subtle.exportKey("raw", dek);
  sessionStorage.setItem(DEK_SESSION_KEY, toBase64(raw));
}

export async function loadCachedDek(): Promise<CryptoKey | null> {
  const b64 = sessionStorage.getItem(DEK_SESSION_KEY);
  if (!b64) return null;
  return importAesKey(fromBase64(b64), true);
}

export function clearCachedDek(): void {
  sessionStorage.removeItem(DEK_SESSION_KEY);
}
