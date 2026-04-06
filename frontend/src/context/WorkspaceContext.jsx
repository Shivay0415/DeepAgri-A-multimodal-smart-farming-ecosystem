import { createContext, useContext, useState } from "react";

const WorkspaceContext = createContext(null);

export function WorkspaceProvider({ children }) {
  const [cropReport, setCropReport] = useState(null);
  const [irrigationPlan, setIrrigationPlan] = useState(null);
  const [diseaseReport, setDiseaseReport] = useState(null);
  const [marketReport, setMarketReport] = useState(null);
  const [advisorAnswer, setAdvisorAnswer] = useState(null);

  const value = {
    cropReport,
    irrigationPlan,
    diseaseReport,
    marketReport,
    advisorAnswer,
    saveCropReport: setCropReport,
    saveIrrigationPlan: setIrrigationPlan,
    saveDiseaseReport: setDiseaseReport,
    saveMarketReport: setMarketReport,
    saveAdvisorAnswer: setAdvisorAnswer,
  };

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspace() {
  const value = useContext(WorkspaceContext);
  if (!value) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return value;
}
