import Seo from "@/components/Seo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import FileUploader from "@/components/FileUploader";
import { useState } from "react";

const Step = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <Card>
    <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
    <CardContent>{children}</CardContent>
  </Card>
);

const NewJobWizard = () => {
  const [step, setStep] = useState(1);

  return (
    <div>
      <Seo title="New Job — Scollab" description="Create a study material generation job." />
      <h1 className="text-2xl font-bold mb-4">New Job</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
        {["Course & Syllabus","Upload Files","Processing Options","Template & Branding","Run"].map((s, idx) => (
          <div key={s} className={`rounded-md border p-2 text-sm ${idx+1===step? 'elevated':''}`}>{idx+1}. {s}</div>
        ))}
      </div>

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
              <Select><SelectTrigger><SelectValue placeholder="Select year" /></SelectTrigger><SelectContent>{[1,2,3,4].map(y=> <SelectItem key={y} value={String(y)}>{y}</SelectItem>)}</SelectContent></Select>
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
            <FileUploader label="Question banks" />
          </div>
        </Step>
      )}

      {step === 3 && (
        <Step title="Processing Options">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>OCR language</Label>
              <Select><SelectTrigger><SelectValue placeholder="Auto-detect" /></SelectTrigger><SelectContent><SelectItem value="auto">Auto-detect</SelectItem><SelectItem value="en">English</SelectItem></SelectContent></Select>
            </div>
            <div>
              <Label>Retrieval strategy</Label>
              <Select><SelectTrigger><SelectValue placeholder="Page-level" /></SelectTrigger><SelectContent><SelectItem value="page">Page-level</SelectItem><SelectItem value="chunk">Chunk-level</SelectItem></SelectContent></Select>
            </div>
          </div>
        </Step>
      )}

      {step === 4 && (
        <Step title="Template & Branding">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Template</Label>
              <Select><SelectTrigger><SelectValue placeholder="Exam-compact" /></SelectTrigger><SelectContent><SelectItem value="compact">Exam-compact</SelectItem><SelectItem value="detailed">Study-detailed</SelectItem></SelectContent></Select>
            </div>
            <div>
              <Label>Footer options</Label>
              <Input placeholder="Include college, faculty, date" />
            </div>
          </div>
        </Step>
      )}

      {step === 5 && (
        <Step title="Run & Schedule">
          <div className="flex gap-3">
            <Button className="elevated">Run now</Button>
            <Button variant="secondary">Save as draft</Button>
          </div>
        </Step>
      )}

      <div className="mt-4 flex justify-between">
        <Button variant="secondary" onClick={() => setStep((s) => Math.max(1, s-1))}>Back</Button>
        <Button onClick={() => setStep((s) => Math.min(5, s+1))}>{step===5? 'Finish' : 'Next'}</Button>
      </div>
    </div>
  );
};

export default NewJobWizard;
