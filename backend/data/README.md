# Demo Data Inventory

This folder now contains the bundled demo datasets for the capstone backend.

Files included:

- `crop_recommendation.csv`: training data for Module 1
- `irrigation_training.csv`: training data for Module 2
- `market_price_history.csv`: bundled market history for Module 4
- `disease_catalog.json`: disease knowledge base for Module 3
- `agri_knowledge_base.json`: multilingual FAQ and answer base for Module 5

Train the demo crop and irrigation models with:

```bash
python manage.py bootstrap_demo_models
```

Or train them separately with:

```bash
python manage.py train_crop_model --dataset data/crop_recommendation.csv
python manage.py train_irrigation_model --dataset data/irrigation_training.csv
```
