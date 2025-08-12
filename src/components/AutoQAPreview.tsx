import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { QAPreviewItem, QuestionStatus } from "@/types/autoqa";
import { CheckCircle2, AlertCircle, Clock, ExternalLink } from "lucide-react";

interface AutoQAPreviewProps {
  items: QAPreviewItem[];
  isGenerating?: boolean;
  progress?: number;
  onOpenReview?: () => void;
}

const statusConfig: Record<QuestionStatus, { icon: any; color: string; label: string }> = {
  FOUND: { icon: CheckCircle2, color: "text-green-600", label: "Found" },
  NOT_FOUND: { icon: AlertCircle, color: "text-red-600", label: "Not Found" },
  NEEDS_REVIEW: { icon: Clock, color: "text-yellow-600", label: "Needs Review" },
};

const AutoQAPreview = ({ items, isGenerating = false, progress = 0, onOpenReview }: AutoQAPreviewProps) => {
  const stats = items.reduce(
    (acc, item) => {
      acc[item.status]++;
      return acc;
    },
    { FOUND: 0, NOT_FOUND: 0, NEEDS_REVIEW: 0 } as Record<QuestionStatus, number>
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Generated Questions Preview</CardTitle>
          {onOpenReview && (
            <Button variant="outline" size="sm" onClick={onOpenReview}>
              <ExternalLink className="h-4 w-4 mr-2" />
              Open Review Center
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {isGenerating && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>Generating questions...</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <Progress value={progress} className="w-full" />
          </div>
        )}

        {/* Stats Summary */}
        <div className="grid grid-cols-3 gap-4">
          {Object.entries(stats).map(([status, count]) => {
            const config = statusConfig[status as QuestionStatus];
            const Icon = config.icon;
            return (
              <div key={status} className="text-center">
                <div className="flex items-center justify-center gap-2">
                  <Icon className={`h-4 w-4 ${config.color}`} />
                  <span className="font-semibold">{count}</span>
                </div>
                <p className="text-xs text-muted-foreground">{config.label}</p>
              </div>
            );
          })}
        </div>

        {/* Questions List */}
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {items.map((item) => {
            const config = statusConfig[item.status];
            const Icon = config.icon;
            
            return (
              <div key={item.question_id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">{item.marks}M</Badge>
                    <Icon className={`h-4 w-4 ${config.color}`} />
                  </div>
                  <p className="text-sm font-medium truncate mt-1" title={item.question_text}>
                    {item.question_text}
                  </p>
                  <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                    <span>{item.page_count} page refs</span>
                    {item.confidence_score && (
                      <span>Confidence: {Math.round(item.confidence_score * 100)}%</span>
                    )}
                  </div>
                </div>
                <Badge variant={item.status === "FOUND" ? "default" : item.status === "NOT_FOUND" ? "destructive" : "secondary"}>
                  {config.label}
                </Badge>
              </div>
            );
          })}
        </div>

        {items.length === 0 && !isGenerating && (
          <div className="text-center py-8 text-muted-foreground">
            <Clock className="h-8 w-8 mx-auto mb-2" />
            <p>No questions generated yet</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AutoQAPreview;
