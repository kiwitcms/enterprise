FROM kiwitcms/kiwi

USER 0
RUN dnf -y --setopt=tsflags=nodocs install \
    gcc krb5-devel python3-devel && \
    yum clean all

USER 1001

# Install any additional Python dependencies
COPY ./requirements.txt /Kiwi/
RUN pip install --no-cache-dir -r /Kiwi/requirements.txt

COPY ./enterprise.py /venv/lib64/python3.6/site-packages/tcms/settings/local_settings_dir/
COPY ./tcms_enterprise/  /venv/lib64/python3.6/site-packages/tcms_enterprise/
COPY ./templates.d/ /venv/lib64/python3.6/site-packages/tcms/ee_templates/
COPY ./static.d/    /venv/lib64/python3.6/site-packages/tcms/ee_static/

# woraround broken CSS which will break collectstatic
# because they refer to non-existing ../fonts/glyphicons-halflings-regular.eot (no fonts/ directory)
# remove django_tenants/templates/admin/index.html b/c it is ugly and b/c we use grapelli
RUN rm -rf /venv/lib64/python3.6/site-packages/tcms/node_modules/c3/htdocs/ \
           /venv/lib64/python3.6/site-packages/tcms/node_modules/eonasdan-bootstrap-datetimepicker/build/css/bootstrap-datetimepicker-standalone.css \
           /venv/lib64/python3.6/site-packages/tcms/node_modules/bootstrap-touchspin/demo/ \
           /venv/lib64/python3.6/site-packages/django_tenants/templates/admin/index.html

# collect static files again
RUN /Kiwi/manage.py collectstatic --clear --link --noinput
