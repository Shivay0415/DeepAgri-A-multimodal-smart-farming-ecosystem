# Irrigation Dataset Format

Place the Module 2 training dataset at `backend/data/irrigation_training.csv`.

Supported dataset schemas:

1. Regressor schema:
   - `crop`
   - `growth_stage`
   - `soil_moisture_pct`
   - `rainfall_forecast_mm`
   - `temperature_c`
   - `humidity_pct`
   - `area_hectares`
   - `target_water_depth_mm`

2. Notebook-style classifier schema:
   - `crop` or `Crop`
   - `growth_stage` or `Growth_Stage`
   - `soil_moisture_pct` or `Soil_Moisture`
   - `rainfall_forecast_mm` or `Rainfall_mm`
   - `temperature_c` or `Temperature_C`
   - `humidity_pct` or `Humidity`
   - optional `area_hectares`
   - `Irrigation_Need`

Example:

```csv
crop,growth_stage,soil_moisture_pct,rainfall_forecast_mm,temperature_c,humidity_pct,area_hectares,target_water_depth_mm
cotton,vegetative,32,5,30,64,1.5,4.8
rice,seedling,48,14,28,78,2.0,3.2
maize,flowering,22,1,34,52,1.2,6.1
```

Train with:

```bash
python manage.py train_irrigation_model --dataset data/irrigation_training.csv
```
