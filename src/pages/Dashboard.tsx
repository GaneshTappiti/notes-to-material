import Seo from "@/components/Seo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plus, Upload, BookOpen, FileClock } from "lucide-react";
import { Link } from "react-router-dom";

const KPI = ({ title, value }: { title: string; value: string }) => (
  <Card className="elevated">
    <CardHeader>
      <CardTitle className="text-sm text-muted-foreground">{title}</CardTitle>
    </CardHeader>
    <CardContent>
      <p className="text-3xl font-semibold">{value}</p>
    </CardContent>
  </Card>
);

const Dashboard = () => {
  return (
    <div>
      <Seo title="Dashboard — Scollab" description="Monitor jobs and start new automated study material generation." />
      <header className="mb-6">
        <h1 className="text-3xl font-bold">Automated Study Material Generator</h1>
        <p className="text-muted-foreground mt-1">Turn faculty notes into exam-ready PDFs with OCR, retrieval, and review.</p>
      </header>

      <section aria-label="KPIs" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <KPI title="Pending uploads" value="8" />
        <KPI title="Processing jobs" value="3" />
        <KPI title="Ready for review" value="12" />
        <KPI title="Published PDFs" value="27" />
      </section>

      <section className="mb-8">
        <div className="flex flex-wrap gap-3">
          <Link to="/new-job"><Button className="elevated"><Plus className="h-4 w-4 mr-2" /> New Job</Button></Link>
          <Link to="/uploads"><Button variant="secondary"><Upload className="h-4 w-4 mr-2" /> Upload Notes</Button></Link>
          <Link to="/uploads"><Button variant="secondary"><BookOpen className="h-4 w-4 mr-2" /> Upload QBank</Button></Link>
          <Link to="/queue"><Button variant="outline"><FileClock className="h-4 w-4 mr-2" /> View Queue</Button></Link>
        </div>
      </section>

      <section aria-label="Recent jobs" className="space-y-3">
        <h2 className="text-xl font-semibold">Recent jobs</h2>
        <div className="grid grid-cols-1 gap-3">
          {[1,2,3,4,5].map((i) => (
            <Card key={i}>
              <CardContent className="py-4 flex items-center justify-between">
                <div>
                  <p className="font-medium">CSE201 Unit {i} — Midterm Pack</p>
                  <p className="text-sm text-muted-foreground">Course: CSE201 • Uploader: Faculty {i}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">Processing</Badge>
                  <span className="text-xs text-muted-foreground">Updated 5m ago</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
};

export default Dashboard;
