# Irrigation Dataset Format

Place the Module 2 training dataset at `backend/data/irrigation_training.csv`.

Expected columns:

- `crop`
- `growth_stage`
- `soil_moisture_pct`
- `rainfall_forecast_mm`
- `temperature_c`
- `humidity_pct`
- `area_hectares`
- `target_water_depth_mm`

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

