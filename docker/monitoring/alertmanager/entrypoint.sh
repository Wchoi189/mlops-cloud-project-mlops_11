#!/bin/sh
set -e

echo "🔧 환경 변수 치환과 함께 AlertManager를 시작합니다..."

cp /etc/alertmanager/alertmanager-template.yml /etc/alertmanager/alertmanager.yml

echo "🔧 /etc/alertmanager/alertmanager-template.yml..."


# Replace variables with debug output
echo "🔄 SLACK_CRITICAL_WEBHOOK_URL 치환 중..."
if [ -n "$SLACK_CRITICAL_WEBHOOK_URL" ]; then
    sed -i "s|\${SLACK_CRITICAL_WEBHOOK_URL}|${SLACK_CRITICAL_WEBHOOK_URL}|g" /etc/alertmanager/alertmanager.yml
    echo "✅ SLACK_CRITICAL_WEBHOOK_URL 치환 완료"
else
    echo "❌ SLACK_CRITICAL_WEBHOOK_URL이 비어있음"
fi

echo "🔄 SMTP_HOST 치환 중..."
if [ -n "$SMTP_HOST" ]; then
    sed -i "s|\${SMTP_HOST}|${SMTP_HOST}|g" /etc/alertmanager/alertmanager.yml
    echo "✅ SMTP_HOST 치환 완료"
fi

echo "🔄 SMTP_FROM 치환 중..."
if [ -n "$SMTP_FROM" ]; then
    sed -i "s|\${SMTP_FROM}|${SMTP_FROM}|g" /etc/alertmanager/alertmanager.yml
    echo "✅ SMTP_FROM 치환 완료"
fi

echo "🔄 WEBHOOK_URL 치환 중..."
if [ -n "$WEBHOOK_URL" ]; then
    sed -i "s|\${WEBHOOK_URL}|${WEBHOOK_URL}|g" /etc/alertmanager/alertmanager.yml
    echo "✅ WEBHOOK_URL 치환 완료"
fi

echo "🔄 SLACK_API_WEBHOOK_URL 치환 중..."
if [ -n "$SLACK_API_WEBHOOK_URL" ]; then
    sed -i "s|\${SLACK_API_WEBHOOK_URL}|${SLACK_API_WEBHOOK_URL}|g" /etc/alertmanager/alertmanager.yml
    echo "✅ SLACK_API_WEBHOOK_URL 치환 완료"
fi

echo "🔄 SLACK_ML_WEBHOOK_URL 치환 중..."
if [ -n "$SLACK_ML_WEBHOOK_URL" ]; then
    sed -i "s|\${SLACK_ML_WEBHOOK_URL}|${SLACK_ML_WEBHOOK_URL}|g" /etc/alertmanager/alertmanager.yml
    echo "✅ SLACK_ML_WEBHOOK_URL 치환 완료"
fi

echo "🔄 SLACK_DEVOPS_WEBHOOK_URL 치환 중..."
if [ -n "$SLACK_DEVOPS_WEBHOOK_URL" ]; then
    sed -i "s|\${SLACK_DEVOPS_WEBHOOK_URL}|${SLACK_DEVOPS_WEBHOOK_URL}|g" /etc/alertmanager/alertmanager.yml
    echo "✅ SLACK_DEVOPS_WEBHOOK_URL 치환 완료"
fi

echo "📋 완전한 생성된 AlertManager 설정:"

echo "📋 설정 파일 끝"

echo "🚀 AlertManager를 시작합니다..."

exec alertmanager \
    --config.file=/etc/alertmanager/alertmanager.yml \
    --storage.path=/alertmanager \
    --web.external-url=http://localhost:9093 \
    --log.level=debug
