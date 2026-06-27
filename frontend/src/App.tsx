import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import BatchAnalysisPage from "./pages/BatchAnalysis";
import BatchChat from "./pages/BatchChat";
import BatchDetails from "./pages/BatchDetails";
import BatchesList from "./pages/BatchesList";
import Dashboard from "./pages/Dashboard";
import ReportAnalysis from "./pages/ReportAnalysis";
import ReportChat from "./pages/ReportChat";
import ReportDetails from "./pages/ReportDetails";
import ReportsList from "./pages/ReportsList";
import SavedAnalysesList from "./pages/SavedAnalysesList";
import SavedAnalysisDetail from "./pages/SavedAnalysisDetail";
import Settings from "./pages/Settings";
import UploadBatch from "./pages/UploadBatch";
import UploadReport from "./pages/UploadReport";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/upload" element={<UploadReport />} />
        <Route path="/batches/upload" element={<UploadBatch />} />
        <Route path="/batches" element={<BatchesList />} />
        <Route path="/batches/:id" element={<BatchDetails />} />
        <Route path="/batches/:id/analysis" element={<BatchAnalysisPage />} />
        <Route path="/batches/:id/chat" element={<BatchChat />} />
        <Route path="/reports" element={<ReportsList />} />
        <Route path="/reports/:id" element={<ReportDetails />} />
        <Route path="/reports/:id/analysis" element={<ReportAnalysis />} />
        <Route path="/reports/:id/chat" element={<ReportChat />} />
        <Route path="/saved-analyses" element={<SavedAnalysesList />} />
        <Route path="/saved-analyses/:id" element={<SavedAnalysisDetail />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}
