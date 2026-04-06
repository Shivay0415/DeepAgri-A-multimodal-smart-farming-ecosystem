# System Architecture

## Goal

Build a unified agriculture intelligence platform where each module solves one stage of the farmer journey and passes context to the next stage.

## End-to-End Flow

1. The farmer enters soil data.
2. Module 1 recommends a crop.
3. Module 2 uses the crop plus forecast conditions to recommend irrigation timing and water quantity.
4. Module 3 detects disease from a leaf image.
5. Module 5 explains disease causes and remedies in the farmer's language.
6. Module 4 forecasts market price and expected revenue near harvest.
7. Module 6 presents all outputs in one dashboard.

## Backend Design

The backend uses a single Django project with separate apps and services for each module:

- `/api/v1/crop/recommend/`
- `/api/v1/irrigation/plan/`
- `/api/v1/disease/detect/`
- `/api/v1/market/forecast/`
- `/api/v1/chat/ask/`

Each module has:

- a dedicated Django app
- a `views.py` file that exposes JSON endpoints
- a `services.py` file for the core logic

This keeps team ownership clean while preserving a single backend for deployment.

## Frontend Design

The frontend is a React dashboard that:

- introduces the six modules
- shows the farmer workflow
- highlights model choices and API contracts
- acts as the future integration surface for live model outputs

## Recommended Milestones

### Milestone 1

- Finalize dataset choices
- Freeze request and response contracts
- Stand up the Django backend and dashboard shell

### Milestone 2

- Train Module 1 and Module 2 models
- Integrate disease image preprocessing
- Add sample data and evaluation metrics

### Milestone 3

- Integrate market forecasting
- Add multilingual chatbot with retrieval
- Connect frontend forms to live APIs

### Milestone 4

- Add login, persistence, and farmer history
- Improve explainability and confidence reporting
- Prepare demo dataset and final presentation flow

## Production Upgrades

- Add PostgreSQL for farmer records, model predictions, and forecast history
- Add Celery or background workers for slow model inference
- Add object storage for disease images
- Add monitoring for API latency, model drift, and forecast performance
