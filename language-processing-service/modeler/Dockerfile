# Reference: https://hub.docker.com/_/python/

FROM deleidos/vizwiz-python:1.0

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install -r requirements.txt

COPY modelerserver modelerserver/
COPY *.ini setup.py /usr/src/app/

RUN python /usr/src/app/setup.py install
WORKDIR /usr/src/app/modelerserver/domainmodeler/python-goose/
RUN python setup.py install
WORKDIR /usr/src/app/modelerserver/domainmodeler/news-corpus-builder/
RUN python setup.py install
WORKDIR /usr/src/app
RUN pip install -e .


EXPOSE 9002

CMD ["pserve", "/usr/src/app/production.ini" ]
