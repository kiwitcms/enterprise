# Copyright (c) 2025 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from csv_export.views import CSVExportView
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from tcms.kiwi_auth.admin import KiwiUserAdmin


User = get_user_model()  # pylint: disable=invalid-name


class EnterpriseUserAdmin(KiwiUserAdmin):
    actions = ("deactivate_selected", "export_as_csv")

    @admin.action(
        permissions=["view"],
        description=_("Export as CSV"),
    )
    def export_as_csv(self, request, queryset):
        view = CSVExportView(
            queryset=queryset,
            fields=(
                "pk",
                "username",
                "email",
                "first_name",
                "last_name",
            ),
        )
        return view.get(request)


admin.site.unregister(User)
admin.site.register(User, EnterpriseUserAdmin)
