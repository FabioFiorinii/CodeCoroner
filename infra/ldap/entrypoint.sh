#!/bin/sh
set -e

mkdir -p /run/slapd

if [ ! -f /var/lib/ldap/.bootstrapped ]; then
    rm -rf /var/lib/ldap/*
    slapadd -f /etc/ldap/slapd.conf -l /seed.ldif 2>/dev/null
    touch /var/lib/ldap/.bootstrapped
fi

chown -R openldap:openldap /var/lib/ldap /run/slapd

exec slapd -d 1 -f /etc/ldap/slapd.conf -h 'ldap://0.0.0.0:3890/' -u openldap -g openldap