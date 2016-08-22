# Reference: https://hub.docker.com/_/python/

FROM deleidos/vizwiz-python:1.0

RUN apt-get -y update
# remove before release
RUN apt-get -y install vim

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install -r requirements.txt
RUN python3 -m nltk.downloader punkt averaged_perceptron_tagger wordnet stopwords

COPY reasonerserver reasonerserver/
COPY *.ini setup.py /usr/src/app/

RUN pip install -e .

EXPOSE 9001

CMD ["pserve", "/usr/src/app/production.ini" ]
