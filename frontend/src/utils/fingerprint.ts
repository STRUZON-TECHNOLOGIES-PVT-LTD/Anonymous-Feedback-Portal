import type { DeviceInfo } from "../api/types";

/**
 * Collects only what a browser actually exposes to a web page: user-agent,
 * screen size, timezone, language, and a canvas-rendering-based hash. There is
 * no browser API that reveals OS username, computer name, or MAC address to a
 * website - none of the major browsers expose that, on any OS, to any site.
 */
export function collectDeviceInfo(): DeviceInfo {
  return {
    user_agent: navigator.userAgent,
    platform: navigator.platform || undefined,
    screen_resolution: `${screen.width}x${screen.height}`,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    language: navigator.language,
    fingerprint_hash: canvasFingerprint(),
  };
}

/** A coarse, non-invasive device signature (not full-strength browser fingerprinting) used only to flag repeat submissions from the same device in admin stats. */
function canvasFingerprint(): string {
  try {
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    if (!ctx) return "";

    ctx.textBaseline = "top";
    ctx.font = "14px 'Arial'";
    ctx.fillText("feedback-portal-fp", 2, 2);

    const raw = [
      canvas.toDataURL(),
      navigator.userAgent,
      screen.width,
      screen.height,
      screen.colorDepth,
      Intl.DateTimeFormat().resolvedOptions().timeZone,
      navigator.language,
      navigator.hardwareConcurrency,
    ].join("|");

    return simpleHash(raw);
  } catch {
    return "";
  }
}

function simpleHash(input: string): string {
  let hash = 0;
  for (let i = 0; i < input.length; i++) {
    hash = (hash << 5) - hash + input.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash).toString(16);
}
