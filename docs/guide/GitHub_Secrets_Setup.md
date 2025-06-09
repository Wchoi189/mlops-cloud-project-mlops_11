# GitHub Secrets Setup Guide

## Required Secrets for CI/CD Pipeline

Navigate to your GitHub repository → Settings → Secrets and variables → Actions

### 1. Notification Secrets (Optional but Recommended)

```bash
# Slack Webhook for notifications
SLACK_ML_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Email notifications
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password  # Use app password, not regular password
NOTIFICATION_EMAIL=team@your-company.com
```

### 2. Setup Instructions

#### Slack Webhook URL

1. Go to your Slack workspace
2. Apps → Incoming Webhooks → Add to Slack
3. Choose channel and copy webhook URL
4. Add as `SLACK_ML_WEBHOOK_URL` secret

#### Email Notifications

1. Use Gmail with App Password (recommended)
2. Enable 2FA on Gmail account
3. Generate App Password in Gmail settings
4. Use app password (not regular password)

### 3. Auto-Provided Secrets

These are automatically available:

- `GITHUB_TOKEN` - Automatically provided by GitHub Actions

### 4. Verification

Test your secrets by triggering a pipeline:

```bash
git add .
git commit -m "test: Trigger CI/CD pipeline"
git push origin main
```

Check GitHub Actions tab for pipeline execution.
