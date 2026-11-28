# Copyright (c) 2017-2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# checkov:skip=CKV_DOCKER_2:Ensure that HEALTHCHECK instructions have been added to container images
ARG KIWI_VERSION=latest

FROM quay.io/centos/centos:stream10 AS postgres17-buildroot
ARG PG_MAJOR=17
USER 0
RUN set -eux; \
    dnf -y --nodocs install dnf-plugins-core rpm-build; \
    dnf -y --nodocs install \
        "https://download.postgresql.org/pub/repos/yum/reporpms/EL-10-$(uname -m)/pgdg-redhat-repo-latest.noarch.rpm"; \
    dnf -y --disablerepo='pgdg*' --enablerepo=pgdg${PG_MAJOR}-source \
        --setopt=pgdg${PG_MAJOR}-source.baseurl=https://dnf-srpms.postgresql.org/srpms/${PG_MAJOR}/redhat/rhel-10-$(uname -m)/ \
        download --source --destdir=/tmp "postgresql${PG_MAJOR}"; \
    srpm=$(ls /tmp/postgresql${PG_MAJOR}*.src.rpm | sort -V | tail -1); \
    dnf -y --disablerepo='pgdg*' --enablerepo=crb builddep --define "pgmajorversion ${PG_MAJOR}" "$srpm"; \
    rpmbuild --rebuild --define "pgmajorversion ${PG_MAJOR}" --define "_topdir /tmp/rpmbuild" "$srpm"; \
    rpm -Uvh --nodeps --noscripts \
        /tmp/rpmbuild/RPMS/*/postgresql${PG_MAJOR}-${PG_MAJOR}.*.rpm \
        /tmp/rpmbuild/RPMS/*/postgresql${PG_MAJOR}-libs-*.rpm; \
    /usr/pgsql-${PG_MAJOR}/bin/psql --version; \
    /usr/pgsql-${PG_MAJOR}/bin/pg_dump --version; \
    rm -rf /tmp/rpmbuild "$srpm"

FROM quay.io/centos/centos:stream10 AS postgres18-buildroot
ARG PG_MAJOR=18
USER 0
RUN set -eux; \
    dnf -y --nodocs install dnf-plugins-core rpm-build; \
    dnf -y --nodocs install \
        "https://download.postgresql.org/pub/repos/yum/reporpms/EL-10-$(uname -m)/pgdg-redhat-repo-latest.noarch.rpm"; \
    dnf -y --disablerepo='pgdg*' --enablerepo=pgdg${PG_MAJOR}-source \
        --setopt=pgdg${PG_MAJOR}-source.baseurl=https://dnf-srpms.postgresql.org/srpms/${PG_MAJOR}/redhat/rhel-10-$(uname -m)/ \
        download --source --destdir=/tmp "postgresql${PG_MAJOR}"; \
    srpm=$(ls /tmp/postgresql${PG_MAJOR}*.src.rpm | sort -V | tail -1); \
    dnf -y --disablerepo='pgdg*' --enablerepo=crb builddep --define "pgmajorversion ${PG_MAJOR}" "$srpm"; \
    rpmbuild --rebuild --define "pgmajorversion ${PG_MAJOR}" --define "_topdir /tmp/rpmbuild" "$srpm"; \
    rpm -Uvh --nodeps --noscripts \
        /tmp/rpmbuild/RPMS/*/postgresql${PG_MAJOR}-${PG_MAJOR}.*.rpm \
        /tmp/rpmbuild/RPMS/*/postgresql${PG_MAJOR}-libs-*.rpm; \
    /usr/pgsql-${PG_MAJOR}/bin/psql --version; \
    /usr/pgsql-${PG_MAJOR}/bin/pg_dump --version; \
    rm -rf /tmp/rpmbuild "$srpm"

FROM quay.io/centos/centos:stream10 AS postgres19-buildroot
ARG PG_MAJOR=19
USER 0
RUN set -eux; \
    dnf -y --nodocs install dnf-plugins-core rpm-build; \
    dnf -y --nodocs install \
        "https://download.postgresql.org/pub/repos/yum/reporpms/EL-10-$(uname -m)/pgdg-redhat-repo-latest.noarch.rpm"; \
    dnf -y --disablerepo='pgdg*' --enablerepo=pgdg${PG_MAJOR}-source \
        --setopt=pgdg${PG_MAJOR}-source.baseurl=https://dnf-srpms.postgresql.org/srpms/${PG_MAJOR}/redhat/rhel-10-$(uname -m)/ \
        download --source --destdir=/tmp "postgresql${PG_MAJOR}"; \
    srpm=$(ls /tmp/postgresql${PG_MAJOR}*.src.rpm | sort -V | tail -1); \
    dnf -y --disablerepo='pgdg*' --enablerepo=crb builddep --define "pgmajorversion ${PG_MAJOR}" "$srpm"; \
    rpmbuild --rebuild --define "pgmajorversion ${PG_MAJOR}" --define "_topdir /tmp/rpmbuild" "$srpm"; \
    rpm -Uvh --nodeps --noscripts \
        /tmp/rpmbuild/RPMS/*/postgresql${PG_MAJOR}-${PG_MAJOR}.*.rpm \
        /tmp/rpmbuild/RPMS/*/postgresql${PG_MAJOR}-libs-*.rpm; \
    /usr/pgsql-${PG_MAJOR}/bin/psql --version; \
    /usr/pgsql-${PG_MAJOR}/bin/pg_dump --version; \
    rm -rf /tmp/rpmbuild "$srpm"

