FROM python:3.12.0-alpine3.18

MAINTAINER Klemens Schueppert "schueppi@envot.io"

WORKDIR /mesquesh/

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./mesquesh.py /mesquesh/mesquesh.py

ENV PYTHONUNBUFFERED TRUE
ENV HOST localhost
ENV PORT 1883
ENV GRAFANALINK "http://link.to.grafana/d/aFG2XBMSz/eot-devices-selective?orgId=1&var-device_type=%s&var-device_name=%s&var-search=%s&var-searchand=%%23&var-searchor=asdf&from=now-%s&to=now"

ENTRYPOINT python mesquesh.py -host ${HOST} -port ${PORT}
