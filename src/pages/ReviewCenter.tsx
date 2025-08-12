import Seo from "@/components/Seo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useMemo, useState } from "react";

const sampleQuestions = Array.from({ length: 24 }).map((_, i) => ({
  id: i + 1,
  text: `Explain stack ADT with operations (Q${i + 1}).`,
  marks: [2,5,10][i % 3],
  status: ["FOUND", "NOT_FOUND", "Needs Edit"][i % 3],
  refs: i % 3 === 0 ? 2 : 0,
}));

const ReviewCenter = () => {
  const [activeId, setActive] = useState(1);
  const active = useMemo(() => sampleQuestions.find((q) => q.id === activeId)!, [activeId]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
      <Seo title="Review Center — Scollab" description="Human-in-the-loop review and editing of generated answers." />
      <h1 className="sr-only">Review Center</h1>

      <aside className="lg:col-span-4 border rounded-md">
        <div className="p-3 border-b flex items-center gap-2">
          <Input placeholder="Search questions" aria-label="Search questions" />
          <Select><SelectTrigger className="w-36"><SelectValue placeholder="All marks" /></SelectTrigger><SelectContent>{["All","2","5","10"].map(m=> <SelectItem key={m} value={m}>{m}</SelectItem>)}</SelectContent></Select>
        </div>
        <ul className="max-h-[70vh] overflow-y-auto divide-y">
          {sampleQuestions.map((q) => (
            <li key={q.id} className={`p-3 cursor-pointer ${q.id===activeId? 'bg-secondary':''}`} onClick={() => setActive(q.id)}>
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
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">{active.text}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <Label>Marks</Label>
                <Select defaultValue={String(active.marks)}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{[2,5,10].map(m => <SelectItem key={m} value={String(m)}>{m}</SelectItem>)}</SelectContent></Select>
              </div>
              <div>
                <Label>Status</Label>
                <Select defaultValue="FOUND"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{["FOUND","NOT_FOUND","Needs Edit"].map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent></Select>
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
      </section>
    </div>
  );
};

export default ReviewCenter;
