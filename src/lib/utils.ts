import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Trim text to maxChars, ending at a sentence boundary (., !, ?) if possible.
// Falls back to nearest word boundary and adds ellipsis if truncated.
export function trimToSentence(text: string, maxChars: number): string {
  if (text.length <= maxChars) return text;
  const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
  let out = '';
  for (const s of sentences) {
    if ((out + s).length > maxChars) break;
    out += s.trim() + ' ';
  }
  out = out.trim();
  if (!out) {
    // fallback: trim to last space before maxChars
    const slice = text.slice(0, maxChars - 1);
    const lastSpace = slice.lastIndexOf(' ');
    return (lastSpace > 40 ? slice.slice(0, lastSpace) : slice).trim() + '…';
  }
  if (out.length < text.length) return out + '…';
  return out;
}
