#relevant commands:
#docker build -t <name> .
#docker login (if using dockerhub)
#docker tag local-image:tagname new-repo:tagname
#docker push new-repo:tagname

FROM python:3.9.5-slim-buster

WORKDIR /usr/src/

ADD setup.py .
COPY fpsim/ ./fpsim
COPY ./README.rst .
RUN pip install -e .