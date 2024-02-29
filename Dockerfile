FROM python:3.12-alpine
LABEL MAINTAINER KBase Developer

COPY ./ /kb/module/
WORKDIR /kb/module
# install python modules one at a time so that all deps get resolved properly
RUN apk --update add uwsgi-python3 && \
    pip install --upgrade pip && \
    cat requirements.txt | sed -e '/^\s*#.*$/d' -e '/^\s*$/d' | xargs -n 1 pip install && \
    cat requirements-test.txt | sed -e '/^\s*#.*$/d' -e '/^\s*$/d' | xargs -n 1 pip install && \
    mkdir -p /kb/module/work && \
    chmod -R a+rw /kb/module && \
    cp compile_report.json work/ \
    && \
	chmod a+rx ./scripts/*.sh
    # && \
	# chmod a+rx scripts/entrypoint.sh && \
	# chmod +x scripts/start_server.sh && \
	# chmod +x test/run_tests.sh

ENV PYTHONPATH="/kb/module/lib:$PYTHONPATH"
WORKDIR /kb/module

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD []
