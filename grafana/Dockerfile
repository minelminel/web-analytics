FROM grafana/grafana

WORKDIR /etc/grafana/
COPY ./conf/grafana.ini .
COPY ./conf/dashboards.yaml ./provisioning/dashboards/
COPY ./conf/postgres.yaml ./provisioning/datasources/
