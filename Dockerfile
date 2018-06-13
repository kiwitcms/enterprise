FROM kiwitcms/kiwi

# Set virtualenv environment variables. This is equivalent to running
# source /env/bin/activate. This ensures the application is executed within
# the context of the virtualenv and will have access to its dependencies.
ENV VIRTUAL_ENV /venv
ENV PATH /venv/bin:$PATH

# Install any additional Python dependencies we may have specified
COPY ./requirements.d/ /Kiwi/requirements.d/
RUN for F in /Kiwi/requirements.d/*.txt; do pip install -r $F; done

# Install any 3rd party Python modules the user may have added
COPY ./libs.d/ /venv/lib64/python3.6/site-packages/tcms/libs/

COPY ./product.py /venv/lib64/python3.6/site-packages/tcms/settings/
# collect static files again
RUN /Kiwi/manage.py collectstatic -c --noinput
