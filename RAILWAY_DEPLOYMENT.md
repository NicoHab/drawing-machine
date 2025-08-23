# 🚀 Drawing Machine Railway Deployment Guide

Deploy your Drawing Machine to Railway cloud while keeping local development intact.

## 🎯 What You Get

### 🏠 **Local Development** (Unchanged)
- Full system with GUI: `python complete_system_demo.py`
- All debugging and development features
- Motor TCP GUI window
- Multiple local servers

### ☁️ **Railway Production**
- Public URL: `https://your-app-name.railway.app`
- WebSocket: `wss://your-app-name.railway.app`
- Automatic scaling and monitoring
- Global accessibility

## 🚀 Quick Deploy to Railway

### 1. **Get API Keys** (Required)
```bash
# Get from: https://etherscan.io/apis
ETHERSCAN_API_KEY=your_key_here

# Get from: https://pro.coinbase.com/profile/api  
COINBASE_API_KEY=your_key_here
COINBASE_API_SECRET=your_secret_here
```

### 2. **Push to Git**
```bash
git add .
git commit -m "Ready for Railway deployment"
git push origin main
```

### 3. **Deploy to Railway**
1. Go to [railway.app](https://railway.app)
2. Click "Deploy from GitHub" 
3. Select your repository
4. Add environment variables in Railway dashboard
5. Deploy automatically starts!

### 4. **Connect Frontend**
Update your frontend `.env.local`:
```
VITE_BACKEND_URL=wss://your-app-name.railway.app
```

## 📁 Deployment Files Created

- ✅ `railway_production.py` - Production server entry point
- ✅ `railway.json` - Railway configuration  
- ✅ `Procfile` - Process definition
- ✅ `requirements.txt` - Python dependencies
- ✅ `.env.production.example` - Environment template

## 🔧 Local Development Unchanged

Everything you have locally continues to work:

```bash
# Full local system (unchanged)
python complete_system_demo.py

# Frontend development
cd frontend && npm run dev
```

**Local URLs remain the same**:
- Frontend: http://localhost:5180
- Backend: ws://localhost:8768

## 🌐 Production Benefits

✅ **24/7 Uptime** - Always available  
✅ **Auto-scaling** - Handles traffic spikes  
✅ **Global CDN** - Fast worldwide access  
✅ **WebSocket Support** - Real-time connections  
✅ **Automatic HTTPS** - Secure by default  
✅ **Zero Downtime Deploys** - Seamless updates  

## 🔍 Verify Deployment

### Check Status
```bash
# Install Railway CLI (optional)
npm install -g @railway/cli
railway login
railway logs
```

### Test WebSocket
```javascript
// Test in browser console
const ws = new WebSocket('wss://your-app-name.railway.app');
ws.onopen = () => console.log('✅ Railway connection success!');
```

## 🎨 Result

You now have:

1. **Complete Local Development** - Full featured localhost environment
2. **Production Cloud Backend** - Railway hosted with public URL
3. **Flexible Frontend** - Can connect to either local or cloud
4. **Easy Deployment** - Git push to update production

Your Drawing Machine is now ready for both development and production use! 🚀