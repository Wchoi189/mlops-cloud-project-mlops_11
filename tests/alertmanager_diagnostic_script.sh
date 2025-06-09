#!/bin/bash
echo "🔍 AlertManager Diagnostic Report"
echo "================================="

echo -e "\n📊 Container Status:"
docker ps | grep alertmanager || echo "❌ AlertManager container not running"

echo -e "\n📝 Recent Logs:"
docker logs mlops-alertmanager --tail 20 2>/dev/null || echo "❌ Cannot get logs"

echo -e "\n🔧 Configuration Check:"
if docker exec mlops-alertmanager test -f /etc/alertmanager/alertmanager.yml 2>/dev/null; then
    echo "✅ Config file exists"
    docker exec mlops-alertmanager /bin/alertmanager --config.file=/etc/alertmanager/alertmanager.yml --config.check 2>/dev/null && echo "✅ Config is valid" || echo "❌ Config is invalid"
else
    echo "❌ Config file not found"
fi

echo -e "\n🌐 Network Check:"
curl -s http://localhost:9093/-/healthy >/dev/null && echo "✅ AlertManager is responding" || echo "❌ AlertManager not responding"

echo -e "\n📁 File System Check:"
ls -la docker/monitoring/alertmanager/alertmanager.yml 2>/dev/null && echo "✅ Host config file exists" || echo "❌ Host config file missing"

echo -e "\n🔑 Environment Variables:"
docker exec mlops-alertmanager env | grep SLACK | head -2 2>/dev/null || echo "❌ No SLACK environment variables found"

echo -e "\n🐳 Docker Compose Status:"
docker compose -f docker/docker-compose.monitoring.yml ps alertmanager
