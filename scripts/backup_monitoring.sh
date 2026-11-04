#!/bin/bash
# LR7: бэкап данных Prometheus + Grafana
B=/home/student/backups
D=$(date +%F_%H%M)
mkdir -p $B
PROM_VOL=$(docker volume ls -q | grep prometheus)
GRAF_VOL=$(docker volume ls -q | grep grafana)
docker run --rm -v $PROM_VOL:/data:ro -v $B:/backup alpine tar czf /backup/prometheus_$D.tar.gz -C /data .
docker run --rm -v $GRAF_VOL:/data:ro -v $B:/backup alpine tar czf /backup/grafana_$D.tar.gz -C /data .
find $B -name '*.tar.gz' -mtime +7 -delete
echo "Бэкап OK: $D"
