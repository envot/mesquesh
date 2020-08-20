FROM python:3.7.9-alpine3.12

MAINTAINER Klemens Schueppert "schueppi@envot.io"

WORKDIR /mesquesh/

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./mesquesh.py /mesquesh/mesquesh.py

ENV PYTHONUNBUFFERED TRUE
ENV HOST localhost
ENV PORT 1883

ENTRYPOINT python mesquesh.py -host ${HOST} -port ${PORT}
