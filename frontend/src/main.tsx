import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { CompanySettingsProvider } from "./context/CompanySettingsContext";
import "./i18n";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <CompanySettingsProvider>
        <App />
      </CompanySettingsProvider>
    </BrowserRouter>
  </StrictMode>
);
