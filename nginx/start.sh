#!/bin/sh

set -o errexit
set -o pipefail
set -o nounset

FULLCHAIN=/etc/nginx/ssl/live/leomichalski.xyz/fullchain.pem
PRIVKEY=/etc/nginx/ssl/live/leomichalski.xyz/privkey.pem

# Delete the default.conf file
if [ -f "/etc/nginx/conf.d/default.conf" ] ; then
    rm "/etc/nginx/conf.d/default.conf"
fi

# Substitute placeholders with current environment variables
export DOLLAR="$"

# Enable "/.well-known/acme-challenge/" endpoint
cp /etc/nginx/conf.d/01_http.conf.bak /etc/nginx/conf.d/01_http.conf
echo "'/.well-known/acme-challenge/' endpoint enabled."

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
cp /etc/nginx/conf.d/02_https.conf.bak /etc/nginx/conf.d/02_https.conf
nginx -s reload

echo "Enabled 02_https.conf."

# Sleeps while keeping the ssl certificates up to date
trap exit TERM

while true
do
    # The SSL certificates are renewed by certbot about 30 days before the expire date,
    # so it should be okay to reload nginx in 0h to 24h after the renew.
    sleep 24h & wait ${!}
    nginx -s reload
done
