FROM prom/alertmanager:v0.25.0

# Copy the configuration template and entrypoint script
COPY --chmod=755 docker/monitoring/alertmanager/alertmanager-template.yml /etc/alertmanager/alertmanager-template.yml
COPY --chmod=755 docker/monitoring/alertmanager/entrypoint.sh /entrypoint.sh

# Use custom entrypoint
ENTRYPOINT ["/entrypoint.sh"]
