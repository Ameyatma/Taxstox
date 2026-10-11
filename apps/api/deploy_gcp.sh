#!/bin/bash
# TaxStox GCP Cloud Run Deployment Script

# Source the production environment variables
if [ -f .env.production ]; then
    source .env.production
else
    echo "❌ ERROR: .env.production file not found. Create it and add DATABASE_URL, TAXSTOX_JWT_SECRET, TAXSTOX_ENCRYPTION_KEY."
    exit 1
fi

PROJECT_ID=$(gcloud config get-value project)
REGION="asia-south1" # Mumbai region for lowest latency
REPO_NAME="taxstox-repo"
IMAGE_NAME="asia-south1-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/taxstox-api:latest"
FRONTEND_URL="https://taxstox.co"
ENVIRONMENT="production"

echo "🚀 Building Docker image and pushing to GCP Artifact Registry..."
gcloud builds submit --tag $IMAGE_NAME

echo "⚡ Deploying to Google Cloud Run..."
gcloud run deploy taxstox-api \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --max-instances 5 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --set-env-vars="PYTHON_VERSION=3.12,ENVIRONMENT=${ENVIRONMENT},FRONTEND_URL=${FRONTEND_URL},DATABASE_URL=${DATABASE_URL},TAXSTOX_JWT_SECRET=${TAXSTOX_JWT_SECRET},TAXSTOX_ENCRYPTION_KEY=${TAXSTOX_ENCRYPTION_KEY},GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID},GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}"

echo "✅ Backend Live on Google Cloud Run!"