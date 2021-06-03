FROM ubuntu:16.04

COPY .ci/requirements_linux.txt /tmp/

RUN apt-get update \
    && apt-get install -y git \
    && pip3 install --requirement /tmp/requirements_linux.txt
