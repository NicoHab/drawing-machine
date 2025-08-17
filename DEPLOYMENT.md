# Drawing Machine Deployment Guide

This guide covers deploying the Drawing Machine manual control system.

## 🌐 Frontend Deployment Options

### Option 1: Netlify (Recommended - Free)

1. **Build the frontend:**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. **Deploy to Netlify:**
   - Go to [netlify.com](https://netlify.com)
   - Create account/login
   - Click "Add new site" → "Deploy manually" 
   - Drag & drop the `frontend/dist/` folder
   - Site will be available at `https://[random-name].netlify.app`

### Option 2: Vercel (Free)

1. **Build the frontend:**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. **Deploy to Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Create account/login
   - Click "Add New" → "Project"
   - Connect GitHub repo or upload `frontend/dist/` folder

### Option 3: GitHub Pages (Free)

1. **Enable GitHub Pages:**
   - Go to repository Settings → Pages
   - Source: GitHub Actions
   - Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to GitHub Pages
on:
  push:
    branches: [ main ]
    paths: [ 'frontend/**' ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: cd frontend && npm install
      - name: Build
        run: cd frontend && npm run build
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: frontend/dist
```

## 🖥️ Backend Deployment Options

### Option 1: Railway (Recommended for WebSocket)

1. **Create `Procfile` in root:**
   ```
   web: poetry run python edge/manual_control/manual_control_server.py
   ```

2. **Deploy:**
   - Go to [railway.app](https://railway.app)
   - Connect GitHub repo
   - Deploy automatically

### Option 2: Heroku

1. **Create `Procfile` in root:**
   ```
   web: poetry run python edge/manual_control/manual_control_server.py
   ```

2. **Deploy:**
   - Install Heroku CLI
   - `heroku create drawing-machine-api`
   - `git push heroku main`

## 🔧 Environment Configuration

### Frontend Environment Variables

Create `frontend/.env.production`:
```
VITE_WEBSOCKET_URL=wss://your-backend-domain.com
```

### Backend Environment Variables

Set these in your deployment platform:
```
PORT=8080
HOST=0.0.0.0
WEBSOCKET_PORT=8766
```

## 🚀 Quick Deploy Commands

### Build and prepare for deployment:
```bash
# Build frontend
cd frontend
npm run build

# The dist/ folder is ready for deployment
```

### Test production build locally:
```bash
cd frontend
npm run preview
```

## 📡 CORS and WebSocket Configuration

When deploying, update the WebSocket URL in the frontend:

**In `frontend/src/views/ManualControlView.vue`:**
```typescript
// For production deployment
const wsUrl = ref('wss://your-backend-domain.com')

// For local development  
const wsUrl = ref('ws://localhost:8766')
```

## 🔐 Security Considerations

- Enable HTTPS for production
- Configure CORS properly for your domain
- Use environment variables for sensitive configuration
- Consider rate limiting for WebSocket connections

## 📊 Monitoring

- **Frontend**: Use built-in analytics from Netlify/Vercel
- **Backend**: Add logging and monitoring service
- **WebSocket**: Monitor connection health and message rates