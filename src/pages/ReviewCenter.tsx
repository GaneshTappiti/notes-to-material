import Seo from "@/components/Seo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useMemo, useState } from "react";
import { GeneratedQuestion, QuestionStatus } from "@/types/autoqa";
import { CheckCircle2, AlertCircle, Clock, FileText, Image, RotateCcw } from "lucide-react";

// Sample data for Auto Q&A questions
const sampleAutoQAQuestions: GeneratedQuestion[] = Array.from({ length: 24 }).map((_, i) => ({
  question_id: `auto-${i + 1}`,
  question_text: `Explain stack ADT with operations (Q${i + 1}).`,
  marks: [2, 5, 10][i % 3] as 2 | 5 | 10,
  answer: i % 3 === 0 ? "A stack is a linear data structure that follows LIFO principle..." : "",
  answer_format: ["concise", "structured", "detailed"][i % 3] as "concise" | "structured" | "detailed",
  page_references: i % 3 === 0 ? [`notes_ch${Math.floor(i/3) + 1}.pdf:${i + 3}`] : [],
  diagram_images: i % 4 === 0 ? [`notes_ch${Math.floor(i/4) + 1}.pdf:${i + 5}`] : [],
  verbatim_quotes: i % 3 === 0 ? [`"Stack follows LIFO principle" — notes_ch${Math.floor(i/3) + 1}.pdf:${i + 3}`] : [],
  status: ["FOUND", "NOT_FOUND", "NEEDS_REVIEW"][i % 3] as QuestionStatus,
  retrieval_scores: i % 3 === 0 ? [{ source: `notes_ch${Math.floor(i/3) + 1}.pdf:${i + 3}`, score: 0.85 + (i % 10) * 0.01 }] : [],
  generation_metadata: {
    prompt_template: "notes_gqa_v1",
    model: "gemini-1.5-pro",
    generated_at: new Date().toISOString(),
  },
}));

// Legacy sample questions for backward compatibility
const sampleQuestions = Array.from({ length: 24 }).map((_, i) => ({
  id: i + 1,
  text: `Explain stack ADT with operations (Q${i + 1}).`,
  marks: [2,5,10][i % 3],
  status: ["FOUND", "NOT_FOUND", "Needs Edit"][i % 3],
  refs: i % 3 === 0 ? 2 : 0,
}));

