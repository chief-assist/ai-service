# Deployment Guide for ChefAssist AI Service

## Free Hosting Options (Accessible from China)

Since you're in China and need to access DeepSeek API (not Google services), here are the best free hosting options:

### 1. **Railway.app** ⭐ Recommended
- **Free Tier**: $5 credit/month (enough for small apps)
- **Accessibility**: Good from China
- **Features**: 
  - Docker support
  - Environment variables
  - Auto-deploy from GitHub
  - HTTPS included
- **Setup**: Very easy, connects to GitHub
- **URL**: https://railway.app

**Deployment Steps:**
```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login
railway login

# 3. Initialize project
railway init

# 4. Deploy
railway up
```

### 2. **Render.com**
- **Free Tier**: 750 hours/month (enough for 24/7)
- **Accessibility**: Generally accessible from China
- **Features**:
  - Docker support
  - Environment variables
  - Auto-deploy from GitHub
  - HTTPS included
- **Limitation**: Free tier spins down after 15 min inactivity
- **URL**: https://render.com

**Deployment Steps:**
1. Connect GitHub repo
2. Select "Web Service"
3. Use Dockerfile
4. Add environment variables
5. Deploy

### 3. **Fly.io**
- **Free Tier**: 3 shared VMs, 160GB outbound data
- **Accessibility**: Good global coverage
- **Features**:
  - Docker support
  - Edge deployment
  - Environment variables
- **URL**: https://fly.io

**Deployment Steps:**
```bash
# 1. Install Fly CLI
curl -L https://fly.io/install.sh | sh

# 2. Login
fly auth login

# 3. Launch
fly launch
```

### 4. **Hugging Face Spaces** (Great for AI services)
- **Free Tier**: Unlimited
- **Accessibility**: Good from China
- **Features**:
  - Python runtime
  - Environment variables
  - Auto-deploy from GitHub
  - HTTPS included
- **URL**: https://huggingface.co/spaces

**Deployment Steps:**
1. Create a new Space
2. Select "Docker" SDK
3. Push your code
4. Add environment variables in Settings

### 5. **Chinese Cloud Providers** (Best for China)

#### Aliyun (Alibaba Cloud)
- **Free Tier**: 1 month trial, then pay-as-you-go
- **Accessibility**: Excellent in China
- **Features**: Full Docker support
- **URL**: https://www.aliyun.com

#### Tencent Cloud
- **Free Tier**: 1 month trial
- **Accessibility**: Excellent in China
- **Features**: Full Docker support
- **URL**: https://cloud.tencent.com

### 6. **Vercel** (For Serverless)
- **Free Tier**: Generous
- **Accessibility**: Good
- **Note**: Better for serverless, may need adjustments for FastAPI
- **URL**: https://vercel.com

## Recommended Setup for China

**Best Option**: **Railway.app** or **Render.com**
- Easy setup
- Good accessibility from China
- Free tier sufficient for development
- Docker support
- Environment variables

## Pre-Deployment Checklist

### 1. Update Environment Variables

Make sure your `.env` has:
```env
# DeepSeek API (works in China)
DEEPSEEK_API_KEY=your_deepseek_api_key

# Service API Key
API_KEY=your_service_api_key

# CORS - Update with your deployment URL
ALLOWED_ORIGINS=https://your-app.railway.app,https://your-app.onrender.com
```

### 2. Update Dockerfile (if needed)

Your current Dockerfile looks good. Make sure it exposes port 8000.

### 3. Test Locally First

```bash
# Test with DeepSeek
python main.py

# Or
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Update CORS Settings

After deployment, update `ALLOWED_ORIGINS` in your `.env` to include:
- Your frontend URL
- Your Express API URL
- Your deployment URL

## Deployment Steps (Railway.app Example)

1. **Create Railway Account**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure Environment Variables**
   - Go to Variables tab
   - Add:
     - `DEEPSEEK_API_KEY`
     - `API_KEY`
     - `ALLOWED_ORIGINS`
     - `PORT=8000`

4. **Deploy**
   - Railway auto-detects Dockerfile
   - Deploys automatically
   - Get your URL: `https://your-app.railway.app`

5. **Test**
   ```bash
   curl https://your-app.railway.app/api/ai/health
   ```

## Quick Comparison

| Platform | Free Tier | China Access | Docker | Ease |
|----------|-----------|--------------|--------|------|
| Railway | $5/month | ⭐⭐⭐⭐ | ✅ | ⭐⭐⭐⭐⭐ |
| Render | 750hrs/mo | ⭐⭐⭐⭐ | ✅ | ⭐⭐⭐⭐⭐ |
| Fly.io | 3 VMs | ⭐⭐⭐ | ✅ | ⭐⭐⭐⭐ |
| Hugging Face | Unlimited | ⭐⭐⭐⭐ | ✅ | ⭐⭐⭐⭐ |
| Aliyun | 1mo trial | ⭐⭐⭐⭐⭐ | ✅ | ⭐⭐⭐ |
| Tencent | 1mo trial | ⭐⭐⭐⭐⭐ | ✅ | ⭐⭐⭐ |

## Troubleshooting

### Connection Issues from China
- Use Chinese cloud providers (Aliyun/Tencent) for best performance
- Railway and Render usually work but may be slower

### Environment Variables Not Working
- Make sure variables are set in hosting platform
- Restart service after adding variables

### Port Issues
- Most platforms auto-detect port from Dockerfile
- Some require `PORT` environment variable

### DeepSeek API Access
- DeepSeek should work fine from China
- Test API key locally first
- Check DeepSeek status page if issues

## Next Steps

1. **Choose a platform** (recommend Railway or Render)
2. **Test locally** with DeepSeek API
3. **Deploy** using platform's Docker support
4. **Update CORS** with your deployment URL
5. **Test endpoints** from your Express API

## Support

If you need help with deployment:
- Check platform documentation
- Test locally first
- Check logs in hosting platform dashboard
- Verify environment variables are set correctly
