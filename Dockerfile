# Copyright (c) 2017-2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# checkov:skip=CKV_DOCKER_2:Ensure that HEALTHCHECK instructions have been added to container images
ARG KIWI_VERSION=latest
FROM hub.kiwitcms.eu/kiwitcms/version:$KIWI_VERSION

USER 0
RUN microdnf -y --nodocs install augeas-libs krb5-libs psmisc xmlsec1 xmlsec1-openssl && \
    microdnf clean all

HEALTHCHECK CMD [ -d /proc/$(cat /tmp/nginx.pid) ] && [ -d /proc/$(cat /tmp/kiwitcms.pid) ]
USER 1001

# override NGINX configuration
CMD /Kiwi/bin/docker-entrypoint
COPY ./etc/nginx.override /Kiwi/etc/nginx.override
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

COPY ./bin/* /Kiwi/bin/
COPY ./dist/ /Kiwi/dist/

ARG PKG_TOKEN
RUN pip install --no-cache-dir --only-binary :all: decorator lxml && \
    pip install --no-cache-dir --find-links /Kiwi/dist/ --no-index /Kiwi/dist/xmlsec*.whl && \
    pip install --no-cache-dir --find-links /Kiwi/dist/ \
        --index-url https://$PKG_TOKEN@pkg.kiwitcms.eu/pypi/ \
        --extra-index-url https://pypi.org/simple/ \
        /Kiwi/dist/kiwitcms_enterprise*.whl

# workaround broken CSS which will break collectstatic
# because they refer to non-existing ../fonts/glyphicons-halflings-regular.eot (no fonts/ directory)
# remove django_tenants/templates/admin/index.html b/c it is ugly and b/c we use grapelli
RUN rm -rf /venv/lib64/python3.12/site-packages/tcms/node_modules/c3/htdocs/ \
           /venv/lib64/python3.12/site-packages/tcms/node_modules/eonasdan-bootstrap-datetimepicker/build/css/bootstrap-datetimepicker-standalone.css \
           /venv/lib64/python3.12/site-packages/tcms/node_modules/bootstrap-touchspin/demo/ \
           /venv/lib64/python3.12/site-packages/django_tenants/templates/admin/index.html

# create missing source-map files. Not critical for UI functionality, see:
# https://developer.mozilla.org/en-US/docs/Tools/Debugger/How_to/Use_a_source_map
RUN touch /venv/lib64/python3.12/site-packages/tcms/node_modules/bootstrap-slider/dependencies/js/jquery.min.map \
          /venv/lib64/python3.12/site-packages/tcms/node_modules/pdfmake/build/module.mjs.map

# collect static files again
RUN cp /Kiwi/static/ca.crt /Kiwi/ssl/ && \
    /Kiwi/manage.py collectstatic --clear --link --noinput && \
    mv /Kiwi/ssl/ca.crt /Kiwi/static/ && \
    mkdir -p /Kiwi/static/.well-known/acme-challenge/
