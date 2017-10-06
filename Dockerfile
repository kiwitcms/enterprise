FROM kiwitcms/kiwi

# Set virtualenv environment variables. This is equivalent to running
# source /env/bin/activate. This ensures the application is executed within
# the context of the virtualenv and will have access to its dependencies.
ENV VIRTUAL_ENV /venv
ENV PATH /venv/bin:$PATH

### customize this image as you wish
# Install additional Python dependencies
#RUN pip install kerberos

COPY ./product.py /venv/lib64/python3.5/site-packages/tcms/settings/
# collect static files again
RUN /Kiwi/manage.py collectstatic -c --noinput


# now remove -devel RPMs used to build Python dependencies
# and also remove everything else, that we don't need
RUN rpm -qa | grep "\-devel" | grep -v python-devel | xargs yum -y remove && \
    yum -y remove gcc cpp centos-release-scl perl-* *-headers pygobject3-base \
           gobject-introspection bind-license iso-codes xml-common && \
    yum clean all

RUN rpm -qa | grep yum | xargs rpm -ev && \
    rpm -qa | grep "^python-" | xargs rpm -ev --nodeps && \
    rpm -ev dbus-python libxml2-python rpm-python pyliblzma pygpgme pyxattr && \
    rm -rf /anaconda-post.log /var/cache/yum /etc/yum* /usr/lib64/python2.7

# todo: remove static & node_modules from under tcms directory
# todo: remove npm & friends
