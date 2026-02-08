#!/bin/bash
# Quick deploy script for Cloud Run
# Usage: ./deploy.sh YOUR_PROJECT_ID

PROJECT_ID=$1

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: ./deploy.sh YOUR_PROJECT_ID"
    echo "Example: ./deploy.sh my-gcp-project"
    exit 1
fi

echo "🚀 Deploying Leave Policy Assistant to Cloud Run"
echo "Project: $PROJECT_ID"
echo ""

# Set project
gcloud config set project $PROJECT_ID

# Deploy
gcloud run deploy leave-assistant \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars LOG_LEVEL=INFO \
  --set-secrets GOOGLE_API_KEY=GOOGLE_API_KEY:latest,LITELLM_MODEL=LITELLM_MODEL:latest \
  --max-instances 10 \
  --min-instances 0 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300

echo ""
echo "✅ Deployment complete!"
echo "View your service: https://console.cloud.google.com/run"
