import Seo from "@/components/Seo";
import FileUploader from "@/components/FileUploader";

const Uploads = () => {
  return (
    <div>
      <Seo title="Uploads — Scollab" description="Upload notes and question banks for OCR and processing." />
      <h1 className="text-2xl font-bold mb-4">Uploads</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <FileUploader label="Notes (PDFs & images)" />
        <FileUploader label="Question banks" />
      </div>
    </div>
  );
};

export default Uploads;
