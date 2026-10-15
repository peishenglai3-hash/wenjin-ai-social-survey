/**
 * XSS-safe HTML rendering utility.
 *
 * Converts basic markdown to HTML and sanitizes with DOMPurify
 * to prevent XSS from AI-generated or user-supplied content.
 */
import DOMPurify from "dompurify";

/** Minimal markdown → HTML conversion, then sanitize. */
export function renderMarkdown(text: string): string {
  const html = text
    .replace(/### /g, "<h4>")
    .replace(/## /g, "<h3>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/- /g, "· ")
    .replace(/\n/g, "<br/>");

  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ["h3", "h4", "strong", "em", "br", "p", "ul", "ol", "li", "a", "code", "pre", "blockquote"],
    ALLOWED_ATTR: ["href", "target", "rel"],
  });
}

/** Sanitize raw HTML (e.g. CAPTCHA SVG from backend). */
export function sanitizeHtml(html: string): string {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ["svg", "path", "circle", "rect", "line", "text", "g", "defs", "filter", "feFlood", "feColorMatrix", "feBlend", "feComposite"],
    ALLOWED_ATTR: ["d", "fill", "stroke", "stroke-width", "cx", "cy", "r", "x", "y", "width", "height", "viewBox", "xmlns", "font-size", "text-anchor", "dominant-baseline", "transform", "opacity"],
  });
}

/** Convenience: returns { __html: string } for dangerouslySetInnerHTML. */
export function safeHtml(text: string): { __html: string } {
  return { __html: renderMarkdown(text) };
}
