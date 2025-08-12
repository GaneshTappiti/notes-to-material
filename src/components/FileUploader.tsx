import { useRef, useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { UploadCloud } from "lucide-react";
import { uploadFile, getUploadStatus, deleteUpload } from "@/lib/api";
import { toast } from "@/components/ui/use-toast";

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
    // auto start upload
    next.forEach(startUpload);
  };

  const startUpload = async (uf: UploadedFile) => {
    try {
      setFiles((prev) => prev.map(p => p.id === uf.id ? { ...p, status: 'ocr' } : p));
      const res = await uploadFile(uf.file);
      setFiles((prev) => prev.map(p => p.id === uf.id ? { ...p, id: res.file_id, status: 'ocr' } : p));
    } catch (e: any) {
      toast({ title: 'Upload failed', description: e.message, variant: 'destructive' });
      setFiles((prev) => prev.map(p => p.id === uf.id ? { ...p, status: 'error' } : p));
    }
  };

  // Poll statuses
  useEffect(() => {
    const interval = setInterval(() => {
      files.filter(f => f.status === 'ocr').forEach(async f => {
        try {
          const s = await getUploadStatus(f.id);
            if (s.status === 'done') {
              setFiles(prev => prev.map(p => p.id === f.id ? { ...p, status: 'indexed', pages: s.pages } : p));
            }
        } catch {}
      });
    }, 2000);
    return () => clearInterval(interval);
  }, [files]);

  const clearAll = () => setFiles([]);

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
              <li key={f.id} className="flex items-center justify-between rounded-md border px-3 py-2 gap-2">
                <div className="min-w-0 flex-1">
                  <p className="text-sm truncate" title={f.file.name}>{f.file.name}</p>
                  <p className="text-xs text-muted-foreground">{Math.round(f.file.size / 1024)} KB</p>
                </div>
                <Badge variant="secondary" className="shrink-0 mr-1">{f.status ?? "pending"}</Badge>
                {f.status==='indexed' && (
                  <Button size="sm" variant="outline" onClick={async ()=> {
                    try { await deleteUpload(f.id); setFiles(prev=> prev.filter(p=>p.id!==f.id)); } catch {}
                  }}>Delete</Button>
                )}
              </li>
            ))}
          </ul>
        )}

        {files.length > 0 && (
          <div className="mt-4 flex gap-2">
            <Button variant="secondary" onClick={clearAll}>Clear</Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default FileUploader;