const ReviewCenter = () => {
  const [activeId, setActive] = useState("auto-1");
  const [viewMode, setViewMode] = useState<"auto_qa" | "traditional">("auto_qa");

  const activeAutoQA = useMemo(() =>
    sampleAutoQAQuestions.find((q) => q.question_id === activeId),
    [activeId]
  );

  const activeLegacy = useMemo(() =>
    sampleQuestions.find((q) => q.id === parseInt(activeId)),
    [activeId]
  );

  const statusIcon = (status: QuestionStatus) => {
    switch (status) {
      case "FOUND": return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case "NOT_FOUND": return <AlertCircle className="h-4 w-4 text-red-600" />;
      case "NEEDS_REVIEW": return <Clock className="h-4 w-4 text-yellow-600" />;
    }
  };

  return (
    <div className="space-y-4">
      <Seo title="Review Center — Scollab" description="Human-in-the-loop review and editing of generated answers." />

      {/* Header with mode toggle */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Review Center</h1>
        <Tabs value={viewMode} onValueChange={(value) => setViewMode(value as "auto_qa" | "traditional")}>
          <TabsList>
            <TabsTrigger value="auto_qa">Auto Q&A</TabsTrigger>
            <TabsTrigger value="traditional">Traditional</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <aside className="lg:col-span-4 border rounded-md">
          <div className="p-3 border-b flex items-center gap-2">
            <Input placeholder="Search questions" aria-label="Search questions" />
            <Select><SelectTrigger className="w-36"><SelectValue placeholder="All marks" /></SelectTrigger><SelectContent className="dropdown-panel">{["All","2","5","10"].map(m=> <SelectItem key={m} value={m}>{m}</SelectItem>)}</SelectContent></Select>
          </div>
          <ul className="max-h-[70vh] overflow-y-auto divide-y">
            {viewMode === "auto_qa" ? (
              sampleAutoQAQuestions.map((q) => (
                <li key={q.question_id} className={`p-3 cursor-pointer ${q.question_id===activeId? 'bg-secondary':''}`} onClick={() => setActive(q.question_id)}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">{q.marks}M</Badge>
                      {statusIcon(q.status)}
                    </div>
                    <Badge variant={q.status === "FOUND" ? "default" : q.status === "NOT_FOUND" ? "destructive" : "secondary"}>
                      {q.status}
                    </Badge>
                  </div>
                  <p className="text-sm font-medium truncate">{q.question_text}</p>
                  <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                    <span>{q.page_references.length} refs</span>
                    {q.retrieval_scores.length > 0 && (
                      <span>Conf: {Math.round(q.retrieval_scores[0].score * 100)}%</span>
                    )}
                  </div>
                </li>
              ))
            ) : (
              sampleQuestions.map((q) => (
                <li key={q.id} className={`p-3 cursor-pointer ${q.id===parseInt(activeId)? 'bg-secondary':''}`} onClick={() => setActive(String(q.id))}>
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium truncate">{q.text}</p>
                <span className="text-xs text-muted-foreground">{q.marks}m</span>
              </div>
              <p className="text-xs text-muted-foreground">{q.status} • {q.refs} refs</p>
            </li>
          ))}
          </ul>
        </aside>

        <section className="lg:col-span-8 grid gap-4">
          {viewMode === "auto_qa" && activeAutoQA ? (
            <>
              {/* Auto Q&A Question Editor */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{activeAutoQA.question_text}</CardTitle>
                    <div className="flex items-center gap-2">
                      {statusIcon(activeAutoQA.status)}
                      <Badge variant="secondary">{activeAutoQA.marks}M</Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div>
                      <Label>Marks</Label>
                      <Select defaultValue={String(activeAutoQA.marks)}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent className="dropdown-panel">
                          {[2,5,10].map(m => <SelectItem key={m} value={String(m)}>{m}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Status</Label>
                      <Select defaultValue={activeAutoQA.status}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent className="dropdown-panel">
                          {["FOUND","NOT_FOUND","NEEDS_REVIEW"].map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Confidence</Label>
                      <div className="flex items-center gap-2 mt-2">
                        {activeAutoQA.retrieval_scores.length > 0 && (
                          <Badge variant="outline">
                            {Math.round(activeAutoQA.retrieval_scores[0].score * 100)}%
                          </Badge>
                        )}
                        <Button variant="ghost" size="sm">
                          <RotateCcw className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>

                  <Tabs defaultValue="answer" className="w-full">
                    <TabsList>
                      <TabsTrigger value="answer">Answer</TabsTrigger>
                      <TabsTrigger value="sources">Sources</TabsTrigger>
                      <TabsTrigger value="metadata">Metadata</TabsTrigger>
                    </TabsList>

                    <TabsContent value="answer" className="space-y-3">
                      <div>
                        <Label htmlFor="question-editor">Question Text</Label>
                        <textarea
                          id="question-editor"
                          className="mt-1 w-full min-h-[80px] rounded-md border bg-background p-3 text-sm"
                          defaultValue={activeAutoQA.question_text}
                        />
                      </div>
                      <div>
                        <Label htmlFor="answer-editor">Answer</Label>
                        <textarea
                          id="answer-editor"
                          className="mt-1 w-full min-h-[240px] rounded-md border bg-background p-3 text-sm"
                          defaultValue={activeAutoQA.answer}
                          placeholder="Generated answer will appear here..."
                        />
                        <p className="mt-1 text-xs text-muted-foreground">
                          Format: {activeAutoQA.answer_format} • Tip: Press Ctrl/Cmd+S to save quickly
                        </p>
                      </div>
                    </TabsContent>

                    <TabsContent value="sources" className="space-y-3">
                      <div>
                        <Label className="text-base font-semibold">Page References</Label>
                        <div className="mt-2 space-y-2">
                          {activeAutoQA.page_references.map((ref, idx) => (
                            <div key={idx} className="flex items-center gap-2 p-2 border rounded">
                              <FileText className="h-4 w-4" />
                              <span className="text-sm">{ref}</span>
                              <Button variant="ghost" size="sm">View</Button>
                            </div>
                          ))}
                          {activeAutoQA.page_references.length === 0 && (
                            <p className="text-sm text-muted-foreground">No page references found</p>
                          )}
                        </div>
                      </div>

                      <div>
                        <Label className="text-base font-semibold">Diagram Images</Label>
                        <div className="mt-2 space-y-2">
                          {activeAutoQA.diagram_images.map((img, idx) => (
                            <div key={idx} className="flex items-center gap-2 p-2 border rounded">
                              <Image className="h-4 w-4" />
                              <span className="text-sm">{img}</span>
                              <Button variant="ghost" size="sm">Insert</Button>
                            </div>
                          ))}
                          {activeAutoQA.diagram_images.length === 0 && (
                            <p className="text-sm text-muted-foreground">No diagrams found</p>
                          )}
                        </div>
                      </div>

                      <div>
                        <Label className="text-base font-semibold">Verbatim Quotes</Label>
                        <div className="mt-2 space-y-2">
                          {activeAutoQA.verbatim_quotes.map((quote, idx) => (
                            <div key={idx} className="p-2 border rounded bg-muted/50">
                              <p className="text-sm italic">"{quote.split(' — ')[0]}"</p>
                              <p className="text-xs text-muted-foreground mt-1">{quote.split(' — ')[1]}</p>
                            </div>
                          ))}
                          {activeAutoQA.verbatim_quotes.length === 0 && (
                            <p className="text-sm text-muted-foreground">No verbatim quotes</p>
                          )}
                        </div>
                      </div>
                    </TabsContent>

                    <TabsContent value="metadata" className="space-y-3">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <Label>Model Used</Label>
                          <p className="text-sm mt-1">{activeAutoQA.generation_metadata.model}</p>
                        </div>
                        <div>
                          <Label>Prompt Template</Label>
                          <p className="text-sm mt-1">{activeAutoQA.generation_metadata.prompt_template}</p>
                        </div>
                        <div>
                          <Label>Generated At</Label>
                          <p className="text-sm mt-1">{new Date(activeAutoQA.generation_metadata.generated_at || "").toLocaleString()}</p>
                        </div>
                        <div>
                          <Label>Retrieval Scores</Label>
                          <div className="mt-1 space-y-1">
                            {activeAutoQA.retrieval_scores.map((score, idx) => (
                              <div key={idx} className="text-xs">
                                <span className="font-mono">{score.source}</span>: {Math.round(score.score * 100)}%
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </TabsContent>
                  </Tabs>

                  <div className="flex gap-2">
                    <Button className="elevated">Approve</Button>
                    <Button variant="secondary">Save</Button>
                    <Button variant="outline">Regenerate</Button>
                    <Button variant="outline">Flag for faculty</Button>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : activeLegacy ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">{activeLegacy.text}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div>
                    <Label>Marks</Label>
                    <Select defaultValue={String(activeLegacy.marks)}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent className="dropdown-panel">{[2,5,10].map(m => <SelectItem key={m} value={String(m)}>{m}</SelectItem>)}</SelectContent></Select>
                  </div>
                  <div>
                    <Label>Status</Label>
                    <Select defaultValue="FOUND"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent className="dropdown-panel">{["FOUND","NOT_FOUND","Needs Edit"].map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent></Select>
                  </div>
                </div>

                <div>
                  <Label htmlFor="editor">Answer</Label>
                  <textarea id="editor" className="mt-1 w-full min-h-[240px] rounded-md border bg-background p-3 text-sm" placeholder="Write or edit the generated answer. Use references and insert diagrams." />
                  <p className="mt-1 text-xs text-muted-foreground">Tip: Select text and press Ctrl/Cmd+S to save quickly.</p>
                </div>

                <div className="flex gap-2">
                  <Button className="elevated">Approve</Button>
                  <Button variant="secondary">Save</Button>
                  <Button variant="outline">Flag for faculty</Button>
                </div>
              </CardContent>
            </Card>
          ) : null}

          {/* Legacy Sources Panel for Traditional Mode */}
          {viewMode === "traditional" && (
            <Card>
              <CardHeader><CardTitle>Sources & Page references</CardTitle></CardHeader>
              <CardContent>
                <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {[1,2,3,4].map(p => (
                    <li key={p} className="rounded-md border p-3">
                      <p className="text-sm font-medium">notes.pdf : page {p}</p>
                      <p className="text-xs text-muted-foreground line-clamp-3">Lorem ipsum excerpt of OCR text from the page that can be cited...</p>
                      <div className="mt-2 flex gap-2">
                        <Button size="sm" variant="secondary">Insert text</Button>
                        <Button size="sm" variant="outline">Insert diagram</Button>
                      </div>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </section>
      </div>
    </div>
  );
};

export default ReviewCenter;
