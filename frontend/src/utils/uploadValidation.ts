/** Shared file upload validation utilities for 问津.
 *
 * Provides consistent client-side pre-checks so users get instant feedback
 * before a large/unexpected file hits the network.
 */

export interface UploadLimits {
  maxSize: number;       // bytes
  extensions: string[];  // e.g. [".wav", ".mp3"]
  mimeTypes: string[];   // e.g. ["audio/*", "video/*"]
}

export interface ValidationResult {
  ok: boolean;
  reason?: string;       // Human-readable error (Chinese)
  sizeMB: number;
}

/** Pre-defined limits matching backend constraints */
export const LIMITS: Record<string, UploadLimits> = {
  image: {
    maxSize: 10 * 1024 * 1024,
    extensions: [".jpg", ".jpeg", ".png", ".webp"],
    mimeTypes: ["image/jpeg", "image/png", "image/webp"],
  },
  audio: {
    maxSize: 500 * 1024 * 1024,
    extensions: [".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac", ".opus", ".webm"],
    mimeTypes: ["audio/*", "video/*"],
  },
  reference: {
    maxSize: 10 * 1024 * 1024,
    extensions: [".txt", ".md", ".docx", ".pdf"],
    mimeTypes: [
      "text/plain",
      "text/markdown",
      "text/x-markdown",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "application/pdf",
    ],
  },
};

/** Format a byte count as a human-readable string in Chinese units */
export function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

/** Check whether a MIME type matches an accept pattern like "audio/*" or "image/png" */
function mimeMatches(mime: string, pattern: string): boolean {
  if (pattern.endsWith("/*")) {
    const prefix = pattern.slice(0, -1);
    return mime.startsWith(prefix);
  }
  return mime === pattern;
}

/** Validate a File object against a limits preset.
 *
 * Returns { ok: true } or { ok: false, reason: "..." }.
 * The reason is already in Chinese so the caller can display it directly.
 */
export function validateFile(
  file: File,
  limitsKey: keyof typeof LIMITS,
): ValidationResult {
  const limits = LIMITS[limitsKey];
  const sizeMB = file.size / (1024 * 1024);

  if (file.size > limits.maxSize) {
    return {
      ok: false,
      sizeMB: Math.round(sizeMB * 10) / 10,
      reason: `文件过大（${formatSize(file.size)}），最大允许 ${formatSize(limits.maxSize)}`,
    };
  }

  if (file.size === 0) {
    return { ok: false, sizeMB: 0, reason: "文件为空，请重新选择" };
  }

  const fileName = file.name.toLowerCase();
  const ext = fileName.includes(".") ? `.${fileName.split(".").pop()}` : "";
  const extOk = limits.extensions.some((e) => ext === e.toLowerCase());
  if (!extOk && limits.extensions.length > 0) {
    return {
      ok: false,
      sizeMB: Math.round(sizeMB * 10) / 10,
      reason: `不支持的格式 "${ext || "未知"}"，支持：${limits.extensions.join(", ")}`,
    };
  }

  if (limits.mimeTypes.length > 0 && file.type) {
    const mimeOk = limits.mimeTypes.some((p) => mimeMatches(file.type, p));
    if (!mimeOk && !limits.mimeTypes.includes("*/*")) {
      console.warn(
        `[uploadValidation] MIME "${file.type}" doesn't match expected for "${file.name}" — allowing on extension check`,
      );
    }
  }

  return { ok: true, sizeMB: Math.round(sizeMB * 10) / 10 };
}
