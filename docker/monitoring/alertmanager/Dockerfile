FROM prom/alertmanager:v0.25.0

# Copy the configuration template and entrypoint script
COPY --chmod=755 ./monitoring/alertmanager/alertmanager-template.yml /etc/alertmanager/alertmanager-template.yml
COPY --chmod=755 ./monitoring/alertmanager/entrypoint.sh /entrypoint.sh

# Make entrypoint executable
# RUN chmod +x /entrypoint.sh # works for linux but not for windows


# Use custom entrypoint
ENTRYPOINT ["/entrypoint.sh"]