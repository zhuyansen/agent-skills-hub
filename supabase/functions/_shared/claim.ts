/**
 * The buyer's key, encrypted for the 24 hours it waits in order_key_claims (migration 046).
 * AES-GCM with a 256-bit key from the CLAIM_KEY secret (base64), a fresh 96-bit IV per row.
 * stripe-fulfill encrypts when it issues a key; claim-key decrypts for the buyer's success page.
 */

/** A live or test Checkout Session id, as Stripe puts it in the success URL. */
export const SESSION_ID = /^cs_(live|test)_[A-Za-z0-9]{20,100}$/;

const KEY_BYTES = 32; // AES-256
const IV_BYTES = 12; // 96-bit nonce, the AES-GCM standard size

const b64 = (bytes: Uint8Array) => btoa(String.fromCharCode(...bytes));
const unb64 = (text: string) => Uint8Array.from(atob(text), (c) => c.charCodeAt(0));

async function aesKey(secretB64: string): Promise<CryptoKey> {
  const raw = unb64(secretB64);
  if (raw.length !== KEY_BYTES) throw new Error(`CLAIM_KEY must be ${KEY_BYTES} bytes, base64`);
  return await crypto.subtle.importKey("raw", raw, "AES-GCM", false, ["encrypt", "decrypt"]);
}

export async function sealKey(plain: string, secretB64: string): Promise<{ iv: string; ciphertext: string }> {
  const iv = crypto.getRandomValues(new Uint8Array(IV_BYTES));
  const sealed = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, await aesKey(secretB64), new TextEncoder().encode(plain));
  return { iv: b64(iv), ciphertext: b64(new Uint8Array(sealed)) };
}

export async function openKey(row: { iv: string; ciphertext: string }, secretB64: string): Promise<string> {
  const plain = await crypto.subtle.decrypt({ name: "AES-GCM", iv: unb64(row.iv) }, await aesKey(secretB64), unb64(row.ciphertext));
  return new TextDecoder().decode(plain);
}
