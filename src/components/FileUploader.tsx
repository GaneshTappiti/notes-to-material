import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { UploadCloud } from "lucide-react";

export type UploadedFile = {
  id: string;
  file: File;
  pages?: number;
  status?: "pending" | "ocr" | "indexed" | "error";
};

interface FileUploaderProps {
  label: string;
  onFilesChange?: (files: UploadedFile[]) => void;
}

const FileUploader = ({ label, onFilesChange }: FileUploaderProps) => {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [files, setFiles] = useState<UploadedFile[]>([]);

  const onDrop = (fileList: FileList | null) => {
    if (!fileList) return;
    const next = Array.from(fileList).map((f, i) => ({ id: `${Date.now()}-${i}`, file: f, status: "pending" as const }));
    setFiles((prev) => {
      const merged = [...prev, ...next];
      onFilesChange?.(merged);
      return merged;
    });
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <div
          className="border-dashed border rounded-lg p-6 text-center cursor-pointer hover:bg-accent/50 transition-colors"
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            onDrop(e.dataTransfer.files);
          }}
          role="button"
          aria-label={`Upload ${label}`}
        >
          <UploadCloud className="mx-auto h-8 w-8 text-muted-foreground" aria-hidden="true" />
          <p className="mt-2 text-sm text-muted-foreground">Drag & drop PDFs/images or click to browse</p>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,image/*"
            multiple
            onChange={(e) => onDrop(e.target.files)}
            className="hidden"
          />
        </div>

        {files.length > 0 && (
          <ul className="mt-4 space-y-2">
            {files.map((f) => (
              <li key={f.id} className="flex items-center justify-between rounded-md border px-3 py-2">
                <div className="min-w-0">
                  <p className="text-sm truncate" title={f.file.name}>{f.file.name}</p>
                  <p className="text-xs text-muted-foreground">{Math.round(f.file.size / 1024)} KB</p>
                </div>
                <Badge variant="secondary">{f.status ?? "pending"}</Badge>
              </li>
            ))}
          </ul>
        )}

        {files.length > 0 && (
          <div className="mt-4 flex gap-2">
            <Button variant="default">Start OCR</Button>
            <Button variant="secondary">Clear</Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default FileUploader;
