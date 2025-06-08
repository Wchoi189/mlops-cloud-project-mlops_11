# 1. Show current directory structure
echo "=== Current Directory ==="
pwd
ls -la

echo "=== Docker Directory ==="
ls -la docker/

# 2. Check if monitoring.env exists and has content
echo "=== Monitoring.env Content ==="
if [ -f "docker/monitoring.env" ]; then
    echo "Found: docker/monitoring.env"
    head -5 docker/monitoring.env
else
    echo "NOT FOUND: docker/monitoring.env"
fi

if [ -f "monitoring.env" ]; then
    echo "Found: monitoring.env (in project root)"
    head -5 monitoring.env
else
    echo "NOT FOUND: monitoring.env (in project root)"
fi

# 3. Test Docker Compose config resolution
echo "=== Docker Compose Config Test ==="
docker compose -f docker/docker-compose.monitoring.yml config --services