async function readJson(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

async function postJson(path, payload, fallbackMessage) {
  const response = await fetch(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await readJson(response);
  if (!response.ok) {
    throw new Error(data.error || fallbackMessage);
  }

  return data;
}

export function requestCropRecommendation(payload) {
  return postJson(
    "/api/v1/crop/recommend/",
    payload,
    "Unable to generate the crop recommendation right now.",
  );
}

export function requestIrrigationPlan(payload) {
  return postJson(
    "/api/v1/irrigation/plan/",
    payload,
    "Unable to generate the irrigation plan right now.",
  );
}

export async function requestDiseaseDetection({ crop, symptomHint, file }) {
  const formData = new FormData();
  formData.append("crop", crop);
  formData.append("symptom_hint", symptomHint);
  formData.append("image", file);

  const response = await fetch("/api/v1/disease/detect/", {
    method: "POST",
    body: formData,
  });

  const data = await readJson(response);
  if (!response.ok) {
    throw new Error(data.error || "Unable to analyze the uploaded leaf image right now.");
  }

  return data;
}

export function requestMarketForecast(payload) {
  return postJson(
    "/api/v1/market/forecast/",
    payload,
    "Unable to generate the market forecast right now.",
  );
}

export function requestAdvisorAnswer(payload) {
  return postJson(
    "/api/v1/chat/ask/",
    payload,
    "Unable to get an advisor response right now.",
  );
}

export async function requestBackendHealth() {
  const response = await fetch("/health/");
  const data = await readJson(response);

  if (!response.ok) {
    throw new Error(data.error || "Unable to reach the Django backend right now.");
  }

  return data;
}
