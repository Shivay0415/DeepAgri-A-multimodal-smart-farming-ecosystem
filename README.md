# Smart Agriculture Intelligence Platform

This repository is a starter implementation for a six-module capstone project that helps farmers decide what to grow, when to irrigate, how to detect plant disease, when to sell, and how to ask questions in their local language from one unified dashboard.

## Modules

1. **Crop Recommendation Engine**: Uses soil chemistry to recommend the best crop candidate.
2. **Smart Irrigation & Weather Analysis**: Converts weather and soil conditions into irrigation advice.
3. **Visual Plant Disease Detection**: Accepts a leaf image and returns a likely disease plus remedies.
4. **Market Intelligence & Yield Forecasting**: Projects short-term crop prices and expected revenue.
5. **Multilingual AI Agri-Bot**: Answers farmer questions in English, Hindi, or Tamil with domain-aware responses.
6. **Unified Dashboard**: A single frontend that surfaces the outputs of all modules.

## Starter Stack

- **Backend**: Django
- **Frontend**: React + Vite
- **Model integration style**: Each AI module has its own Django app and service layer so the team can swap placeholder logic for trained models later.

## Repository Layout

```text
backend/
  manage.py
  agri_platform/
  core/
  crop/
  irrigation/
  disease/
  market/
  chatbot/
docs/
  system-architecture.md
frontend/
  src/
  package.json
```

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Backend runs at `http://127.0.0.1:8000`.

If you want the Agri-Bot to use ChatGPT or Gemini from the Django backend, copy `backend/.env.example` to `backend/.env` and add at least one API key before starting Django.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://127.0.0.1:5173`.

If PowerShell does not recognize `npm` right after installing Node.js, open a new terminal or run:

```powershell
powershell -ExecutionPolicy Bypass -File .\run-dev.ps1
```

## Module 1 Status

Module 1 now has a live frontend form and a Django API integration.

- If no trained model exists, the backend uses a rule-based fallback recommender.
- If you train a model artifact, the same endpoint automatically switches to the trained classifier.

### Train Module 1

1. Put your crop dataset at `backend/data/crop_recommendation.csv`
2. Ensure it includes either the project schema:
   `nitrogen`, `phosphorus`, `potassium`, `temperature_c`, `humidity_pct`, `ph`, `rainfall_mm`, `label`
   or the standard crop dataset schema:
   `N`, `P`, `K`, `temperature`, `humidity`, `ph`, `rainfall`, `label`
3. From the `backend` folder, run:

```bash
python manage.py train_crop_model --dataset data/crop_recommendation.csv
```

You can also use the notebook-derived trainers that were ported from the supplied capstone notebook:

```bash
python manage.py train_crop_model --dataset data/crop_recommendation.csv --trainer notebook-mlp
python manage.py train_crop_model --dataset data/crop_recommendation.csv --trainer notebook-transformer
```

Those two advanced trainers require `torch` to be installed in your local Python environment.

This saves the trained model to `backend/models/crop_recommender.joblib`.

### Test Module 1

1. Start Django with `python manage.py runserver`
2. Start the frontend with `npm run dev`
3. Open the dashboard and submit the soil form
4. Check whether the result shows `fallback` or `trained` mode

## Module 2 Status

Module 2 now has a live frontend form and a Django API integration.

- If no trained regressor exists, the backend uses a rule-based irrigation planner.
- If you train the regressor artifact, the same endpoint automatically switches to the trained model.
- The irrigation trainer also supports a notebook-style Random Forest classifier dataset with `Irrigation_Need` labels such as `High`, `Medium`, and `Low`.
- If `OPENWEATHER_API_KEY` is configured on the backend, Module 2 can use OpenWeatherMap-assisted live weather inputs.

### Train Module 2

1. Put your irrigation dataset at `backend/data/irrigation_training.csv`
2. Ensure it includes these columns:
   `crop`, `growth_stage`, `soil_moisture_pct`, `rainfall_forecast_mm`, `temperature_c`, `humidity_pct`, `area_hectares`, `target_water_depth_mm`
3. From the `backend` folder, run:

```bash
python manage.py train_irrigation_model --dataset data/irrigation_training.csv
```

