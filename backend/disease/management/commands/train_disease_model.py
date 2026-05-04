from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from disease.training import train_disease_model


class Command(BaseCommand):
    help = "Train the Module 3 MobileNetV2 disease classifier from an image-folder dataset."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--dataset",
            required=True,
            help="Path to the image dataset root folder relative to backend/ or as an absolute path.",
        )
        parser.add_argument(
            "--class-filter",
            default=None,
            help="Optional substring filter such as 'Tomato' to train only matching folders.",
        )
        parser.add_argument(
            "--max-images-per-class",
            type=int,
            default=800,
            help="Maximum number of images to copy from each class folder.",
        )
        parser.add_argument(
            "--epochs",
            type=int,
            default=6,
            help="Number of fine-tuning epochs.",
        )

    def handle(self, *args, **options) -> None:
        dataset_value = options["dataset"]
        dataset_path = Path(dataset_value)
        if not dataset_path.is_absolute():
            dataset_path = Path.cwd() / dataset_path

        if not dataset_path.exists():
            raise CommandError(f"Dataset not found: {dataset_path}")

        try:
            summary = train_disease_model(
                dataset_path,
                class_filter=options["class_filter"],
                max_images_per_class=options["max_images_per_class"],
                epochs=options["epochs"],
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS("Disease model trained successfully."))
        self.stdout.write(f"Samples: {summary['samples']}")
        self.stdout.write("Classes: " + ", ".join(summary["class_names"]))
        self.stdout.write(f"Train accuracy: {summary['train_accuracy']:.4f}")
        self.stdout.write(f"Validation accuracy: {summary['validation_accuracy']:.4f}")
        self.stdout.write(f"Model saved to: {summary['model_path']}")
