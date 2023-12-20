#!/bin/sh

set -o errexit
set -o pipefail
set -o nounset

FULLCHAIN=/usr/local/apache2/live/${SERVER_NAME}/fullchain.pem
PRIVKEY=/usr/local/apache2/live/${SERVER_NAME}/privkey.pem

# Delete the default.conf file
if [ -f "/usr/local/apache2/conf/default.conf" ] ; then
    rm "/usr/local/apache2/conf/default.conf"
fi

# Substitute placeholders with current environment variables
export DOLLAR="$"

envsubst < /usr/local/apache2/conf/01_http.conf.bak | tee /usr/local/apache2/conf/01_http.conf.bak.bak > /dev/null 2>&1
envsubst < /usr/local/apache2/conf/02_https.conf.bak | tee /usr/local/apache2/conf/02_https.conf.bak.bak > /dev/null 2>&1

# Enable "/.well-known/acme-challenge/" endpoint
cp /usr/local/apache2/conf/01_http.conf.bak.bak /usr/local/apache2/conf/01_http.conf
echo "'/.well-known/acme-challenge/' endpoint enabled."

# TODO: começar apache em paralelo
nginx -g "daemon off;" &

# Wait for SSL certificates before enabling HTTPS
until [ -f ${FULLCHAIN} ]
do
     sleep 1
done

until [ -f ${PRIVKEY} ]
do
     sleep 1
done

# Enable 02_https.conf
cp /usr/local/apache2/conf/02_https.conf.bak.bak /usr/local/apache2/conf/02_https.conf
# TODO: reload apache
nginx -s reload

echo "Enabled 02_https.conf."

# Sleeps while keeping the ssl certificates up to date
trap exit TERM

while true
do
    # The SSL certificates are renewed by certbot about 30 days before the expire date,
    # so it should be okay to reload nginx in 0h to 24h after the renew.
    sleep 24h & wait ${!}
    # TODO: reload apache
    nginx -s reload
done
