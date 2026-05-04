from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from irrigation.training import train_irrigation_model


class Command(BaseCommand):
    help = "Train the irrigation regressor from a CSV dataset."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--dataset",
            default="data/irrigation_training.csv",
            help="Path to the irrigation training CSV relative to backend/.",
        )

    def handle(self, *args, **options) -> None:
        dataset_value = options["dataset"]
        dataset_path = Path(dataset_value)
        if not dataset_path.is_absolute():
            dataset_path = Path.cwd() / dataset_path

        if not dataset_path.exists():
            raise CommandError(f"Dataset not found: {dataset_path}")

        summary = train_irrigation_model(dataset_path)
        self.stdout.write(self.style.SUCCESS("Irrigation model trained successfully."))
        self.stdout.write(f"Samples: {summary['samples']}")
        self.stdout.write(f"Prediction kind: {summary['prediction_kind']}")
        if summary.get("target_labels"):
            self.stdout.write("Target labels: " + ", ".join(summary["target_labels"]))
        self.stdout.write(f"Model saved to: {summary['model_path']}")
