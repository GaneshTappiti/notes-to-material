import Seo from "@/components/Seo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Switch } from "@/components/ui/switch";
import FileUploader from "@/components/FileUploader";
import { useState } from "react";
import { AutoQAJobConfig, GenerationSettings, QuestionMarks, QAPreviewItem } from "@/types/autoqa";
import AutoQAPreview from "@/components/AutoQAPreview";
import { useAutoQAGeneration } from "@/hooks/useAutoQAGeneration";
import { BookOpen, Zap } from "lucide-react";

const Step = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <Card>
    <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
    <CardContent>{children}</CardContent>
  </Card>
);

const NewJobWizard = () => {
  const [step, setStep] = useState(0); // Start with job type selection
  const [jobType, setJobType] = useState<"traditional" | "auto_qa_from_notes">("traditional");
  const [generationSettings, setGenerationSettings] = useState<GenerationSettings>({
    marks_to_generate: [2, 5, 10],
    questions_per_mark: { 2: 5, 5: 3, 10: 2 },
    mode: "per_chapter",
    include_model_problems: true,
    strict_sourcing: true,
    retrieval_threshold: 0.8,
  });
  const [previewItems, setPreviewItems] = useState<QAPreviewItem[]>([]);
  const { runGeneration, isGenerating, progress, error } = useAutoQAGeneration();
  const [generatedQuestions, setGeneratedQuestions] = useState<any[]>([]); // TODO remove if unused

  const triggerGeneration = async () => {
    try {
      const preview = await runGeneration({
        marks: generationSettings.marks_to_generate,
        questionsPerMark: generationSettings.questions_per_mark,
        promptContext: ''
      });
      setPreviewItems(preview);
    } catch {}
  };

  return (
    <div>
      <Seo title="New Job — Scollab" description="Create a study material generation job." />
      <h1 className="text-2xl font-bold mb-4">New Job</h1>

      <div className="grid grid-cols-1 md:grid-cols-6 gap-4 mb-4">
        { [
            "Job Type",
            "Course & Syllabus",
            "Upload Files",
            jobType === "auto_qa_from_notes" ? "Generation Settings" : "Processing Options",
            jobType === "auto_qa_from_notes" ? "Preview" : "Template & Branding",
            jobType === "auto_qa_from_notes" ? "Template & Branding" : "Run",
            "Run"
          ].filter((_, i, arr) => jobType === "auto_qa_from_notes" ? true : i !== 4 ).map((s, idx) => (
          <div key={s} className={`rounded-md border p-2 text-sm ${idx===step? 'elevated':''}`}>{idx+1}. {s}</div>
        ))}
      </div>

      {step === 0 && (
        <Step title="Select Job Type">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card
              className={`cursor-pointer transition-all ${jobType === "traditional" ? "ring-2 ring-primary" : ""}`}
              onClick={() => setJobType("traditional")}
            >
              <CardContent className="p-6">
                <div className="flex items-center gap-3">
                  <BookOpen className="h-8 w-8 text-primary" />
                  <div>
                    <h3 className="font-semibold">Traditional Q&A</h3>
                    <p className="text-sm text-muted-foreground">Upload notes and question banks, manually create Q&A</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card
              className={`cursor-pointer transition-all ${jobType === "auto_qa_from_notes" ? "ring-2 ring-primary" : ""}`}
              onClick={() => setJobType("auto_qa_from_notes")}
            >
              <CardContent className="p-6">
                <div className="flex items-center gap-3">
                  <Zap className="h-8 w-8 text-primary" />
                  <div>
                    <h3 className="font-semibold">Auto Q&A from Notes</h3>
                    <p className="text-sm text-muted-foreground">AI generates questions and answers from uploaded notes</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </Step>
      )}

      {step === 1 && (
        <Step title="Select Course & Syllabus">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="college">College</Label>
              <Input id="college" placeholder="Enter or pick" />
            </div>
            <div>
              <Label>Department</Label>
              <Input placeholder="e.g., CSE" />
            </div>
            <div>
              <Label>Year</Label>
              <Select><SelectTrigger><SelectValue placeholder="Select year" /></SelectTrigger><SelectContent className="dropdown-panel">{[1,2,3,4].map(y=> <SelectItem key={y} value={String(y)}>{y}</SelectItem>)}</SelectContent></Select>
            </div>
            <div>
              <Label>Course</Label>
              <Input placeholder="e.g., Data Structures" />
            </div>
          </div>
        </Step>
      )}

      {step === 2 && (
        <Step title="Upload Files">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <FileUploader label="Notes (chapter-wise)" />
            {jobType === "traditional" && <FileUploader label="Question banks" />}
          </div>
        </Step>
      )}

  {step === 3 && jobType === "auto_qa_from_notes" && (
        <Step title="Generation Settings">
          <div className="space-y-6">
            {/* Marks Selection */}
            <div>
              <Label className="text-base font-semibold">Question Marks to Generate</Label>
              <div className="flex gap-4 mt-2">
                {([2, 5, 10] as QuestionMarks[]).map((mark) => (
                  <div key={mark} className="flex items-center space-x-2">
                    <Checkbox
                      id={`mark-${mark}`}
                      checked={generationSettings.marks_to_generate.includes(mark)}
                      onCheckedChange={(checked) => {
                        if (checked) {
                          setGenerationSettings(prev => ({
                            ...prev,
                            marks_to_generate: [...prev.marks_to_generate, mark]
                          }));
                        } else {
                          setGenerationSettings(prev => ({
                            ...prev,
                            marks_to_generate: prev.marks_to_generate.filter(m => m !== mark)
                          }));
                        }
                      }}
                    />
                    <Label htmlFor={`mark-${mark}`}>{mark} Mark Questions</Label>
                  </div>
                ))}
              </div>
            </div>

            {/* Questions per Mark */}
            <div>
              <Label className="text-base font-semibold">Questions per Mark Type</Label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-2">
                {generationSettings.marks_to_generate.map((mark) => (
                  <div key={mark}>
                    <Label htmlFor={`count-${mark}`}>{mark} Mark Questions</Label>
                    <Input
                      id={`count-${mark}`}
                      type="number"
                      min="1"
                      max="20"
                      value={generationSettings.questions_per_mark[mark]}
                      onChange={(e) => {
                        const count = parseInt(e.target.value) || 1;
                        setGenerationSettings(prev => ({
                          ...prev,
                          questions_per_mark: { ...prev.questions_per_mark, [mark]: count }
                        }));
                      }}
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Generation Mode */}
            <div>
              <Label className="text-base font-semibold">Generation Mode</Label>
              <Select
                value={generationSettings.mode}
                onValueChange={(value: "per_chapter" | "entire_notes") =>
                  setGenerationSettings(prev => ({ ...prev, mode: value }))
                }
              >
                <SelectTrigger className="mt-2">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="dropdown-panel">
                  <SelectItem value="per_chapter">Per Chapter</SelectItem>
                  <SelectItem value="entire_notes">Entire Notes</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Additional Options */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-base font-semibold">Include Model Problems/Examples</Label>
                  <p className="text-sm text-muted-foreground">Generate questions based on solved examples in notes</p>
                </div>
                <Switch
                  checked={generationSettings.include_model_problems}
                  onCheckedChange={(checked) =>
                    setGenerationSettings(prev => ({ ...prev, include_model_problems: checked }))
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-base font-semibold">Strict Sourcing</Label>
                  <p className="text-sm text-muted-foreground">Only generate answers that can be fully sourced from notes</p>
                </div>
                <Switch
                  checked={generationSettings.strict_sourcing}
                  onCheckedChange={(checked) =>
                    setGenerationSettings(prev => ({ ...prev, strict_sourcing: checked }))
                  }
                />
              </div>
            </div>
          </div>
        </Step>
      )}

  {step === 3 && jobType === "traditional" && (
        <Step title="Processing Options">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>OCR language</Label>
              <Select><SelectTrigger><SelectValue placeholder="Auto-detect" /></SelectTrigger><SelectContent className="dropdown-panel"><SelectItem value="auto">Auto-detect</SelectItem><SelectItem value="en">English</SelectItem></SelectContent></Select>
            </div>
            <div>
              <Label>Retrieval strategy</Label>
              <Select><SelectTrigger><SelectValue placeholder="Page-level" /></SelectTrigger><SelectContent className="dropdown-panel"><SelectItem value="page">Page-level</SelectItem><SelectItem value="chunk">Chunk-level</SelectItem></SelectContent></Select>
            </div>
          </div>
        </Step>
      )}

      {step === 4 && jobType === "auto_qa_from_notes" && (
        <Step title="Preview & Validation">
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">This shows a live preview of generated questions before moving to export & branding.</p>
            <div className="flex gap-2">
              <Button disabled={isGenerating} onClick={triggerGeneration} variant="secondary">{previewItems.length? 'Regenerate' : 'Generate'} Questions</Button>
              <Button variant="outline" disabled={isGenerating || !previewItems.length} onClick={() => alert('Open Review Center (to implement)')}>Open Review Center</Button>
              {error && <span className="text-xs text-destructive self-center">{error}</span>}
            </div>
            <AutoQAPreview items={previewItems} isGenerating={isGenerating} progress={progress} onOpenReview={() => alert('Review Center placeholder')} />
          </div>
        </Step>
      )}

      {step === 4 && jobType === "traditional" && (
        <Step title="Template & Branding">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Template</Label>
              <Select><SelectTrigger><SelectValue placeholder="Exam-compact" /></SelectTrigger><SelectContent className="dropdown-panel"><SelectItem value="compact">Exam-compact</SelectItem><SelectItem value="detailed">Study-detailed</SelectItem></SelectContent></Select>
            </div>
            <div>
              <Label>Footer options</Label>
              <Input placeholder="Include college, faculty, date" />
            </div>
          </div>
        </Step>
      )}

      {step === 5 && jobType === "auto_qa_from_notes" && (
        <Step title="Template & Branding">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Template</Label>
              <Select><SelectTrigger><SelectValue placeholder="Exam-compact" /></SelectTrigger><SelectContent className="dropdown-panel"><SelectItem value="compact">Exam-compact</SelectItem><SelectItem value="detailed">Study-detailed</SelectItem></SelectContent></Select>
            </div>
            <div>
              <Label>Footer options</Label>
              <Input placeholder="Include college, faculty, date" />
            </div>
          </div>
        </Step>
      )}

      {step === 6 && jobType === "auto_qa_from_notes" && (
        <Step title="Run & Schedule">
          <div className="flex gap-3">
            <Button className="elevated">Run now</Button>
            <Button variant="secondary">Save as draft</Button>
          </div>
        </Step>
      )}

      {step === 5 && jobType === "traditional" && (
        <Step title="Template & Branding">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Template</Label>
              <Select><SelectTrigger><SelectValue placeholder="Exam-compact" /></SelectTrigger><SelectContent className="dropdown-panel"><SelectItem value="compact">Exam-compact</SelectItem><SelectItem value="detailed">Study-detailed</SelectItem></SelectContent></Select>
            </div>
            <div>
              <Label>Footer options</Label>
              <Input placeholder="Include college, faculty, date" />
            </div>
          </div>
        </Step>
      )}

      {step === 6 && jobType === "traditional" && (
        <Step title="Run & Schedule">
          <div className="flex gap-3">
            <Button className="elevated">Run now</Button>
            <Button variant="secondary">Save as draft</Button>
          </div>
        </Step>
      )}

      {/* Navigation */}
      {/* Simplified navigation for dynamic steps */}
      <div className="mt-6 flex justify-between">
        <Button variant="outline" disabled={step===0} onClick={() => setStep(s=> Math.max(0, s-1))}>Previous</Button>
        <Button onClick={() => setStep(s => {
          const maxStep = jobType === 'auto_qa_from_notes' ? 6 : 6; // both currently 6 index max
          return Math.min(maxStep, s+1);
        })}>{(jobType === 'auto_qa_from_notes' ? step===6 : step===6) ? 'Finish' : 'Next'}</Button>
      </div>
    </div>
  );
};

export default NewJobWizard;
