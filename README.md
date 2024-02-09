[![Tidelift](https://tidelift.com/badges/package/pypi/kiwitcms)](https://tidelift.com/subscription/pkg/pypi-kiwitcms?utm_source=pypi-kiwitcms&utm_medium=github&utm_campaign=enterprise)
[![Become-a-sponsor](https://opencollective.com/kiwitcms/tiers/sponsor/badge.svg?label=sponsors&color=brightgreen)](https://opencollective.com/kiwitcms#contributors)
[![Twitter](https://img.shields.io/twitter/follow/KiwiTCMS.svg)](https://twitter.com/KiwiTCMS)


Kiwi TCMS Enterprise Edition
============================

This repository contains downstream distribution for the
[Kiwi TCMS](http://kiwitcms.org) open source test management
system, dubbed *Enterprise Edition*, which contains the following changes:

* Based on `kiwitcms/kiwi` Docker image
* **Compatible only with PostgreSQL !!!**
* Versioned static files
* NGINX replaced by [OpenResty](https://openresty.org) with embedded
  [Lua](https://github.com/openresty/lua-nginx-module) support
* Add-ons:
  - [django-ses](https://github.com/django-ses/django-ses) - Amazon SES email backend
  - [dj-database-url](https://github.com/jacobian/dj-database-url) - DB configuration
    via `DATABASE_URL`
  - [django-prometheus](https://github.com/korfuri/django-prometheus) - Export Django
    monitoring metrics for Prometheus.io
  - [kiwitcms-github-app](https://github.com/kiwitcms/github-app/) - extra integration
    with GitHub
  - [kiwitcms-tenants](https://github.com/kiwitcms/tenants/) - multi-tenant support
  - [kiwitcms-trackers-integration](https://github.com/kiwitcms/trackers-integration/) -
    integration with extra issue trackers
  - [raven](https://github.com/getsentry/raven-python) - automatic error logs via Sentry
  - [social-auth-app-django](https://github.com/python-social-auth/social-app-django) -
    extra [authentication backends](http://python-social-auth.readthedocs.io/en/latest/backends/index.html#supported-backends)
  - [social-auth-kerberos](https://github.com/kiwitcms/python-social-auth-kerberos/) -
    MIT Kerberos authentication backend
  - [django-python3-ldap](https://github.com/etianen/django-python3-ldap) -
    LDAP authentication backend
  - [Let's Encrypt certbot](https://certbot.eff.org/)
* Supported environment variables, configurable on the container:
  - ``NGX_AUTHENTICATED_RATE``  - req/sec for authenticated URLs
  - ``NGX_AUTHENTICATED_BURST`` - burst rate for authenticated URLs
  - ``NGX_ERRORS_RATE``  - req/sec for URLs resulting in 4xx, 5xx errors
  - ``NGX_ERRORS_BURST`` - burst rate for URLs resulting in 4xx, 5xx errors
  - ``NGX_STATIC_RATE``  - req/sec for static files
  - ``NGX_STATIC_BURST`` - burst rate for static files
  - ``NGX_UPLOADS_RATE`` - req/sec for uploaded files
  - ``NGX_UPLOADS_BURST``- burst rate for uploaded files


While the software itself is open source we do not provide public
access to the resulting `kiwitcms/enterprise` container image.
This is made available only to our subscribers, see https://kiwitcms.org/containers/
and https://kiwitcms.org/#subscriptions for more information.

If you want to use Kiwi TCMS free of charge head to http://kiwitcms.org!


Initial configuration
---------------------

1. Create your *docker-compose.yml* similar to our
   [docker-compose.testing](https://github.com/kiwitcms/enterprise/blob/master/docker-compose.testing).
   Make sure to define the `KIWI_TENANTS_DOMAIN` environment variable.
2. Once your containers are running execute:

    ```
    docker exec -it web /Kiwi/manage.py initial_setup
    ```

   **NOTE:** the domain value provided during `initial_setup` should be the same or one-level up from
   the value of `KIWI_TENANTS_DOMAIN`.

For more information see
https://kiwitcms.readthedocs.io/en/latest/installing_docker.html#initial-configuration-of-running-container
and https://github.com/kiwitcms/tenants/#first-boot-configuration

3. For initial configuration of Let's Encrypt SSL certificates execute the command:

    ```
    docker exec -it -u0 web /Kiwi/bin/lets-encrypt <secondary-fqdn> <tertiary-fqdn> <etc>
    ```

   - the value of `KIWI_TENANTS_DOMAIN` will be the primary domain on the SSL certificate
   - additional domain names may be specified as arguments
   - **WARNINGS:**:
       - true
         [wildcard certificates](https://letsencrypt.org/docs/faq/#does-let-s-encrypt-issue-wildcard-certificates)
         are only possible via certbot's DNS plugins while this script uses `--webroot`
       - for full control you may want to execute the `certbot` command directly
       - you need to bind-mount `/etc/letsencrypt/` and `/Kiwi/ssl/` inside the container
         if you want the Let's Encrypt certificates to persist a restart


Hacking and customization
-------------------------

In case you need to customize and extend the container image we recommend to use the
existing image as a baseline and incorporate all of your changes on top of it. For example
create a `Dockerfile` like so:

```
FROM quay.io/kiwitcms/enterprise

# your own changes go here
```

then build your own image with the command
`docker build -f Dockerfile.customized -t kiwitcms/customized .`.


Rebuilding from source is not recommended b/c it will result in slightly different images
compared to what we provide online to subscribers. There is no way for the Kiwi TCMS team
to test or provide any guarantees on container images rebuilt by anyone but us!

In the event that you need to do so then use the `make docker-image` command and watchout
for errors during the build process. The buildroot generally needs Python 3,
the `make` and `docker` commands, the `wheel` and `twine` Python packages.


Changelog
---------

### v13.0-mt (17 Jan 2024)

- Based on Kiwi TCMS v13.0
- Update container runtime from Python 3.9 to Python 3.11
- Update django-ses from 3.5.0 to 3.5.2
- Update kiwitcms-github-app from 1.5.1 to 1.6.0
- Update kiwitcms-tenants from 2.5.2 to 2.6.0
- Update kiwitcms-trackers-integration from 0.6.0 to 0.7.0
- Update social-auth-kerberos from 0.2.4 to 0.3.0
- Start testing with upstream Postgres container image
- Assert that Personal API Tokens is listed in PLUGINS menu
- Adjust search path for images during test


### v12.7-mt (25 Nov 2023)

- Based on Kiwi TCMS v12.7
- Update kiwitcms-tenants from 2.5.1 to 2.5.2
- Update kiwitcms-trackers-integration from 0.5.0 to 0.6.0

    Provides functionality for personal API tokens. Accessible via
    PLUGINS -> Personal API tokens menu!

    WARNING: in order for users to be able to define personal API tokens
    for 3rd party bug-trackers they will need to be assigned permissions.

    Database administrators should consider granting the following
    permissions::

        tracker_integrations | api token | Can add api token
        tracker_integrations | api token | Can change api token
        tracker_integrations | api token | Can delete api token
        tracker_integrations | api token | Can view api token

    either individually per-user basis or via groups!

- Update python3-saml from 1.15.0 to 1.16.0
- Update social-auth-app-django from 5.2.0 to 5.4.0


### v12.6.1-mt (31 Aug 2023)

- Based on Kiwi TCMS v12.6.1
- Update dj-database-url from 2.0.0 to 2.1.0



### v12.5-mt (04 Jul 2023)

- Based on Kiwi TCMS v12.5
- Update django-python3-ldap from 0.15.4 to 0.15.5
- Install django-prometheus inside container
- Pin Selenium to 4.9.1 b/c of failures with 4.10.0


### v12.4-mt (06 Jun 2023)

- Based on Kiwi TCMS v12.4
- Update kiwitcms-trackers-integration from 0.4.0 to 0.5.0


### v12.3-mt (22 May 2023)

- Based on Kiwi TCMS v12.3
- Update dj-database-url from 1.3.0 to 2.0.0
- Update django-ses from 3.3.0 to 3.5.0
- Update kiwitcms-tenants from 2.5.0 to 2.5.1
- Explicitly set permissions to read-all
- Enable checkov linter


### v12.2-mt (23 Apr 2023)

- Based on Kiwi TCMS v12.2
- Update social-auth-app-django from 5.0.0 to 5.2.0


### v12.1-mt (29 Mar 2023)

- Based on Kiwi TCMS v12.1
- Update dj-database-url from 1.2.0 to 1.3.0
- Update kiwitcms-github-app from 1.4.1 to 1.5.1
- Update kiwitcms-trackers-integration from 0.3.0 to 0.4.0
- Add test for missing migrations


### v12.0-mt (15 Feb 2023)

- Based on Kiwi TCMS v12.0
- Update kiwitcms-github-app from 1.4.0 to 1.4.1
- Update kiwitcms-tenants from 2.4.0 to 2.5.0



### v11.7-mt (03 Jan 2023)

- Based on Kiwi TCMS v11.7
- Update dj-database-url from 1.0.0 to 1.2.0
- Update django-python3-ldap from 0.15.3 to 0.15.4
- Update django-ses from 3.2.2 to 3.3.0
- Update kiwitcms-tenants from 2.3.2 to 2.4.0 to
  allow customization of tenant logo in navigation
- Update python3-saml from 1.14.0 to 1.15.0
- Add CodeQL workflow for GitHub code scanning
- Adjust ldap commands for Ubuntu 22.04.1 during testing in CI



### v11.6-mt (08 Nov 2022)

- Based on Kiwi TCMS v11.6
- Update containers for RHEL 9, CentOS Stream 9 and Python 3.9
- Update actions/checkout from 2 to 3
- Update django-ses from 3.1.2 to 3.2.2
- Update kiwitcms-tenants from 2.3.1 to 2.3.2
- Update kiwitcms-trackers-integration from 0.2.0 to 0.3.0.
  Supports integration with OpenProject and Mantis BT. Closes
  [Issue #2203](<https://github.com/kiwitcms/Kiwi/issues/2203>) and
  [Issue #879](<https://github.com/kiwitcms/Kiwi/issues/879>)



### v11.5.1-mt (10 Sep 2022)

- Update kiwitcms-tenants from 2.3.0 to 2.3.1



### v11.5-mt (06 Sep 2022)

- Based on Kiwi TCMS v11.5
- Update django-python3-ldap from 0.15.2 to 0.15.3
- Update django-ses from 3.1.0 to 3.1.2
- Update kiwitcms-tenants from 2.1.1 to 2.3.0
- Update kiwitcms-github-app from 1.3.3 to 1.4.0



### v11.4-mt (03 Aug 2022)

- Based on Kiwi TCMS v11.4
- Update django-python3-ldap from 0.13.1 to 0.15.2
- Update django-ses from 3.0.1 to 3.1.0
- Update dj-database-url from 0.5.0 to 1.0.0
- Add more icons for extra GitHub login backends
- Add images for various Google login backends



### v11.3.1-mt (27 April 2022)

- Based on Kiwi TCMS v11.3
- Update kiwitcms-tenants from 2.1.0 to 2.1.1 to fix a bug in
  tenant groups admin page


### v11.3-mt (27 April 2022)

- Based on Kiwi TCMS v11.3
- Update django-ses from 2.6.0 to 3.0.1
- Update kiwitcms-tenants from 1.11.0 to 2.1.0 for
  tenant groups support


### v11.2-mt (09 March 2022)

- Based on Kiwi TCMS v11.2
- Update django-ses from 2.4.0 to 2.6.0
- Update python3-saml from 1.13.0 to 1.14.0
- Revert "Use django.contrib.staticfiles.storage from Django==3.2.12".
  Instead use the implementation from latest Django version. Closes
  [Issue #140](https://github.com/kiwitcms/enterprise/issues/140)
- Start building kiwitcms/enterprise on aarch64
- Add changelog check & docker release automation
- Add test for PSA login URLs on login page. References
  [Issue #83](https://github.com/kiwitcms/enterprise/issues/83)
- Add SAML & Azure AD logo images
- Update GitHub Actions
- Hard-code testing with Keycloak 16.1.1 to workaround significant differences
  with Keycloak v17 container


### v11.1-mt (02 February 2022)

- Based on Kiwi TCMS v11.1
- Update kiwitcms-github-app from 1.3.2 to 1.3.3
- Update django-ses from 2.3.1 to 2.4.0
- Update python3-saml from 1.12.0 to 1.13.0
- Workaround UnicodeDecodeError while building the docker image

### v11.0-mt (24 January 2022)

- Based on Kiwi TCMS v11.0
- Update kiwitcms-tenants from 1.8.0 to 1.11.0

### v10.5.1-mt (05 January 2022)

- Based on Kiwi TCMS v10.5
- Update django-python3-ldap from 0.13.0 to 0.13.1
- Update kiwitcms-github-app from 1.3.1 to 1.3.2

### v10.5-mt (25 November 2021)

- Based on Kiwi TCMS v10.5
- Update django-python3-ldap from 0.12.0 to 0.12.1
- Update django-ses from 2.3.0 to 2.3.1
- Update kiwitcms-tenants from 1.7.0 to 1.8.0


### v10.4.1-mt (05 October 2021)

- Update kiwitcms-github-app from 1.3.0 to 1.3.1


### v10.4-mt (04 October 2021)

- Based on Kiwi TCMS v10.4
- Update django-ses from 2.2.1 to 2.3.0
- Update python3-saml from 1.11.0 to 1.12.0
- Update social-auth-app-django from 4.0.0 to 5.0.0
- Use initial_setup during testing. Closes
  [Issue #88](https://github.com/kiwitcms/enterprise/issues/88)
- Fix new pylint issues and start using f-strings
- Test "ADMIN -> Users and Groups" menu redirect


### v10.3-mt (11 August 2021)

- Based on Kiwi TCMS v10.3
- Container image based on Red Hat Universal Base Image
- Update django-ses from 2.1.1 to 2.2.1
- Update python3-saml from 1.10.1 to 1.11.0
- Add GitLab login icon


### v10.2-mt (11 July 2021)

- Based on Kiwi TCMS v10.2
- Update django-ses from 2.0.0 to 2.1.1
- Update django-python3-ldap from 0.11.4 to 0.12.0
- Update documentation around initial config


### v10.1.1-mt (01 July 2021)

- Based on Kiwi TCMS v10.1
- Fix URL to Python Social Auth documentation
- Support read-only view on tenants for anonymous users. Contains a
  database migration to rename `on_trial` field to `publicly_readable`
- Document initial configuration. Site administrators should add the
  `tenants.change_tenant` permission to users/groups who are allowed
  to make their tenants publicly visible. Fixes
  [Issue #87](https://github.com/kiwitcms/enterprise/issues/87),
  References
  [Issue #88](https://github.com/kiwitcms/enterprise/issues/88)
- Document the build process. Fixes
  [Issue #89](https://github.com/kiwitcms/enterprise/issues/89)
- Verify support for Keycloak logins. Fixes
  [Issue #86](https://github.com/kiwitcms/enterprise/issues/86)
- Update kiwitcms-github-app from 1.2.4 to 1.3.0
- Update kiwitcms-tenants from 1.5.0 to 1.6.0


### v10.1-mt (18 May 2021)

- Based on Kiwi TCMS v10.1
- Container image built with Python 3.8
- Update kiwitcms-tenants from 1.4.3 to 1.4.4


### v10.0.1-mt (29 Apr 2021)

- Based on Kiwi TCMS v10.0
- Update django-ses from 1.0.3 to 2.0.0
- Add python3-saml to dependencies, needed by Python Social Auth SAML backend


### v10.0-mt (02 Mar 2021)

- Based on Kiwi TCMS v10.0
- Update kiwitcms-github-app from 1.2.2 to 1.2.4
- Update kiwitcms-tenants from 1.4.2 to 1.4.3
- Update django-python3-ldap from 0.11.3 to 0.11.4


### v9.0-mt (12 Jan 2021)

- Based on Kiwi TCMS v9.0
- Update kiwitcms-github-app from 1.2.1 to 1.2.2
- Update kiwitcms-tenants from 1.3.1 to 1.4.2


### v8.9-mt (07 Dec 2020)

- Based on Kiwi TCMS v8.9


### v8.8-mt (07 Nov 2020)

- Based on Kiwi TCMS v8.8
- Update kiwitcms-github-app from 1.2 to 1.2.1


### v8.7-mt (16 Sep 2020)

- Based on Kiwi TCMS v8.7
- Overrides for setting ``PUBLIC_VIEWS`` have been removed b/c this
  setting has been removed upstream
- Update django-ses from 1.0.2 to 1.0.3
- Update kiwitcms-github-app from 1.1 to 1.2
- Update kiwitcms-tenants from 1.2.1 to 1.3.1


### v8.6-mt (23 Aug 2020)

- Based on Kiwi TCMS v8.6


### v8.5.2-mt (06 Aug 2020)

- Update django-ses from 1.0.1 to 1.0.2
- Update kiwitcms-github-app from 1.0 to 1.1


### v8.5.1-mt (24 July 2020)

- Based on Kiwi TCMS v8.5
- Update kiwitcms-tenants from 1.2 to 1.2.1


### v8.5-mt (10 July 2020)

- Based on Kiwi TCMS v8.5
- Update django-ses from 0.8.14 to 1.0.1
- Update kiwitcms-tenants from 1.1.1 to 1.2
- Update social-auth-app-django from 3.4.0 to 4.0.0
- Start tagging non-Enterprise images of `kiwitcms/kiwi` - will be provided
  via separate private repository for enterprise customers


### v8.4-mt (03 June 2020)

- Based on Kiwi TCMS v8.4
- Update social-auth-app-django from 3.1.0 to 3.4.0
- Add django-python3-ldap add-on for LDAP logins


### v8.3-mt (27 Apr 2020)

- Convert into a proper Kiwi TCMS plugin before installing into docker image
- Update kiwitcms-tenants from 1.0.1 to 1.1.1
- Ship with kiwitcms-github-app plugin
- Add icon for kerberos login backend
- Add translation source strings
- Add ``tcms_settings_dir/`` like other plugins
- Make `enterprise.py` settings idempotent
- Update LICENSE to GPLv3
- Fix pyllint issues
- Add tests in CI
