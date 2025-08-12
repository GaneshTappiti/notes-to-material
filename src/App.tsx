import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import AppLayout from "./components/layout/AppLayout";
import Dashboard from "./pages/Dashboard";
import Uploads from "./pages/Uploads";
import NewJobWizard from "./pages/NewJobWizard";
import Queue from "./pages/Queue";
import ReviewCenter from "./pages/ReviewCenter";
import TemplatesExport from "./pages/TemplatesExport";
import Jobs from "./pages/Jobs";
import Settings from "./pages/Settings";
import Logs from "./pages/Logs";
import NotFound from "./pages/NotFound";
import RagPlayground from "./pages/RagPlayground";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <HelmetProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <AppLayout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/uploads" element={<Uploads />} />
              <Route path="/new-job" element={<NewJobWizard />} />
              <Route path="/queue" element={<Queue />} />
              <Route path="/review" element={<ReviewCenter />} />
              <Route path="/jobs" element={<Jobs />} />
              <Route path="/templates" element={<TemplatesExport />} />
              <Route path="/exports" element={<TemplatesExport />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/logs" element={<Logs />} />
              <Route path="/rag" element={<RagPlayground />} />
              {/* CATCH-ALL */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </AppLayout>
        </BrowserRouter>
      </TooltipProvider>
    </HelmetProvider>
  </QueryClientProvider>
);

export default App;