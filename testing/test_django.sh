#!/bin/bash

# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# Run the Django test suite shipped with this package, inside the container.
# This exercises the add-on code the same way the container does, using the
# real enterprise settings and the database started via docker compose.

# Note: execute this file from the project root directory

. /usr/share/beakerlib/beakerlib.sh

rlJournalStart
    rlPhaseStartTest "Django tests inside the container"
        rlRun -t -c "docker compose -f docker-compose.testing up -d db web"

        # give the database and the container time to come up
        sleep 10

        rlRun -t -c "docker exec -i web /Kiwi/manage.py test -v 2 tcms_enterprise"
    rlPhaseEnd

    rlPhaseStartCleanup
        rlRun -t -c "docker compose -f docker-compose.testing down"
    rlPhaseEnd
rlJournalEnd

rlJournalPrintText
