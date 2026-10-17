from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from catalog.importer import ImportRejected, import_dataset


class Command(BaseCommand):
    help = "Import the synthetic resource dataset (idempotent, fail-closed, synthetic-only)."

    def add_arguments(self, parser):
        parser.add_argument("--path", default=settings.STP_SYNTHETIC_DATASET)

    def handle(self, *args, **opts):
        try:
            run = import_dataset(opts["path"])
        except ImportRejected as exc:
            raise CommandError(f"REJECTED: {exc} (no rows written)")
        self.stdout.write(f"OK file_sha256={run.file_sha256} created={run.created} unchanged={run.unchanged} inherited_flag={run.inherited_flag}")
