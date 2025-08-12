// Placeholder backend-like logic for Auto Q&A generation (front-end mock)
// This simulates generation using the JSON schema defined in types/autoqa.ts
// Real implementation would call a backend service that performs OCR, embeddings, retrieval, and model generation.

import { GeneratedQuestion, QuestionMarks, QuestionStatus, QAPreviewItem } from "@/types/autoqa";

// Deterministic mock generator for UI development without backend/API keys.
export function mockGenerateQuestions(options: {
  marks: QuestionMarks[];
  questionsPerMark: Record<QuestionMarks, number>;
}): { questions: GeneratedQuestion[]; preview: QAPreviewItem[] } {
  const questions: GeneratedQuestion[] = [];
  const preview: QAPreviewItem[] = [];
  const now = new Date().toISOString();

  options.marks.forEach(mark => {
    for (let i = 0; i < options.questionsPerMark[mark]; i++) {
      const id = `auto:${mark}-${i}-${Date.now()}`;
      const status: QuestionStatus = i % 5 === 0 ? "NOT_FOUND" : (i % 3 === 0 ? "NEEDS_REVIEW" : "FOUND");
      const pageRefs = status === "NOT_FOUND" ? [] : ["notes_ch1.pdf:3"]; // simple
      const q: GeneratedQuestion = {
        question_id: id,
        question_text: `Sample ${mark}M question ${i+1}`,
        marks: mark,
        answer: status === "NOT_FOUND" ? "" : `Sample answer for a ${mark} mark question derived from notes page 3.`,
        answer_format: mark === 2 ? "concise" : mark === 5 ? "structured" : "detailed",
        page_references: pageRefs,
        diagram_images: [],
        verbatim_quotes: pageRefs.length ? ["Definition of X — notes_ch1.pdf:3"] : [],
        status,
        retrieval_scores: pageRefs.map(p => ({ source: p, score: 0.82 })),
        generation_metadata: { prompt_template: "notes_gqa_v1", model: "gemini-1.5-pro", generated_at: now }
      };
      questions.push(q);
      preview.push({
        question_id: q.question_id,
        question_text: q.question_text,
        marks: q.marks,
        status: q.status,
        page_count: q.page_references.length,
        confidence_score: q.retrieval_scores[0]?.score
      });
    }
  });

  return { questions, preview };
}
