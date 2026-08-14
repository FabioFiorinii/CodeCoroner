FROM docker.io/debian:bookworm-slim

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends slapd ldap-utils \
    && rm -rf /var/lib/apt/lists/*

COPY slapd.conf /etc/ldap/slapd.conf
COPY seed.ldif /seed.ldif
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 3890

ENTRYPOINT ["/entrypoint.sh"]