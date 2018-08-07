FROM kiwitcms/kiwi

# Install any additional Python dependencies
COPY ./requirements.d/ /Kiwi/requirements.d/
RUN for F in /Kiwi/requirements.d/*.txt; do pip install --no-cache-dir -r $F; done

COPY ./ee_urls.py /venv/lib64/python3.6/site-packages/tcms/ee_urls.py
COPY ./local_settings.py /venv/lib64/python3.6/site-packages/tcms/settings/

# collect static files again
RUN /Kiwi/manage.py collectstatic -c --noinput
