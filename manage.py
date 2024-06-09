#!/usr/bin/env python

# Copyright (c) 2020 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=missing-docstring

import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
