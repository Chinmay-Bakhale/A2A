# Deployment Guide

This guide walks you through deploying the Leave Policy Assistant to Google Cloud Run.

## 📋 Prerequisites

Before deploying, ensure you have:

- ✅ Application tested locally and working
- ✅ Google Cloud account
- ✅ GCP Project created
- ✅ Billing enabled on your GCP project
- ✅ Google Cloud CLI installed

## Part 1: Push to GitHub

### Step 1: Create a Private GitHub Repository

1. Go to https://github.com/new
2. Repository name: `leave-policy-assistant` (or your choice)
3. **Important: Select "Private"**
4. Do NOT initialize with README (we already have one)
5. Click "Create repository"

### Step 2: Initialize Git and Push Code

```powershell
# Navigate to your project directory
cd C:\Users\17cb1\OneDrive\Desktop\Projects\A2A

# Initialize Git repository
git init

# Add all files
git add .

# Check what will be committed (should NOT include .env, .venv, etc.)
git status

# Create initial commit
git commit -m "Initial commit: Leave Policy Assistant Agent with Google ADK"

# Add your GitHub repository as remote (replace with your actual URL)
git remote add origin https://github.com/YOUR_USERNAME/leave-policy-assistant.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 3: Share Repository Access

1. Go to your repository on GitHub
2. Click **Settings** → **Collaborators**
3. Click **Add people**
4. Add: `hr.recruitment@servicehive.tech`
5. Select **Read** access
6. Send invitation

**Alternative (if email doesn't work):**
- Settings → Manage access → Invite teams or people
- Or share the repository URL with them directly

---

## Part 2: Deploy to Google Cloud Run

### Step 1: Install Google Cloud SDK (if not installed)

Download from: https://cloud.google.com/sdk/docs/install

Or use PowerShell:
```powershell
# Download installer
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")

# Run installer
& $env:Temp\GoogleCloudSDKInstaller.exe
```

After installation, restart your terminal.

### Step 2: Initialize GCP CLI

```powershell
# Login to Google Cloud
gcloud auth login

# Set your project (replace with your actual project ID)
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### Step 3: Create Secrets in Secret Manager

```powershell
# Create secret for Gemini API key
echo -n "YOUR_ACTUAL_GEMINI_API_KEY" | gcloud secrets create GOOGLE_API_KEY --data-file=-

# Create secret for LiteLLM model (optional)
echo -n "gemini/gemini-flash-latest" | gcloud secrets create LITELLM_MODEL --data-file=-

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding GOOGLE_API_KEY \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding LITELLM_MODEL \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

**To find your project number:**
```powershell
gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)"
```

### Step 4: Build and Deploy

**Option A: Deploy Directly (Recommended for first deployment)**

```powershell
# Build and deploy in one command
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
```

**Option B: Use Cloud Build (CI/CD Pipeline)**

```powershell
# Submit build using cloudbuild.yaml
gcloud builds submit --config cloudbuild.yaml

# Note: You'll need to update cloudbuild.yaml with your project ID first
```

### Step 5: Test Your Deployment

After deployment completes, you'll get a URL like:
```
https://leave-assistant-XXXXX-uc.a.run.app
```

Test it:
```powershell
# Test health endpoint
curl https://leave-assistant-XXXXX-uc.a.run.app/health

# Test chat endpoint
curl -X POST https://leave-assistant-XXXXX-uc.a.run.app/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How many PTO days do I have?",
    "session_id": "test-1",
    "employee_id": "EMP001"
  }'
```

---

## 🔧 Deployment Configuration Options

### Update Environment Variables

```powershell
gcloud run services update leave-assistant \
  --region us-central1 \
  --set-env-vars LOG_LEVEL=DEBUG
```

### Update Secrets

```powershell
# Update API key
echo -n "NEW_API_KEY" | gcloud secrets versions add GOOGLE_API_KEY --data-file=-

# Cloud Run will automatically use latest version
```

### Scale Configuration

```powershell
# Update scaling
gcloud run services update leave-assistant \
  --region us-central1 \
  --min-instances 1 \
  --max-instances 20
```

### View Logs

```powershell
# Stream logs
gcloud run services logs tail leave-assistant --region us-central1

