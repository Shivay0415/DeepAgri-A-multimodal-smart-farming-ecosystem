from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from crop.training import train_crop_model
from irrigation.training import train_irrigation_model


class Command(BaseCommand):
    help = "Train the bundled demo crop and irrigation models from the included datasets."

    def handle(self, *args, **options) -> None:
        base_dir = Path.cwd()
        crop_dataset = base_dir / "data" / "crop_recommendation.csv"
        irrigation_dataset = base_dir / "data" / "irrigation_training.csv"

        missing = [path for path in (crop_dataset, irrigation_dataset) if not path.exists()]
        if missing:
            raise CommandError(
                "Missing required demo datasets: " + ", ".join(str(path) for path in missing)
            )

        crop_summary = train_crop_model(crop_dataset)
        irrigation_summary = train_irrigation_model(irrigation_dataset)

        self.stdout.write(self.style.SUCCESS("Demo models trained successfully."))
        self.stdout.write(
            f"Crop model: {crop_summary['samples']} rows -> {crop_summary['model_path']}"
        )
        self.stdout.write(
            "Irrigation model: "
            f"{irrigation_summary['samples']} rows -> {irrigation_summary['model_path']}"
        )

