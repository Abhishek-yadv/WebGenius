# 🚀 Google Cloud Run Deployment Guide

## 🎯 **Why Google Cloud Run?**

- ⭐ **Serverless containers** - No server management
- 💰 **Pay-per-use** - Only pay when requests are being processed
- 🆓 **Generous free tier** - 2 million requests/month
- 🐍 **Excellent Python support** - Native container support
- 🚀 **Auto-scaling** - Scales to zero when not in use
- 🌍 **Global deployment** - Multiple regions available

## 📋 **Prerequisites**

1. **Google Cloud Account** - [Sign up here](https://cloud.google.com/)
2. **Google Cloud CLI** - [Install gcloud](https://cloud.google.com/sdk/docs/install)
3. **Docker** - [Install Docker](https://docs.docker.com/get-docker/)
4. **Project setup** - Create a new Google Cloud project

## 🚀 **Quick Deployment**

### Option 1: Automated Script (Recommended)

```bash
# Make the script executable
chmod +x deploy-cloudrun.sh

# Deploy (replace with your project ID)
./deploy-cloudrun.sh your-project-id
```

### Option 2: Manual Deployment

```bash
# 1. Set your project ID
export PROJECT_ID="your-project-id"

# 2. Authenticate with Google Cloud
gcloud auth login
gcloud config set project $PROJECT_ID

# 3. Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# 4. Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/webscraper-backend
gcloud run deploy webscraper-backend \
    --image gcr.io/$PROJECT_ID/webscraper-backend \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300
```

## 🔧 **Configuration Details**

### **Resource Allocation:**
- **Memory**: 2GB (sufficient for Playwright + Chrome)
- **CPU**: 2 vCPUs (handles concurrent scraping)
- **Timeout**: 300 seconds (5 minutes for complex scraping)
- **Concurrency**: 10 requests per instance
- **Max Instances**: 10 (adjust based on needs)

### **Environment Variables:**
- `PORT`: 8080 (Cloud Run standard)
- `PYTHONPATH`: /app
- Auto-configured by Cloud Run

### **Security Features:**
- Non-root user execution
- Minimal container image
- Health checks enabled
- HTTPS by default

## 💰 **Cost Estimation**

### **Free Tier (Monthly):**
- 2 million requests
- 400,000 GB-seconds
- 200,000 vCPU-seconds

### **Typical Usage:**
- **Light usage** (1000 scrapes/month): **FREE**
- **Medium usage** (10,000 scrapes/month): **~$5-10**
- **Heavy usage** (100,000 scrapes/month): **~$50-100**

## 🧪 **Testing Your Deployment**

After deployment, test these endpoints:

```bash
# Get your service URL
SERVICE_URL=$(gcloud run services describe webscraper-backend --region us-central1 --format 'value(status.url)')

# Test health endpoint
curl $SERVICE_URL/api/health

# Test scraping
curl -X POST $SERVICE_URL/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://docs.python.org/3/"}'
```

## 🔄 **Update Your Frontend**

After successful deployment:

1. **Get your Cloud Run URL**:
   ```bash
   gcloud run services describe webscraper-backend --region us-central1 --format 'value(status.url)'
   ```

2. **Update frontend environment variable**:
   ```env
   VITE_RENDER_BACKEND_URL=https://your-service-url.run.app
   ```

3. **Redeploy your frontend**

## 📊 **Monitoring & Logs**

### **View Logs:**
```bash
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=webscraper-backend" --limit 50
```

### **Monitor Performance:**
- Go to [Cloud Run Console](https://console.cloud.google.com/run)
- Click on your service
- View metrics, logs, and performance data

## 🔧 **Advanced Configuration**

### **Custom Domain:**
```bash
gcloud run domain-mappings create --service webscraper-backend --domain your-domain.com --region us-central1
```

### **Environment Variables:**
```bash
gcloud run services update webscraper-backend \
    --set-env-vars "CUSTOM_VAR=value" \
    --region us-central1
```

### **Scaling Configuration:**
```bash
gcloud run services update webscraper-backend \
    --max-instances 20 \
    --min-instances 1 \
    --region us-central1
```

## 🚨 **Troubleshooting**

### **Common Issues:**

1. **Build Failures:**
   - Check Docker is running
   - Verify project permissions
   - Check Cloud Build API is enabled

2. **Memory Issues:**
   - Increase memory allocation
   - Optimize Playwright usage
   - Consider using --no-sandbox flag

3. **Timeout Issues:**
   - Increase timeout setting
   - Optimize scraping logic
   - Use concurrent processing

### **Debug Commands:**
```bash
# Check service status
gcloud run services describe webscraper-backend --region us-central1

# View recent logs
gcloud logs tail "resource.type=cloud_run_revision" --follow

# Test locally
docker run -p 8080:8080 gcr.io/$PROJECT_ID/webscraper-backend
```

## ✅ **Benefits of Cloud Run**

- 🚀 **Fast cold starts** - Typically under 2 seconds
- 💰 **Cost effective** - Pay only for actual usage
- 🔄 **Auto-scaling** - Handles traffic spikes automatically
- 🛡️ **Secure** - HTTPS by default, IAM integration
- 🌍 **Global** - Deploy to multiple regions easily
- 📊 **Observable** - Built-in monitoring and logging

## 🎯 **Next Steps**

1. **Deploy your backend** using the provided scripts
2. **Test all endpoints** to ensure functionality
3. **Update your frontend** with the new backend URL
4. **Set up monitoring** and alerts
5. **Consider custom domain** for production use

Google Cloud Run provides an excellent serverless platform for your WebScraper backend with automatic scaling, built-in security, and cost-effective pricing!