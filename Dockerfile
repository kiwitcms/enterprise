FROM kiwitcms/kiwi

# Install any additional Python dependencies we may have specified
COPY ./requirements.d/ /Kiwi/requirements.d/
RUN for F in /Kiwi/requirements.d/*.txt; do pip install -r $F; done

COPY ./product.py /venv/lib64/python3.6/site-packages/tcms/settings/
# collect static files again
RUN /Kiwi/manage.py collectstatic -c --noinput
