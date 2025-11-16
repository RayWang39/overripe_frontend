# Deployment Guide for Separated Frontend/Backend

## Architecture Overview

```
┌─────────────────┐         ┌─────────────────┐
│  Public Repo    │   API   │  Private Repo   │
│   (Frontend)    │◄────────►│   (Backend)     │
│                 │  HTTPS   │                 │
│  Streamlit UI   │         │  - API Service  │
│  - app.py       │         │  - IYP Query    │
│  - Dashboard    │         │  - Data Files   │
└─────────────────┘         └─────────────────┘
```

## Step 1: Deploy Backend (Private)

### Option A: Deploy to Heroku

1. **Prepare the backend repository:**
```bash
cd private_backend
git init
git add .
git commit -m "Initial backend commit"
```

2. **Create Heroku app:**
```bash
heroku create your-backend-api
heroku config:set ENVIRONMENT=production
heroku config:set VALID_API_KEYS=your-secure-api-key-here
heroku config:set NEO4J_URI=bolt+s://your-neo4j-host.com:7687
heroku config:set NEO4J_USERNAME=your-username
heroku config:set NEO4J_PASSWORD=your-password-here
```

3. **Create Procfile:**
```bash
echo "web: cd api && python -m uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile
```

4. **Deploy:**
```bash
git push heroku main
```

### Option B: Deploy to Railway

1. **Connect GitHub repository**
2. **Set environment variables in Railway dashboard**
3. **Deploy automatically on push**

### Option C: Deploy to AWS/GCP

Use Docker container with the provided Dockerfile in `api/` directory.

## Step 2: Deploy Frontend (Public)

### Deploy to Streamlit Cloud

1. **Push frontend to public GitHub repo:**
```bash
cd public_frontend
git init
git remote add origin https://github.com/yourusername/public-frontend.git
git add .
git commit -m "Initial frontend commit"
git push -u origin main
```

2. **Connect to Streamlit Cloud:**
   - Go to https://streamlit.io/cloud
   - Click "New app"
   - Select your repository
   - Set main file path: `frontend/app.py`

3. **Configure Secrets in Streamlit Cloud:**
```toml
# In Streamlit Cloud secrets management
BACKEND_API_URL = "https://your-backend-api.herokuapp.com"
API_KEY = "your-secure-api-key-here"
```

## Step 3: Test the Connection

### 1. Test Backend API:
```bash
# Health check
curl https://your-backend-api.herokuapp.com/api/v1/health

# Test with API key
curl -H "X-API-Key: your-api-key" \
  https://your-backend-api.herokuapp.com/api/v1/baselines
```

### 2. Test Frontend:
- Visit your Streamlit app URL
- Check the "API Status" tab
- Verify health check passes

## Environment Variables Reference

### Backend (.env)
```bash
# Required
ENVIRONMENT=production
VALID_API_KEYS=key1,key2,key3
NEO4J_URI=bolt+s://your-neo4j-instance
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password

# Optional
PORT=8001
DISABLE_AUTH=false
ALLOWED_ORIGINS=https://your-frontend.streamlit.app
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### Frontend (.env or Streamlit Secrets)
```bash
# Required
BACKEND_API_URL=https://your-backend-api.herokuapp.com
API_KEY=your-api-key

# Optional
STREAMLIT_PORT=8501
```

## Security Checklist

- [ ] Generate strong, unique API keys
- [ ] Use HTTPS for all API communication
- [ ] Set CORS origins to only your frontend domain
- [ ] Enable rate limiting
- [ ] Store API keys in environment variables, never in code
- [ ] Rotate API keys periodically
- [ ] Monitor API access logs
- [ ] Use database credentials with minimal permissions
- [ ] Enable API request/response logging

## Local Development

### Run Backend:
```bash
cd private_backend/api
cp .env.example .env
# Edit .env with your settings
PYTHONPATH=.. python -m uvicorn main:app --reload --port 8001
```

### Run Frontend:
```bash
cd public_frontend
cp .env.example .env
# Edit .env to point to local backend
streamlit run frontend/app.py
```

## Troubleshooting

### Frontend can't connect to backend:
1. Check BACKEND_API_URL is correct
2. Verify API key is valid
3. Check CORS settings allow your frontend domain
4. Ensure backend is running and healthy

### Authentication errors:
1. Verify X-API-Key header is being sent
2. Check API key matches one in VALID_API_KEYS
3. Ensure DISABLE_AUTH is not true in production

### Data not loading:
1. Check CSV files are in correct location in backend
2. Verify file paths in data.py router
3. Check pandas is installed in requirements.txt

## Monitoring

### Backend Metrics to Track:
- API response times
- Error rates
- Request volume by endpoint
- Authentication failures
- Rate limit violations

### Frontend Metrics:
- Page load times
- User sessions
- Error rates
- API call patterns

## Scaling Considerations

### Backend:
- Use Redis for rate limiting instead of in-memory
- Cache Companies House data in database
- Use connection pooling for Neo4j
- Implement request queuing for heavy queries
- Add CDN for static data files

### Frontend:
- Enable Streamlit caching
- Optimize data transfer sizes
- Implement pagination for large results
- Use lazy loading for visualizations

## Cost Optimization

### Free Tier Options:
- **Backend**: Heroku free tier (sleeps after 30 min)
- **Frontend**: Streamlit Cloud free tier
- **Database**: Use existing Neo4j instance

### Production Recommendations:
- **Backend**: Railway ($5/month) or Heroku Hobby ($7/month)
- **Frontend**: Streamlit Cloud (free for public repos)
- **Database**: Neo4j Aura ($65/month for production)

## Support

For issues:
1. Check logs in your hosting platform
2. Verify all environment variables are set
3. Test API endpoints individually
4. Check network connectivity between services