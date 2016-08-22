# Self contained demo

FROM jetty:9.3-jre8

RUN mkdir /var/lib/jetty/webapps/ROOT
COPY dist /var/lib/jetty/webapps/ROOT/

RUN chown -R jetty:jetty /var/lib/jetty/webapps/
