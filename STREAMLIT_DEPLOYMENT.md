# Streamlit Frontend Deployment Guide

## Required Environment Variables

When deploying the Streamlit frontend (on Streamlit Cloud, Heroku, or other platforms), you need to set these environment variables:

### 1. Neo4j Database Connection
```
NEO4J_URI=neo4j+s://iyp.christyquinn.com:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=lewagon25omgbbq
```

### 2. API Connection (CRITICAL)
```
API_BASE_URL=<YOUR_DEPLOYED_API_URL>
```

**Important**: Replace `<YOUR_DEPLOYED_API_URL>` with your actual Railway API deployment URL.
- Example: `https://your-app.up.railway.app`
- Do NOT use `http://localhost:8001` in production

## Deployment on Streamlit Cloud

### Step 1: Fork/Push Repository
Ensure your repository contains:
- `frontend/app.py` - Main Streamlit application
- `frontend/requirements.txt` - Python dependencies
- `.streamlit/config.toml` - Streamlit configuration

### Step 2: Connect to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub repository
3. Select branch: `main`
4. Set main file path: `frontend/app.py`

### Step 3: Configure Secrets
In Streamlit Cloud dashboard, go to Settings → Secrets and add:

```toml
# Database Configuration
NEO4J_URI = "neo4j+s://iyp.christyquinn.com:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "lewagon25omgbbq"

# API Configuration - REPLACE WITH YOUR RAILWAY URL
API_BASE_URL = "https://your-railway-app.up.railway.app"
```

### Step 4: Deploy
Click "Deploy" and Streamlit will:
1. Install dependencies from `frontend/requirements.txt`
2. Load environment variables from Secrets
3. Start the application

## Features That Require the API

The following features require `API_BASE_URL` to be correctly configured:

### ✅ Method Chain Translator
- Converts method chains like `.find.with_organizations.upstream` to Cypher
- Requires connection to the Translation API service
- Will show "Connection error" if API is not accessible

### ✅ Works Without API
- Direct Cypher query execution
- Graph visualization
- Python interpreter for data analysis
- All Neo4j database queries

## Testing the Deployment

### 1. Test API Connection
In the Method Chain Translator section:
- Enter: `.find`
- ASN: `15169`
- Click "Translate Method Chain"
- Should return a valid Cypher query

### 2. Test Database Connection
In the main query box:
- Run: `MATCH (n) RETURN n LIMIT 1`
- Should return and visualize at least one node

## Common Issues and Solutions

### Issue: "Connection error" in Method Chain Translator
**Solution**: Check that `API_BASE_URL` is set correctly to your Railway deployment URL

### Issue: "Query failed" for all queries
**Solution**: Verify Neo4j credentials are correct

### Issue: Graph visualization not showing
**Solution**: Ensure `pyvis` is in requirements.txt and properly installed

## Local Development

For local development, the app uses these defaults if environment variables are not set:
- `NEO4J_URI`: neo4j+s://iyp.christyquinn.com:7687
- `API_BASE_URL`: http://localhost:8001

To run locally:
```bash
# Start the API service (in one terminal)
cd api && PYTHONPATH=.. python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Start Streamlit (in another terminal)
streamlit run frontend/app.py
```

## Environment Variable Priority

1. System environment variables (highest priority)
2. Streamlit Secrets (for Streamlit Cloud)
3. `.env` file (for local development)
4. Default values in code (fallback)

## Deployment Checklist

- [ ] API deployed on Railway and accessible
- [ ] Railway API URL obtained
- [ ] Environment variables configured in Streamlit Cloud:
  - [ ] NEO4J_URI
  - [ ] NEO4J_USERNAME  
  - [ ] NEO4J_PASSWORD
  - [ ] API_BASE_URL (with Railway URL)
- [ ] Repository contains:
  - [ ] frontend/app.py
  - [ ] frontend/requirements.txt
  - [ ] .streamlit/config.toml
- [ ] Test Method Chain Translator after deployment
- [ ] Test direct Cypher queries
- [ ] Test graph visualization