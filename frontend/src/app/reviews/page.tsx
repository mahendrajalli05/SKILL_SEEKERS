import { PageHeader } from "@/components/system/PageHeader";
import { PageState } from "@/components/ui/PageState";

export default function ReviewsPage() {
  return (
    <div className="space-y-4">
      <PageHeader
        title="Human review"
        explanation="A fleet-wide review queue is not available. Officer decisions are recorded on each Investigation Workspace."
      />
      <PageState
        kind="unavailable"
        title="Unavailable"
        message="A fleet-wide review queue is not available in this prototype. Officer decisions are recorded on each Investigation Workspace. The audit table exists; this page is a shell."
      />
    </div>
  );
}
