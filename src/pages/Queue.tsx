import Seo from "@/components/Seo";
import JobTimeline from "@/components/JobTimeline";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const Queue = () => {
  return (
    <div>
      <Seo title="Processing Queue — Scollab" description="Track OCR, indexing, and model runs with live logs." />
      <h1 className="text-2xl font-bold mb-4">Processing Queue</h1>

      <JobTimeline />

      <Card className="mt-4">
        <CardHeader><CardTitle>Live logs</CardTitle></CardHeader>
        <CardContent>
          <pre className="text-xs text-muted-foreground whitespace-pre-wrap">[12:22:05] OCR started for notes.pdf...
[12:22:11] OCR page 1/24 complete
[12:23:01] Indexing chunks...
[12:23:14] Model run queued for Q#23</pre>
        </CardContent>
      </Card>
    </div>
  );
};

export default Queue;
