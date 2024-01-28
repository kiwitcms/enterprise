#!/bin/bash

. /usr/share/beakerlib/beakerlib.sh

assert_up_and_running() {
    sleep 10
    # HTTP redirects; HTTPS displays the login page
    rlRun -t -c "curl       -o- http://testing.example.bg:8080/  | grep '301 Moved Permanently'"
    rlRun -t -c "curl -k -L -o- https://testing.example.bg:8443/ | grep 'Welcome to Kiwi TCMS'"
}

rlJournalStart
    rlPhaseStartTest "Sanity test - boot the docker image"
        rlRun -t -c "docker-compose -f docker-compose.testing up -d"
        sleep 5

        IP_ADDRESS=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' web)
        rlLogInfo "--- testing.example.bg: $IP_ADDRESS --"
        rlRun -t -c "sudo sh -c \"echo '$IP_ADDRESS    testing.example.bg     empty.testing.example.bg' >> /etc/hosts\""

        KC_ADDRESS=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' keycloak_server)
        rlLogInfo "--- kc.example.bg: $KC_ADDRESS --"

        # Kiwi TCMS container needs to know how to resolve the Keycloak server address
        rlRun -t -c "docker exec -u 0 -i web /bin/bash -c \"echo '$KC_ADDRESS    kc.example.bg' >> /etc/hosts\""
    rlPhaseEnd

    rlPhaseStartTest "Sanity test - initial configuration"
        # need to monkey-patch createsuperuser.py b/c it rejects input when not using a TTY
        rlRun -t -c 'docker exec -i web sed -i "s/raise NotRunningInTTYException/pass/" /venv/lib64/python3.11/site-packages/django/contrib/auth/management/commands/createsuperuser.py'
        rlRun -t -c 'docker exec -i web sed -i "s/getpass.getpass/input/" /venv/lib64/python3.11/site-packages/django/contrib/auth/management/commands/createsuperuser.py'
        rlRun -t -c 'echo -e "super-root\nroot@example.com\nsecret-2a9a34cd-e51d-4039-b709-b45f629a5595\nsecret-2a9a34cd-e51d-4039-b709-b45f629a5595\ntesting.example.bg\n" | docker exec -i web /Kiwi/manage.py initial_setup'

        # assert only after initial configuration has been applied
        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartTest "Sanity test - missing migrations"
        rlRun -t -c "docker exec -i web /Kiwi/manage.py makemigrations --check"
    rlPhaseEnd

    rlPhaseStartTest "Sanity test - download login page"
        rlRun -t -c "curl -k -L -o page.html https://testing.example.bg:8443/"
    rlPhaseEnd

    rlPhaseStartTest "Sanity test - check page.html"
        # version is Enterprise
        rlAssertGrep "Version.*-Enterprise" page.html

        # plugins are listed
        rlAssertGrep 'href="/admin/trackers_integration/apitoken/' page.html
        rlAssertGrep 'href="/kiwitcms_tenants/' page.html
        rlAssertGrep 'href="/kiwitcms_github_app/' page.html

        # template override for social icons
        rlAssertGrep "or Continue With" page.html

        # social backends are listed
        # for ICON in tcms_enterprise/static/images/social_auth/backends/*.png; do
        #    BACKEND=`basename $ICON | sed 's/.png//'`
        # check only the backends enabled in test_settings.py b/c the directory above
        # contains more images than backends which can be enabled during testing
        for BACKEND in kerberos keycloak gitlab github github-app fedora; do
            rlAssertGrep "/login/$BACKEND/" page.html
            rlAssertGrep "<img src='/static/images/social_auth/backends/$BACKEND.*.png'" page.html
        done

        # social icons are present
        for URL in `cat page.html | grep "/static/images/social_auth/backends/" | cut -d= -f2 | cut -d"'" -f2`; do
            rlLogInfo "Verify image $URL is present"
            rlRun -t -c "curl -k -f -o /dev/null https://testing.example.bg:8443/$URL"
        done

        # social icons point to correct backend login URL, even with port
        for BACKEND in `cat page.html | grep "/static/images/social_auth/backends/" | cut -d= -f2 | cut -d"'" -f2 | cut -f6 -d/ | cut -f1 -d.`; do
            rlLogInfo "Verify $BACKEND login is present"
            rlAssertGrep "https://testing.example.bg/login/$BACKEND/?next=/" page.html
        done
    rlPhaseEnd

    rlPhaseStartTest "Sanity test - LDAP login and sync"
        LDAP_ADDRESS=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' openldap_server)

        # import users from the local config file and query the LDAP server
        rlRun -t -c "ldapadd -x -H ldap://$LDAP_ADDRESS:389 -D cn=Manager,dc=example,dc=com -w admin -f testing/ldap.ldif"
        rlRun -t -c "ldapsearch -x -LLL -H ldap://$LDAP_ADDRESS:389 -b dc=example,dc=com objectClass=person"

        rlRun -t -c "robot testing/ldap.robot"

        rlRun -t -c "docker exec -i web /Kiwi/manage.py ldap_sync_users"
        rlRun -t -c "cat testing/ldap.py | docker exec -i web /Kiwi/manage.py shell"
    rlPhaseEnd

    rlPhaseStartTest "Sanity test - container is healthy"
        STATE=$(docker inspect web | jq -r ".[].State.Health.Status")
        rlAssertEquals "container state is healthy" "$STATE" "healthy"
    rlPhaseEnd

    rlPhaseStartTest "Container restart"
        rlRun -t -c "docker-compose -f docker-compose.testing restart"

        STATE=$(docker inspect web | jq -r ".[].State.Health.Status")
        rlAssertEquals "container state is healthy" "$STATE" "starting"

        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartTest "Sanity test - ADMIN -> Users and Groups menu"
        # WARNING: reuses username/password from the LDAP test above !!!
        rlRun -t -c "cat testing/configure_tenant_users.py | docker exec -i web /Kiwi/manage.py shell"
        rlRun -t -c "robot testing/admin_users_groups_menu.robot"
    rlPhaseEnd

    rlPhaseStartTest "Sanity test - Keycloak login"
        rlRun -t -c "robot testing/keycloak.robot"
    rlPhaseEnd

    rlPhaseStartCleanup
        rlRun -t -c "docker kill keycloak_server"
        rlRun -t -c "docker-compose -f docker-compose.testing down"
        if [ -n "$ImageOS" ]; then
            rlRun -t -c "docker volume rm enterprise_db_data"
        fi
    rlPhaseEnd
rlJournalEnd

rlJournalPrintText
