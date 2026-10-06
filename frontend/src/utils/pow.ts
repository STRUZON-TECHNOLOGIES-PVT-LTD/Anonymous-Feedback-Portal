import type { PowChallenge, PowSolution } from "../api/types";

function leadingZeroBits(bytes: Uint8Array): number {
  let bits = 0;
  for (const b of bytes) {
    if (b === 0) {
      bits += 8;
      continue;
    }
    bits += Math.clz32(b) - 24;
    break;
  }
  return bits;
}

/** Finds a nonce so sha256(salt + nonce) has `bits` leading zero bits. Runs in batches so the UI stays responsive. */
export async function solvePow(c: PowChallenge): Promise<PowSolution> {
  const enc = new TextEncoder();
  const BATCH = 512;
  for (let start = 0; ; start += BATCH) {
    const nonces = Array.from({ length: BATCH }, (_, i) => String(start + i));
    const digests = await Promise.all(nonces.map((n) => crypto.subtle.digest("SHA-256", enc.encode(c.salt + n))));
    for (let i = 0; i < BATCH; i++) {
      if (leadingZeroBits(new Uint8Array(digests[i])) >= c.bits) {
        return { ...c, nonce: nonces[i] };
      }
    }
    await new Promise((r) => setTimeout(r, 0));
  }
}
