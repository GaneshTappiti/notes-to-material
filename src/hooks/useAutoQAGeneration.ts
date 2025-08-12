import { useState, useCallback } from 'react';
import { generate } from '@/lib/api';
import { QAPreviewItem, QuestionMarks } from '@/types/autoqa';

export interface UseAutoGenOptions {
  marks: QuestionMarks[];
  questionsPerMark: Record<QuestionMarks, number>;
  promptContext?: string; // optional extra context from UI (course / chapter info)
}

interface GenerationResult {
  preview: QAPreviewItem[];
  raw: any;
  job_id: string;
}

export function useAutoQAGeneration() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GenerationResult | null>(null);

  const runGeneration = useCallback(async (opts: UseAutoGenOptions) => {
    setIsGenerating(true);
    setProgress(5);
    setError(null);
    try {
      const parts: string[] = [];
      parts.push('Generate high-quality exam questions with multi-mark answers.');
      parts.push(`Marks to cover: ${opts.marks.join(', ')}.`);
      const counts = opts.marks.map(m => `${opts.questionsPerMark[m]} x ${m}M`).join(', ');
      parts.push(`Target counts: ${counts}.`);
      if (opts.promptContext) parts.push(`Context: ${opts.promptContext}`);
      parts.push('Each question must have answers appropriate in depth for the mark value.');
      const prompt = parts.join(' ');
      setProgress(15);
      const marksFilter = opts.marks as number[];
      const resp = await generate(prompt, 6, marksFilter);
      setProgress(70);
      const items = resp?.output?.items || [];
      const preview: QAPreviewItem[] = [];
      items.forEach((it: any) => {
        const markKeys = (['10','5','2'] as const).filter(k => it.answers && it.answers[k]);
        const primaryMark = (markKeys[0] ? parseInt(markKeys[0],10) : (opts.marks[0] || 2)) as QuestionMarks;
        preview.push({
          question_id: it.id,
            question_text: it.question,
            marks: primaryMark,
            status: (it.status as any) || 'FOUND',
            page_count: Array.isArray(it.page_references) ? it.page_references.length : 0,
            confidence_score: undefined,
        });
      });
      setResult({ preview, raw: items, job_id: resp.job_id });
      setProgress(100);
      return preview;
    } catch (e: any) {
      setError(e.message || 'Generation failed');
      setProgress(100);
      throw e;
    } finally {
      setIsGenerating(false);
    }
  }, []);

  return { isGenerating, progress, error, result, runGeneration };
}
