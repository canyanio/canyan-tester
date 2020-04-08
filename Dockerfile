FROM python:3.8-alpine3.10
WORKDIR /src
COPY . /src
RUN python3 setup.py sdist bdist_wheel

FROM python:3.8-alpine3.10
LABEL maintainer="Canyan Engineering Team <team@canyan.io>"
ENV VERSION 1.1.0

COPY ./scripts/wait-for /usr/bin/wait-for
RUN chmod +x /usr/bin/wait-for

COPY --from=0 /src/dist/canyantester-1.1-py3-none-any.whl /tmp/canyantester-1.1-py3-none-any.whl
RUN true && \
    apk add --no-cache --virtual .build-deps gcc python3-dev musl-dev libffi-dev make && \
    pip install /tmp/canyantester-1.1-py3-none-any.whl pytest && \
    apk del --no-cache .build-deps && \
    apk add --no-cache bash jq sipp vim sngrep netcat-openbsd screen curl && \
    rm /tmp/canyantester-1.1-py3-none-any.whl && \
    rm -fr /root/.cache
