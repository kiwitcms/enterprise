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
