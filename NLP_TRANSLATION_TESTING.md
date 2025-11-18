# 🤖 NLP Translation Feature - Testing Guide

## Overview
This feature adds natural language to Cypher translation using DeepSeek LLM API.

---

## ✅ Prerequisites

1. **API Key Configured:**
   - ✅ Already added to `api/.env`: `DEEPSEEK_API_KEY=sk-ajby...`

2. **Dependencies Installed:**
   ```bash
   pip install -r requirements.txt
   pip install -r api/requirements.txt
   ```

---

## 🚀 Local Testing Instructions

### **Step 1: Start the API Service**

Open Terminal 1:
```bash
cd api
PYTHONPATH=.. python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### **Step 2: Test API Endpoints (Optional)**

Open Terminal 2:
```bash
# Quick API test
./test_nlp_api.sh

# Or test manually:
curl -X POST http://localhost:8001/api/v1/nlp/translate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find all upstream providers of Google",
    "context": {"asn": 15169}
  }'
```

**Expected response:**
```json
{
  "success": true,
  "cypher": "MATCH (as:AS {asn: 15169})-[:DEPENDS_ON]->(upstream:AS)\nRETURN as.asn AS source_asn, upstream.asn AS upstream_asn, upstream.name AS upstream_name\nLIMIT 100",
  "explanation": "Translated natural language query to Cypher",
  "parameters": {}
}
```

### **Step 3: Start Streamlit Frontend**

Open Terminal 3:
```bash
streamlit run frontend/app.py
```

**Browser will open:** http://localhost:8501

### **Step 4: Test Natural Language Translation in UI**

1. **Login** with your credentials
2. Scroll down to the **"🤖 Natural Language Translator (NEW)"** section
3. Try these example queries:

#### **Test Case 1: Simple Query**
- **Input:** "Find all upstream providers of Google"
- **Expected:** Generates Cypher query with AS15169
- **Action:** Click "📋 Use This Query" to copy to query box below

#### **Test Case 2: With ASN Context**
- **Input:** "Show me the upstream providers"
- **Check:** "Include ASN" checkbox
- **ASN:** 15169
- **Expected:** Generates contextual Cypher query

#### **Test Case 3: Geographic Query**
- **Input:** "Show organizations in the United States"
- **Expected:** Generates query with Country filter

#### **Test Case 4: Relationship Query**
- **Input:** "List all IXP members"
- **Expected:** Generates query with MEMBER_OF relationship

### **Step 5: Execute Generated Query**

After translation:
1. Click **"📋 Use This Query"** button
2. Scroll to **"Enter Cypher Query:"** section
3. Click **"Run Query"**
4. View results as **graph visualization** and **data table**

---

## 🧪 Test Scenarios

### **Scenario 1: End-to-End Translation & Execution**
1. Enter: "Find upstream providers of Cloudflare"
2. Click "🤖 Translate with AI"
3. Wait for translation (3-5 seconds)
4. Review generated Cypher
5. Click "📋 Use This Query"
6. Click "Run Query"
7. Verify graph shows Cloudflare's upstreams

### **Scenario 2: Error Handling - API Down**
1. Stop API service (Ctrl+C in Terminal 1)
2. Try translation in UI
3. Expected: "Cannot connect to API" error message

### **Scenario 3: Error Handling - Bad Query**
1. Enter: "asdfasdfasdf random text"
2. Click translate
3. Expected: LLM attempts translation (may produce invalid query)
4. Note: No validation yet in MVP

### **Scenario 4: Context-Aware Translation**
1. Check "Include ASN" box
2. Enter ASN: 13335 (Cloudflare)
3. Enter: "show upstream providers"
4. Expected: Query specifically for AS13335

---

## 📊 What to Look For

### **✅ Success Indicators:**
- API starts without errors
- Health check returns `"llm_configured": true`
- Frontend shows NLP section
- Translation completes in <10 seconds
- Generated Cypher is syntactically valid
- Query executes successfully in Neo4j
- Results display in graph/table

### **⚠️ Common Issues:**

#### **Issue 1: "LLM service not configured"**
- **Cause:** DEEPSEEK_API_KEY not set
- **Fix:** Check `api/.env` file has the key

#### **Issue 2: "Request timeout"**
- **Cause:** LLM API slow or unreachable
- **Fix:** Check internet connection, try again

#### **Issue 3: "Cannot connect to API"**
- **Cause:** API service not running
- **Fix:** Start API service in Terminal 1

#### **Issue 4: Invalid Cypher Generated**
- **Cause:** LLM misunderstood query
- **Fix:** Rephrase query, be more specific

---

## 🔍 Debugging

### **Check API Logs:**
Look at Terminal 1 (API service) for:
```
INFO:     127.0.0.1:xxxxx - "POST /api/v1/nlp/translate HTTP/1.1" 200 OK
```

### **Check API Health:**
```bash
curl http://localhost:8001/api/v1/nlp/health
```

Expected:
```json
{
  "status": "healthy",
  "service": "NLP Translation",
  "llm_configured": true
}
```

### **Test DeepSeek API Directly:**
```bash
curl --request POST \
  --url https://api.siliconflow.cn/v1/chat/completions \
  --header 'Authorization: Bearer sk-ajbyynbjuprotathizodtvlyrrmblsrmygzjcptlmmxlgeoe' \
  --header 'Content-Type: application/json' \
  --data '{
    "model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
    "messages": [{"role": "user", "content": "Say hello"}],
    "stream": false,
    "max_tokens": 100
  }'
```

---

## 📝 Features Implemented

- ✅ Natural language input field
- ✅ Optional ASN context
- ✅ AI translation via DeepSeek API
- ✅ Cypher code display
- ✅ Copy to query box functionality
- ✅ Example queries help section
- ✅ Error handling for API failures
- ✅ Loading indicators
- ✅ Integration with existing query execution

---

## 🎯 MVP Limitations

- ❌ No parameter extraction (hardcodes values)
- ❌ No Cypher validation before display
- ❌ No query refinement/conversation mode
- ❌ Fixed LLM parameters (temp, top_p)
- ❌ No caching of translations
- ❌ No user feedback collection

---

## 🚀 Next Steps (Post-MVP)

1. Add Cypher syntax validation
2. Implement parameter extraction
3. Add query refinement dialogue
4. Cache common translations
5. Add user feedback ratings
6. Implement few-shot learning examples
7. Add retry logic for failed translations

---

## 📞 Support

**If you encounter issues:**
1. Check API is running on port 8001
2. Verify DEEPSEEK_API_KEY is set
3. Check internet connection
4. Review API logs for errors
5. Test DeepSeek API directly

**Ready to test!** 🎉