FROM hub.kiwitcms.eu/kiwitcms/version:$KIWI_VERSION

USER 0
COPY ./etc/pki/rpm-gpg/* /etc/pki/rpm-gpg/
COPY ./etc/yum.repos.d/* /etc/yum.repos.d/
RUN microdnf -y --nodocs install augeas-libs fuse-libs postgresql psmisc restic util-linux-core xmlsec1 xmlsec1-openssl && \
    rpm -Uhv --excludedocs https://s3.amazonaws.com/mountpoint-s3-release/latest/$(uname -m | sed s/aarch64/arm64/)/mount-s3.rpm && \
    microdnf -y --nodocs update && \
    microdnf clean all

RUN mkdir -p /usr/pgsql-16/bin && \
    ln -s /usr/bin/psql    /usr/pgsql-16/bin/psql && \
    ln -s /usr/bin/pg_dump /usr/pgsql-16/bin/pg_dump

COPY --from=postgres17-buildroot /usr/pgsql-17/bin/psql /usr/pgsql-17/bin/pg_dump /usr/pgsql-17/bin/
COPY --from=postgres17-buildroot /usr/pgsql-17/lib/libpq.so.5* /usr/pgsql-17/lib/

COPY --from=postgres18-buildroot /usr/pgsql-18/bin/psql /usr/pgsql-18/bin/pg_dump /usr/pgsql-18/bin/
COPY --from=postgres18-buildroot /usr/pgsql-18/lib/libpq.so.5* /usr/pgsql-18/lib/

COPY --from=postgres19-buildroot /usr/pgsql-19/bin/psql /usr/pgsql-19/bin/pg_dump /usr/pgsql-19/bin/
COPY --from=postgres19-buildroot /usr/pgsql-19/lib/libpq.so.5* /usr/pgsql-19/lib/

HEALTHCHECK CMD [ -d /proc/$(cat /tmp/nginx.pid) ] && [ -d /proc/$(cat /tmp/kiwitcms.pid) ]

RUN useradd --uid 1001 --gid 0 --home-dir /Kiwi kiwitcms
USER 1001

# override NGINX configuration
CMD /Kiwi/bin/docker-entrypoint
COPY --chown=1001:root ./etc/nginx.override /Kiwi/etc/nginx.override
RUN ln -sf /tmp/actual.conf /Kiwi/etc/nginx.conf
ENV NGX_AUTHENTICATED_RATE=300  \
    NGX_AUTHENTICATED_BURST=100 \
    NGX_STATIC_RATE=300         \
    NGX_STATIC_BURST=100        \
    NGX_UPLOADS_RATE=10         \
    NGX_UPLOADS_BURST=10        \
    NGX_ERRORS_RATE=1           \
    NGX_ERRORS_BURST=1          \
    NGX_CSP_SCRIPT_SRC=""       \
    NGX_DENY_INCLUDE="/dev/null"

COPY --chown=1001:root ./bin/* /Kiwi/bin/
COPY --chown=1001:root ./dist/ /Kiwi/dist/

RUN --mount=type=secret,id=PKG_TOKEN,env=PKG_TOKEN \
    pip install --no-cache-dir --only-binary :all: decorator lxml && \
    pip install --no-cache-dir --find-links /Kiwi/dist/ \
        --index-url https://$PKG_TOKEN@pkg.kiwitcms.eu/pypi/ \
        --extra-index-url https://pypi.org/simple/ \
        /Kiwi/dist/kiwitcms_enterprise*.whl

# workaround broken CSS which will break collectstatic
# because they refer to non-existing ../fonts/glyphicons-halflings-regular.eot (no fonts/ directory)
# remove django_tenants/templates/admin/index.html b/c it is ugly and b/c we use grapelli
RUN rm -rf /venv/lib64/python3.14/site-packages/tcms/node_modules/c3/htdocs/ \
           /venv/lib64/python3.14/site-packages/tcms/node_modules/eonasdan-bootstrap-datetimepicker/build/css/bootstrap-datetimepicker-standalone.css \
           /venv/lib64/python3.14/site-packages/tcms/node_modules/bootstrap-touchspin/demo/ \
           /venv/lib64/python3.14/site-packages/django_tenants/templates/admin/index.html

# create missing source-map files. Not critical for UI functionality, see:
# https://developer.mozilla.org/en-US/docs/Tools/Debugger/How_to/Use_a_source_map
RUN touch /venv/lib64/python3.14/site-packages/tcms/node_modules/bootstrap-slider/dependencies/js/jquery.min.map \
          /venv/lib64/python3.14/site-packages/tcms/node_modules/pdfmake/build/browser-module.mjs.map \
          /venv/lib64/python3.14/site-packages/tcms/node_modules/pdfmake/build/module.mjs.map \
          /venv/lib64/python3.14/site-packages/tcms/node_modules/pdfmake/build/pdfkit.browser.mjs.map

# collect static files again
RUN cp /Kiwi/static/ca.crt /Kiwi/ssl/ && \
    /Kiwi/manage.py collectstatic --clear --link --noinput && \
    /Kiwi/manage.py generate_rpc_schema && \
    mv /Kiwi/ssl/ca.crt /Kiwi/static/ && \
    mkdir -p /Kiwi/static/.well-known/acme-challenge/ && \
    mkdir -p /Kiwi/mnt/
