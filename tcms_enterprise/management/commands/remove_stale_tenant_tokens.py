# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.utils import timezone
from django_tenants.utils import get_tenant_model, tenant_context

from oauth2_provider.management.commands.cleartokens import (
    Command as ClearTokensCommand,
)


class Command(ClearTokensCommand):
    help = "Remove expired OAuth tokens for all tenants!"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Don't remove anything, just report what would be removed",
        )

    def handle(self, *args, **kwargs):
        dry_run = kwargs["dry_run"]

        output = None
        if kwargs["verbosity"]:
            output = self.stdout

        for tenant in get_tenant_model().objects.all():
            if output:
                output.write(
                    f"\n\n {timezone.now()} === Removing tokens"
                    f" for tenant '{tenant.schema_name}' === dry run: {dry_run} ==="
                )

            if dry_run:
                if output:
                    output.write("Dry run: skipping removal")
            else:
                with tenant_context(tenant):
                    super().handle(*args, **kwargs)

            if output:
                output.write(
                    f"\n\n {timezone.now()} === End removing tokens"
                    f" for tenant '{tenant.schema_name}' ==="
                )
