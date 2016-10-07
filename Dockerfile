FROM mlaccetti/haproxy-lua:1.6.4-alpine

COPY haproxy.cfg /etc/haproxy/haproxy.cfg
