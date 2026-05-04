from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from crop.training import train_crop_model


class Command(BaseCommand):
    help = "Train the crop recommendation model from a CSV dataset."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--dataset",
            default="data/crop_recommendation.csv",
            help="Path to the crop recommendation CSV dataset relative to backend/.",
        )
        parser.add_argument(
            "--trainer",
            default="sklearn-mlp",
            choices=["sklearn-mlp", "notebook-mlp", "notebook-transformer"],
            help="Training backend to use for the crop recommendation model.",
        )

    def handle(self, *args, **options) -> None:
        dataset_value = options["dataset"]
        dataset_path = Path(dataset_value)
        if not dataset_path.is_absolute():
            dataset_path = Path.cwd() / dataset_path

        if not dataset_path.exists():
            raise CommandError(f"Dataset not found: {dataset_path}")

        summary = train_crop_model(dataset_path, trainer=options["trainer"])
        self.stdout.write(self.style.SUCCESS("Crop model trained successfully."))
        self.stdout.write(f"Samples: {summary['samples']}")
        self.stdout.write(f"Classes: {', '.join(summary['classes'])}")
        self.stdout.write(f"Trainer: {summary['trainer']}")
        if summary["validation_accuracy"] is not None:
            self.stdout.write(f"Validation accuracy: {summary['validation_accuracy']}")
        self.stdout.write(f"Model saved to: {summary['model_path']}")
