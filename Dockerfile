FROM kiwitcms/kiwi

USER 1001

# Install any additional Python dependencies
COPY ./requirements.d/ /Kiwi/requirements.d/
RUN for F in /Kiwi/requirements.d/*.txt; do pip install --no-cache-dir -r $F; done

COPY ./ee_urls.py  /venv/lib64/python3.6/site-packages/tcms/
COPY ./pipeline.py /venv/lib64/python3.6/site-packages/tcms/
COPY ./local_settings.py /venv/lib64/python3.6/site-packages/tcms/settings/
COPY ./templates.d/ /venv/lib64/python3.6/site-packages/tcms/ee_templates/
COPY ./static.d/    /venv/lib64/python3.6/site-packages/tcms/ee_static/

# woraround broken CSS which will break collectstatic
# because they refer to non-existing ../fonts/glyphicons-halflings-regular.eot (no fonts/ directory)
RUN rm -rf /venv/lib64/python3.6/site-packages/tcms/node_modules/c3/htdocs/ \
           /venv/lib64/python3.6/site-packages/tcms/node_modules/eonasdan-bootstrap-datetimepicker/build/css/bootstrap-datetimepicker-standalone.css \
           /venv/lib64/python3.6/site-packages/tcms/node_modules/bootstrap-touchspin/demo/

# collect static files again
RUN /Kiwi/manage.py collectstatic -c --noinput
