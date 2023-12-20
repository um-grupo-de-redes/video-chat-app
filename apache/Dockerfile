FROM httpd:2.4-alpine

RUN mkdir -p /usr/local/apache2/conf
COPY 01_http.conf /usr/local/apache2/conf/01_http.conf.bak
COPY 02_https.conf /usr/local/apache2/conf/02_https.conf.bak

COPY start.sh /start.sh
RUN chmod +x /start.sh
CMD /start.sh
