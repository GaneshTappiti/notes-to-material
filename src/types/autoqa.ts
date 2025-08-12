// Types for Auto Q&A from Notes feature

export type QuestionMarks = 2 | 5 | 10;

export type QuestionStatus = "FOUND" | "NOT_FOUND" | "NEEDS_REVIEW" | "APPROVED";

export type AnswerFormat = "concise" | "structured" | "detailed";

export interface PageReference {
  filename: string;
  page_no: number;
}

export interface VerbatimQuote {
  text: string; // ≤25 words
  source: string; // filename:page_no
}

export interface RetrievalScore {
  source: string; // filename:page_no
  score: number; // 0-1
}

export interface GenerationMetadata {
  prompt_template: string;
  model: string;
  generated_at?: string;
}

export interface GeneratedQuestion {
  question_id: string;
  question_text: string;
  marks: QuestionMarks;
  answer: string;
  answer_format: AnswerFormat;
  page_references: string[]; // ["filename.pdf:page_no"]
  diagram_images: string[]; // ["filename.pdf:page_no"]
  verbatim_quotes: string[]; // ["<=25 words — filename:page_no"]
  status: QuestionStatus;
  retrieval_scores: RetrievalScore[];
  generation_metadata: GenerationMetadata;
}

export interface CoverageReport {
  total_questions: number;
  found_count: number;
  not_found_count: number;
}

export interface AutoQAJobResult {
  job_id: string;
  course_id: string;
  generated_at: string;
  questions: GeneratedQuestion[];
  coverage_report: CoverageReport;
}

export interface GenerationSettings {
  marks_to_generate: QuestionMarks[]; // [2, 5, 10]
  questions_per_mark: Record<QuestionMarks, number>; // {2: 5, 5: 3, 10: 2}
  mode: "per_chapter" | "entire_notes";
  include_model_problems: boolean;
  strict_sourcing: boolean;
  retrieval_threshold: number; // 0-1, for auto-approval
}

export interface AutoQAJobConfig {
  job_type: "auto_qa_from_notes";
  course_info: {
    college: string;
    department: string;
    year: number;
    course: string;
  };
  generation_settings: GenerationSettings;
  processing_options: {
    ocr_language: string;
    retrieval_strategy: "page" | "chunk";
  };
  template_options: {
    template: string;
    footer_options: string;
  };
}

// Extended job stages for Auto Q&A
export interface AutoQAJobStage {
  key: string;
  label: string;
  status: "pending" | "active" | "done" | "error";
  progress?: number; // 0-100 for stages with progress
  details?: string; // Additional info like "Generated 5/10 questions"
}

export const autoQAStages: AutoQAJobStage[] = [
  { key: "upload", label: "File upload", status: "pending" },
  { key: "ocr", label: "OCR & Text Extraction", status: "pending" },
  { key: "indexing", label: "Embedding & Indexing", status: "pending" },
  { key: "question_generation", label: "Question Generation", status: "pending" },
  { key: "answer_generation", label: "Answer Generation", status: "pending" },
  { key: "validation", label: "Validation & Scoring", status: "pending" },
  { key: "ready", label: "Ready for Review", status: "pending" },
];

// For the preview component
export interface QAPreviewItem {
  question_id: string;
  question_text: string;
  marks: QuestionMarks;
  status: QuestionStatus;
  page_count: number;
  confidence_score?: number;
}
