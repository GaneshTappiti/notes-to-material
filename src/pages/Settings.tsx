import Seo from "@/components/Seo";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const Settings = () => {
  return (
    <div>
      <Seo title="Settings — Scollab" description="Configure models, storage, and approvals." />
      <h1 className="text-2xl font-bold mb-4">Settings</h1>
      <Card>
        <CardHeader><CardTitle>AI Model</CardTitle></CardHeader>
        <CardContent>
          <Input placeholder="Model name, e.g., gpt-4o-mini" />
        </CardContent>
      </Card>
    </div>
  );
};

export default Settings;
