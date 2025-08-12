import Seo from "@/components/Seo";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const Logs = () => {
  return (
    <div>
      <Seo title="Logs — Scollab" description="Audit trail of jobs and actions." />
      <h1 className="text-2xl font-bold mb-4">Logs / Activity</h1>

      <Card>
        <CardHeader><CardTitle>Recent activity</CardTitle></CardHeader>
        <CardContent>
          <ul className="text-sm space-y-2 text-muted-foreground">
            <li>12:24 Admin approved 12 answers in CSE201</li>
            <li>12:03 Job rerun: NOT_FOUND items only</li>
            <li>11:40 Faculty uploaded notes.pdf</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
};

export default Logs;
