FROM kiwitcms/kiwi

USER 0
RUN sed -i "s/enabled=0/enabled=1/" /etc/yum.repos.d/CentOS-Linux-PowerTools.repo && \
    dnf -y --setopt=tsflags=nodocs install \
    gcc krb5-devel python38-devel \
    libxml2-devel xmlsec1-devel xmlsec1-openssl-devel libtool-ltdl-devel && \
    dnf clean all

USER 1001

COPY ./dist/kiwitcms_enterprise*.whl /Kiwi/
RUN pip install --no-cache-dir /Kiwi/kiwitcms_enterprise*.whl

# woraround broken CSS which will break collectstatic
# because they refer to non-existing ../fonts/glyphicons-halflings-regular.eot (no fonts/ directory)
# remove django_tenants/templates/admin/index.html b/c it is ugly and b/c we use grapelli
RUN rm -rf /venv/lib64/python3.8/site-packages/tcms/node_modules/c3/htdocs/ \
           /venv/lib64/python3.8/site-packages/tcms/node_modules/eonasdan-bootstrap-datetimepicker/build/css/bootstrap-datetimepicker-standalone.css \
           /venv/lib64/python3.8/site-packages/tcms/node_modules/bootstrap-touchspin/demo/ \
           /venv/lib64/python3.8/site-packages/django_tenants/templates/admin/index.html

# collect static files again
RUN /Kiwi/manage.py collectstatic --clear --link --noinput
