import csv
from datetime import date, datetime, timedelta
from functools import lru_cache
from math import pi, sin
from pathlib import Path


HISTORY_PATH = Path(__file__).resolve().parent.parent / "data" / "market_price_history.csv"

TREND_BY_CROP = {
    "cotton": 0.017,
    "rice": 0.009,
    "maize": 0.012,
    "wheat": 0.008,
    "groundnut": 0.015,
}


@lru_cache(maxsize=1)
def _load_history() -> list[dict]:
    history = []
    with HISTORY_PATH.open("r", encoding="utf-8", newline="") as history_file:
        reader = csv.DictReader(history_file)
        for row in reader:
            history.append(
                {
                    "date": datetime.strptime(row["date"], "%Y-%m-%d").date(),
                    "crop": row["crop"].strip().lower(),
                    "market_name": row["market_name"].strip(),
                    "price_per_quintal": float(row["price_per_quintal"]),
                }
            )
    return history


def _select_history(crop: str, market_name: str | None) -> list[dict]:
    crop_key = crop.strip().lower()
    history = [row for row in _load_history() if row["crop"] == crop_key]
    if market_name:
        target_market = market_name.strip().lower()
        market_specific = [
            row for row in history if row["market_name"].strip().lower() == target_market
        ]
        if market_specific:
            history = market_specific
    return sorted(history, key=lambda row: row["date"])


def _daily_trend(history: list[dict], crop: str) -> float:
    if len(history) < 2:
        return TREND_BY_CROP.get(crop.strip().lower(), 0.01)

    recent = history[-5:]
    changes = []
    for previous, current in zip(recent, recent[1:]):
        if previous["price_per_quintal"] <= 0:
            continue
        changes.append(
            (current["price_per_quintal"] - previous["price_per_quintal"])
            / previous["price_per_quintal"]
        )

    if not changes:
        return TREND_BY_CROP.get(crop.strip().lower(), 0.01)
    return sum(changes) / len(changes)


def forecast_market(payload: dict) -> dict:
    history = _select_history(payload["crop"], payload.get("market_name"))
    crop_key = payload["crop"].strip().lower()
    daily_trend = _daily_trend(history, crop_key)

    if payload.get("current_price_per_quintal") is not None:
        baseline_price = payload["current_price_per_quintal"]
        price_source = "manual input"
    elif history:
        baseline_price = history[-1]["price_per_quintal"]
        price_source = "bundled market dataset"
    else:
        raise ValueError(
            "No market history was found for this crop. Provide current_price_per_quintal manually."
        )

    start = date.today()
    daily_forecast = []
    for offset in range(payload["horizon_days"]):
        current_date = start + timedelta(days=offset)
        seasonal_wave = sin((offset / max(payload["horizon_days"] - 1, 1)) * pi) * 0.02
        growth_factor = 1 + (daily_trend * offset) + seasonal_wave
        predicted_price = round(baseline_price * growth_factor, 2)
        daily_forecast.append(
            {
                "date": current_date,
                "predicted_price_per_quintal": predicted_price,
            }
        )

    peak_point = max(daily_forecast, key=lambda point: point["predicted_price_per_quintal"])
    expected_revenue = round(
        peak_point["predicted_price_per_quintal"] * payload["expected_yield_tons"] * 10,
        2,
    )

    rationale = [
        f"Baseline price was anchored at {baseline_price:.2f} per quintal from {price_source}.",
        f"Recent history produced an estimated daily trend of {daily_trend:.4f}.",
        "A small seasonal wave was applied to mimic short-term market fluctuations.",
    ]
    if payload.get("market_name"):
        rationale.append(f"Forecast is intended for the {payload['market_name']} market context.")
    if history:
        rationale.append(f"History rows used: {len(history)} from the bundled dataset.")

    return {
        "crop": payload["crop"],
        "best_sale_date": peak_point["date"],
        "peak_price_per_quintal": peak_point["predicted_price_per_quintal"],
        "expected_revenue": expected_revenue,
        "daily_forecast": daily_forecast,
        "rationale": rationale,
        "model_family": "Dataset-backed price trend forecaster placeholder for an LSTM / GRU pipeline",
        "price_source": price_source,
        "history_points_used": len(history),
    }
