# STEP-BY-STEP: Push to GitHub and Deploy

## PART 1: PUSH TO GITHUB (15 minutes)

### Step 1: Create GitHub Repository

1. Go to: https://github.com/new
2. Repository name: leave-policy-assistant
3. **IMPORTANT: Check "Private"**
4. Do NOT add README, .gitignore, or license (we already have them)
5. Click "Create repository"
6. Copy the repository URL (e.g., https://github.com/yourusername/leave-policy-assistant.git)

### Step 2: Initialize Git and Push

Open PowerShell in your project folder and run:

```powershell
# Check you're in the right folder
pwd
# Should show: C:\Users\17cb1\OneDrive\Desktop\Projects\A2A

# Initialize git
git init

# Add all files
git add .

# Check what will be committed (should NOT see .env or .venv)
git status

# If you see .env or .venv in the list, STOP and check .gitignore

# Create first commit
git commit -m "Initial commit: Leave Policy Assistant with Google ADK"

# Add your GitHub repository (REPLACE with YOUR actual URL)
git remote add origin https://github.com/YOUR_USERNAME/leave-policy-assistant.git

# Rename branch to main
git branch -M main

# Push to GitHub
git push -u origin main
```

### Step 3: Share with Evaluator

Go to your GitHub repository page:
1. Click "Settings" (top right)
2. Click "Collaborators and teams" (left sidebar)
3. Click "Add people"
4. Enter: hr.recruitment@servicehive.tech
5. Click "Add hr.recruitment@servicehive.tech to this repository"

✅ **PART 1 COMPLETE!** Your code is now on GitHub.

---

## PART 2: DEPLOY TO GOOGLE CLOUD RUN (Optional - 30 minutes)

This part is OPTIONAL but will impress the evaluators!

### Before You Start

You need:
- Google Cloud account (free tier available)
- GCP project created
- Billing enabled (won't be charged if you stay in free tier)

### Step 1: Install Google Cloud SDK

Download from: https://cloud.google.com/sdk/docs/install

After installation, restart your terminal.

### Step 2: Setup GCP

```powershell
# Login to Google Cloud
gcloud auth login
# This will open a browser - login with your Google account

# List your projects (or create one at https://console.cloud.google.com)
gcloud projects list

# Set your project (REPLACE YOUR_PROJECT_ID)
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs (takes 2-3 minutes)
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### Step 3: Create Secrets

**Get your Gemini API key** from your .env file, then:

```powershell
# Create secret for API key (REPLACE with your actual key)
echo YOUR_GEMINI_API_KEY | gcloud secrets create GOOGLE_API_KEY --data-file=-

# Create secret for model
echo gemini/gemini-flash-latest | gcloud secrets create LITELLM_MODEL --data-file=-

# Get your project number (you'll need it next)
gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)"
# It will show a number like: 123456789

# Grant access to secrets (REPLACE PROJECT_NUMBER with the number from above)
gcloud secrets add-iam-policy-binding GOOGLE_API_KEY --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding LITELLM_MODEL --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
```

### Step 4: Deploy!

**Option A: Use the deploy script (easiest)**

```powershell
# REPLACE YOUR_PROJECT_ID
.\deploy.ps1 YOUR_PROJECT_ID
```

**Option B: Manual deploy command**

```powershell
gcloud run deploy leave-assistant --source . --region us-central1 --platform managed --allow-unauthenticated --set-env-vars LOG_LEVEL=INFO --set-secrets GOOGLE_API_KEY=GOOGLE_API_KEY:latest,LITELLM_MODEL=LITELLM_MODEL:latest --max-instances 10 --memory 2Gi --cpu 2 --timeout 300
```

This will take 5-10 minutes. When done, you'll get a URL like:
```
https://leave-assistant-xxxxx-uc.a.run.app
```

### Step 5: Test Your Deployment

```powershell
# Test health (REPLACE with YOUR actual URL)
curl https://leave-assistant-xxxxx-uc.a.run.app/health

# Test chat
curl -X POST https://leave-assistant-xxxxx-uc.a.run.app/chat -H "Content-Type: application/json" -d '{\"message\":\"How many PTO days?\",\"session_id\":\"test\",\"employee_id\":\"EMP001\"}'
```

### Step 6: Update Your README

Add the deployment URL to your README.md:

```markdown
## 🚀 Live Deployment

The application is deployed at: https://leave-assistant-xxxxx-uc.a.run.app

- API Documentation: https://leave-assistant-xxxxx-uc.a.run.app/docs
- Health Check: https://leave-assistant-xxxxx-uc.a.run.app/health
```

Then commit and push:

```powershell
git add README.md
git commit -m "Add deployment URL"
git push
```

✅ **PART 2 COMPLETE!** Your app is live on Google Cloud!

---

## 🎯 SUBMISSION CHECKLIST

Before submitting, verify:

- [ ] Code pushed to private GitHub repository
- [ ] Repository access shared with hr.recruitment@servicehive.tech
- [ ] README.md is complete with:
  - [ ] Architecture diagram
  - [ ] Setup instructions
  - [ ] Environment variables documented
  - [ ] How to run locally
  - [ ] How to run tests
  - [ ] (Optional) Deployment URL
- [ ] All tests passing locally
- [ ] No .env file in repository (check on GitHub)
- [ ] No API keys visible in code

---

## 🆘 TROUBLESHOOTING

### Git Issues

**"fatal: not a git repository"**
```powershell
git init
```

**"remote origin already exists"**
```powershell
git remote remove origin
git remote add origin YOUR_URL
```

**"failed to push"**
```powershell
git pull origin main --rebase
git push -u origin main
```

### GCP Issues

**"gcloud: command not found"**
- Restart terminal after installing Cloud SDK
- Make sure Cloud SDK is in your PATH

**"Permission denied"**
- Make sure billing is enabled on your GCP project
- Check you have necessary permissions (Owner or Editor role)

**"Secret not found"**
```powershell
# List secrets
gcloud secrets list

# Recreate if needed
echo YOUR_API_KEY | gcloud secrets create GOOGLE_API_KEY --data-file=-
```

**Deployment fails**
```powershell
# Check logs
gcloud run services logs read leave-assistant --limit 50
```

---

## 📧 SUBMISSION

Send email to: hr.recruitment@servicehive.tech

Subject: Leave Policy Assistant - GitHub Repository Access

Body:
```
Hello,

I have completed the Leave Policy Assistant assignment.

Repository: https://github.com/YOUR_USERNAME/leave-policy-assistant
Access: Granted to hr.recruitment@servicehive.tech

[Optional if deployed]
Live Deployment: https://leave-assistant-xxxxx-uc.a.run.app
API Documentation: https://leave-assistant-xxxxx-uc.a.run.app/docs

The repository includes:
- Complete implementation with Google ADK
- Custom tools (check_leave_balance, calculate_eligibility)
- Security callbacks (PII detection, content filtering)
- Circuit breaker pattern for Snowflake integration
- FastAPI wrapper with /chat endpoint
- Comprehensive tests (>80% coverage)
- Docker deployment configuration
- Complete documentation

Thank you for your consideration.

Best regards,
[Your Name]
```

---

Good luck! 🚀
