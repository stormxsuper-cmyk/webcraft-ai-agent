# WebCraft AI Deployment Guide

## 1. Push to GitHub
- Create a new repository on GitHub named `webcraft-ai-agent`.
- Upload all files inside this directory to your repository.

## 2. Deploy on Railway
1. Go to https://railway.app and click **New Project**.
2. Choose **Deploy from GitHub repo** and select `webcraft-ai-agent`.
3. Go to project **Variables** in Railway and add:
   `GEMINI_API_KEY` = `your_gemini_api_key_here`
4. Click **Deploy**. Railway will automatically detect Python and start your application!
