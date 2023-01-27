ARG KIWI_VERSION=latest
FROM kiwitcms/kiwi:$KIWI_VERSION

USER 0
RUN microdnf -y --nodocs install krb5-libs xmlsec1 xmlsec1-openssl && \
    microdnf clean all

USER 1001

COPY ./dist/ /Kiwi/dist/
RUN pip install --no-cache-dir --find-links /Kiwi/dist/ /Kiwi/dist/kiwitcms_enterprise*.whl

# woraround broken CSS which will break collectstatic
# because they refer to non-existing ../fonts/glyphicons-halflings-regular.eot (no fonts/ directory)
# remove django_tenants/templates/admin/index.html b/c it is ugly and b/c we use grapelli
RUN rm -rf /venv/lib64/python3.9/site-packages/tcms/node_modules/c3/htdocs/ \
           /venv/lib64/python3.9/site-packages/tcms/node_modules/eonasdan-bootstrap-datetimepicker/build/css/bootstrap-datetimepicker-standalone.css \
           /venv/lib64/python3.9/site-packages/tcms/node_modules/bootstrap-touchspin/demo/ \
           /venv/lib64/python3.9/site-packages/django_tenants/templates/admin/index.html

# create missing source-map files. Not critical for UI functionality, see:
# https://developer.mozilla.org/en-US/docs/Tools/Debugger/How_to/Use_a_source_map
RUN touch /venv/lib64/python3.9/site-packages/tcms/node_modules/bootstrap-slider/dependencies/js/jquery.min.map

# collect static files again
RUN /Kiwi/manage.py collectstatic --clear --link --noinput