# Or view in console
# https://console.cloud.google.com/run
```

---

## 🔒 Security Best Practices

### 1. Enable Authentication (Optional)

If you want to restrict access:

```powershell
# Deploy with authentication required
gcloud run deploy leave-assistant \
  --region us-central1 \
  --no-allow-unauthenticated

# Grant access to specific users
gcloud run services add-iam-policy-binding leave-assistant \
  --region us-central1 \
  --member="user:EMAIL@example.com" \
  --role="roles/run.invoker"
```

### 2. Use Custom Domain

```powershell
# Map custom domain
gcloud run domain-mappings create \
  --service leave-assistant \
  --domain api.yourcompany.com \
  --region us-central1
```

### 3. Set Up Monitoring

```powershell
# Enable Cloud Monitoring
gcloud services enable monitoring.googleapis.com

# View metrics in Cloud Console:
# https://console.cloud.google.com/monitoring
```

---

## 🐛 Troubleshooting Deployment

### Issue: Build Fails

```powershell
# Check build logs
gcloud builds list --limit 5
gcloud builds log BUILD_ID
```

### Issue: Service Won't Start

```powershell
# Check service logs
gcloud run services logs read leave-assistant --region us-central1 --limit 50
```

### Issue: Permission Denied

```powershell
# Check IAM permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID

# Add required roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="user:YOUR_EMAIL@gmail.com" \
  --role="roles/run.admin"
```

### Issue: Secret Not Found

```powershell
# List secrets
gcloud secrets list

# Check secret access
gcloud secrets describe GOOGLE_API_KEY
```

---

## 📊 Cost Estimation

**Cloud Run Pricing (Free Tier):**
- 2 million requests/month
- 360,000 GB-seconds/month
- 180,000 vCPU-seconds/month

**Your configuration:**
- 2 vCPU, 2GB RAM
- ~2-5 seconds per request
- Estimated cost: **$0 - $5/month** for light usage

**Monitor costs:**
```powershell
# View billing
gcloud billing accounts list
```

---

## 🔄 Update Deployment

After making code changes:

```powershell
# 1. Commit changes
git add .
git commit -m "Update: Description of changes"
git push

# 2. Redeploy
gcloud run deploy leave-assistant \
  --source . \
  --region us-central1
```

---

## ✅ Post-Deployment Checklist

- [ ] Service deployed successfully
- [ ] Health endpoint responds: `/health`
- [ ] Chat endpoint works: `/chat`
- [ ] Secrets configured correctly
- [ ] Logs are accessible
- [ ] Repository shared with evaluator
- [ ] API documentation accessible: `/docs`
- [ ] README updated with deployment URL

---

## 📝 Submission Checklist

- [ ] Private GitHub repository created
- [ ] Code pushed to `main` branch
- [ ] Repository access shared with: `hr.recruitment@servicehive.tech`
- [ ] README.md included with:
  - [ ] Architecture diagram
  - [ ] Setup instructions
  - [ ] Environment variables documented
  - [ ] Local run instructions
  - [ ] Testing instructions
- [ ] Application deployed to Cloud Run (optional but impressive)
- [ ] Deployment URL documented in README (if deployed)

---

## 🎯 Quick Deploy Commands Summary

```powershell
# 1. Push to GitHub
git init
git add .
git commit -m "Initial commit: Leave Policy Assistant"
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
git push -u origin main

# 2. Deploy to GCP
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com

# 3. Create secrets
echo -n "YOUR_API_KEY" | gcloud secrets create GOOGLE_API_KEY --data-file=-

# 4. Deploy
gcloud run deploy leave-assistant --source . --region us-central1 --allow-unauthenticated --set-secrets GOOGLE_API_KEY=GOOGLE_API_KEY:latest

# 5. Share repository access with hr.recruitment@servicehive.tech
```

---

## 📞 Support

For GCP-specific issues, check:
- Cloud Run Documentation: https://cloud.google.com/run/docs
- Cloud Build Documentation: https://cloud.google.com/build/docs
- Secret Manager: https://cloud.google.com/secret-manager/docs

For assignment questions, refer to the technical requirements document.
