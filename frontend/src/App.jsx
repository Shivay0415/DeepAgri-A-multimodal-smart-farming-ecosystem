import { Navigate, Route, Routes } from "react-router-dom";

import AppShell from "./components/AppShell";
import AdvisorPage from "./pages/AdvisorPage";
import CropPage from "./pages/CropPage";
import DiseasePage from "./pages/DiseasePage";
import HomePage from "./pages/HomePage";
import IrrigationPage from "./pages/IrrigationPage";
import MarketPage from "./pages/MarketPage";

function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<HomePage />} />
        <Route path="crop" element={<CropPage />} />
        <Route path="irrigation" element={<IrrigationPage />} />
        <Route path="disease" element={<DiseasePage />} />
        <Route path="market" element={<MarketPage />} />
        <Route path="advisor" element={<AdvisorPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export default App;
