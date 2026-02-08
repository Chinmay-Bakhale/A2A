# Quick Deploy Script for Windows PowerShell
# Usage: .\deploy.ps1 YOUR_PROJECT_ID

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId
)

Write-Host "🚀 Deploying Leave Policy Assistant to Cloud Run" -ForegroundColor Green
Write-Host "Project: $ProjectId"
Write-Host ""

# Set project
gcloud config set project $ProjectId

# Deploy
gcloud run deploy leave-assistant `
  --source . `
  --region us-central1 `
  --platform managed `
  --allow-unauthenticated `
  --set-env-vars LOG_LEVEL=INFO `
  --set-secrets GOOGLE_API_KEY=GOOGLE_API_KEY:latest,LITELLM_MODEL=LITELLM_MODEL:latest `
  --max-instances 10 `
  --min-instances 0 `
  --memory 2Gi `
  --cpu 2 `
  --timeout 300

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "View your service: https://console.cloud.google.com/run"