This saves the trained model to `backend/models/irrigation_regressor.joblib`.

### Configure Live Weather For Module 2

Set one of these environment variables before starting Django:

```powershell
$env:OPENWEATHER_API_KEY="your_api_key_here"
```

or

```powershell
$env:OPENWEATHERMAP_API_KEY="your_api_key_here"
```

### Test Module 2

1. Start Django with `python manage.py runserver`
2. Start the frontend with `npm run dev`
3. Open the dashboard and fill in the irrigation planner
4. Optionally enable live weather and provide a location
5. Check whether the result shows `fallback` or `trained` mode and whether weather came from `manual` or `live`

## Module 3 Status

Module 3 now supports a real MobileNetV2 image-classification path with a safe fallback.

- Dataset file: `backend/data/disease_catalog.json`
- Backend service: if a trained disease classifier exists and TensorFlow is installed, uploaded leaf images are classified by the CNN; otherwise the system falls back to symptom-and-catalog matching
- Current limitation: TensorFlow is not bundled into the lightweight starter environment, so the CNN path requires a compatible TensorFlow install before training and inference

### Train Module 3

From the `backend` folder, point the trainer at a folder dataset such as PlantVillage:

```bash
python manage.py train_disease_model --dataset "C:\path\to\PlantVillage" --class-filter Tomato --epochs 6
```

This command copies a bounded subset of matching class folders, fine-tunes a MobileNetV2 classifier, and saves the result to:

- `backend/models/disease_classifier.keras`
- `backend/models/disease_classifier_metadata.json`

## Module 4 Status

Module 4 now uses bundled price history.

- Dataset file: `backend/data/market_price_history.csv`
- Backend service: forecasts from recent crop and market history
- If `current_price_per_quintal` is omitted, the backend can use the latest bundled market price

## Module 5 Status

Module 5 now supports provider-backed chat with a local agriculture fallback.

- Dataset file: `backend/data/agri_knowledge_base.json`
- Backend service: OpenAI Responses API or Google Gemini API when keys are configured, plus bundled agriculture grounding and local fallback matching

### Configure Module 5 Provider Support

Create `backend/.env` from `backend/.env.example`, then set one of these:

```powershell
OPENAI_API_KEY=your_openai_key
OPENAI_CHAT_MODEL=gpt-4.1-mini
```

or

```powershell
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.5-flash
```

You can also force the provider choice:

```powershell
AGRI_BOT_PROVIDER=openai
```

or

```powershell
AGRI_BOT_PROVIDER=gemini
```

If no provider key is configured, the Agri-Bot still works through the bundled agriculture knowledge base, but open-ended answers are more limited than the full provider-backed chat mode.

## Demo Bootstrap

Bundled demo datasets are included for crop training, irrigation training, market history, disease knowledge, and chatbot knowledge.

From the `backend` folder, you can train the demo crop and irrigation models together with:

```bash
python manage.py bootstrap_demo_models
```

This uses:

- `backend/data/crop_recommendation.csv`
- `backend/data/irrigation_training.csv`
- `backend/data/market_price_history.csv`
- `backend/data/disease_catalog.json`
- `backend/data/agri_knowledge_base.json`

## Suggested Team Ownership

- **Member 1** owns `backend/crop/services.py`
- **Member 2** owns `backend/irrigation/services.py`
- **Member 3** owns `backend/disease/services.py`
- **Member 4** owns `backend/market/services.py`
- **Member 5** owns `backend/chatbot/services.py`
- **Member 6** owns the frontend plus final integration work

## Integration Plan

1. Replace the placeholder crop recommender with a trained DNN or TabNet model.
2. Connect irrigation planning to OpenWeatherMap and a trained regressor.
3. Swap the disease placeholder with a CNN inference pipeline using uploaded images.
4. Connect market forecasting to historical mandi or commodity price datasets and an LSTM or GRU model.
5. Expand the Agri-Bot grounding layer into a fuller RAG pipeline with richer document retrieval.
6. Add authentication, persistence, and farmer records in Django models.

## Current Scope

This starter is intentionally lightweight. The Django endpoints already model the integration contracts and return meaningful demo responses, while the frontend explains the workflow and system architecture in a form the team can extend.
