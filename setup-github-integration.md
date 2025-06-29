# 🔗 GitHub + Google Cloud Run Integration

## 🎯 **Automatic Deployment from GitHub**

This setup will automatically deploy your backend to Cloud Run whenever you push to your GitHub repository.

## 📋 **Prerequisites**

1. **GitHub repository** with your code
2. **Google Cloud project** created
3. **gcloud CLI** installed and authenticated

## 🚀 **Step 1: Enable APIs**

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable sourcerepo.googleapis.com
```

## 🔗 **Step 2: Connect GitHub Repository**

### Option A: Using Google Cloud Console (Easiest)

1. **Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)**
2. **Click "Connect Repository"**
3. **Select "GitHub (Cloud Build GitHub App)"**
4. **Authenticate with GitHub**
5. **Select your repository**
6. **Click "Connect"**

### Option B: Using gcloud CLI

```bash
# Install the GitHub app (if not done via console)
gcloud alpha builds connections create github \
    --region=us-central1 \
    --authorizer-token=YOUR_GITHUB_TOKEN \
    --app-installation-id=YOUR_INSTALLATION_ID
```

## ⚙️ **Step 3: Create Build Trigger**

### Using Google Cloud Console:

1. **Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)**
2. **Click "Create Trigger"**
3. **Configure:**
   - **Name**: `webscraper-backend-deploy`
   - **Event**: Push to a branch
   - **Source**: Your connected GitHub repo
   - **Branch**: `^main$` (or your default branch)
   - **Configuration**: Cloud Build configuration file
   - **Location**: Repository
   - **File**: `cloudbuild.yaml`

### Using gcloud CLI:

```bash
gcloud builds triggers create github \
    --repo-name=your-repo-name \
    --repo-owner=your-github-username \
    --branch-pattern="^main$" \
    --build-config=cloudbuild.yaml \
    --description="Deploy WebScraper backend to Cloud Run"
```

## 📁 **Step 4: Add Configuration Files**

The following files should already be in your repository:
- ✅ `cloudbuild.yaml` - Build and deployment configuration
- ✅ `Dockerfile.cloudrun` - Container configuration
- ✅ `backend/requirements-cloudrun.txt` - Python dependencies

## 🧪 **Step 5: Test the Integration**

1. **Make a small change** to your code
2. **Commit and push** to your main branch:
   ```bash
   git add .
   git commit -m "Test Cloud Build integration"
   git push origin main
   ```
3. **Check Cloud Build** - Go to [Cloud Build History](https://console.cloud.google.com/cloud-build/builds)
4. **Monitor the build** - Should take 5-10 minutes
5. **Check Cloud Run** - Your service should be updated automatically

## 🔍 **Step 6: Get Your Service URL**

After successful deployment:

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe webscraper-backend --region us-central1 --format 'value(status.url)')
echo "Your backend is deployed at: $SERVICE_URL"
```

## 🎯 **Step 7: Update Frontend**

Update your frontend environment variable:

```env
VITE_RENDER_BACKEND_URL=https://your-service-url.run.app
```

## 🔧 **Customizing the Build**

### **Environment Variables:**
Add to `cloudbuild.yaml`:
```yaml
- name: 'gcr.io/cloud-builders/gcloud'
  args:
  - 'run'
  - 'deploy'
  - 'webscraper-backend'
  - '--set-env-vars'
  - 'CUSTOM_VAR=value,ANOTHER_VAR=value'
```

### **Different Branches:**
Create separate triggers for staging/production:
```bash
# Staging trigger (develop branch)
gcloud builds triggers create github \
    --repo-name=your-repo-name \
    --repo-owner=your-github-username \
    --branch-pattern="^develop$" \
    --build-config=cloudbuild-staging.yaml

# Production trigger (main branch)
gcloud builds triggers create github \
    --repo-name=your-repo-name \
    --repo-owner=your-github-username \
    --branch-pattern="^main$" \
    --build-config=cloudbuild.yaml
```

## 📊 **Monitoring Your Deployments**

### **Build Status:**
- [Cloud Build History](https://console.cloud.google.com/cloud-build/builds)
- GitHub commit status checks
- Email notifications (configurable)

### **Service Health:**
- [Cloud Run Console](https://console.cloud.google.com/run)
- Automatic health checks
- Error reporting

## 🚨 **Troubleshooting**

### **Build Fails:**
1. Check [Cloud Build logs](https://console.cloud.google.com/cloud-build/builds)
2. Verify `cloudbuild.yaml` syntax
3. Check repository permissions

### **Deployment Fails:**
1. Check Cloud Run service logs
2. Verify container health
3. Check resource limits

### **GitHub Integration Issues:**
1. Re-authenticate GitHub connection
2. Check repository permissions
3. Verify webhook configuration

## ✅ **Benefits of This Setup**

- 🚀 **Automatic deployments** - Push to deploy
- 🔄 **Continuous integration** - Builds and tests automatically
- 📊 **Build history** - Track all deployments
- 🛡️ **Secure** - No manual credential management
- 📧 **Notifications** - Get notified of build status
- 🌍 **Scalable** - Handles multiple environments

## 🎯 **Next Steps**

1. **Set up the GitHub integration** using the steps above
2. **Test with a small change** to verify it works
3. **Configure notifications** for build status
4. **Set up staging environment** if needed
5. **Add automated tests** to your build pipeline

This setup gives you a professional CI/CD pipeline that automatically deploys your backend whenever you push changes to GitHub!