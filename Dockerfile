FROM python:3.9-alpine

ENV PYTHONUNBUFFERED 1

RUN mkdir /plaxt

WORKDIR /plaxt

COPY requirements.txt /plaxt/
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt
COPY . /plaxt/

RUN chmod +x entrypoint.sh

ENTRYPOINT ["/plaxt/entrypoint.sh"]

VOLUME /config
