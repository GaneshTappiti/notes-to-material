import { CheckCircle2, Database, FileUp, FileText, Scan, Shield } from "lucide-react";
import { cn } from "@/lib/utils";

export type JobStage = {
  key: string;
  label: string;
  status: "pending" | "active" | "done" | "error";
};

const icons: Record<string, any> = {
  upload: FileUp,
  ocr: Scan,
  indexing: Database,
  model: Shield,
  validation: CheckCircle2,
  ready: FileText,
};

export const defaultStages: JobStage[] = [
  { key: "upload", label: "File upload", status: "done" },
  { key: "ocr", label: "OCR", status: "active" },
  { key: "indexing", label: "Indexing", status: "pending" },
  { key: "model", label: "Model Runs", status: "pending" },
  { key: "validation", label: "Validation", status: "pending" },
  { key: "ready", label: "Ready for Review", status: "pending" },
];

interface Props {
  stages?: JobStage[];
}

const JobTimeline = ({ stages = defaultStages }: Props) => {
  return (
    <ol className="grid grid-cols-1 md:grid-cols-6 gap-3">
      {stages.map((s) => {
        const Icon = icons[s.key] ?? CheckCircle2;
        return (
          <li key={s.key} className={cn("rounded-lg border p-3", s.status === "done" && "bg-secondary", s.status === "active" && "elevated")}
              aria-current={s.status === "active" ? "step" : undefined}>
            <div className="flex items-center gap-2">
              <Icon className={cn("h-4 w-4", s.status === "error" && "text-destructive")} aria-hidden="true" />
              <span className="text-sm font-medium">{s.label}</span>
            </div>
            <p className="mt-1 text-xs text-muted-foreground capitalize">{s.status}</p>
          </li>
        );
      })}
    </ol>
  );
};

export default JobTimeline;
