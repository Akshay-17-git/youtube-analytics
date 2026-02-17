# Security Guide for YouTube Analytics Dashboard

## 🔐 API Key Security

### Local Development
- **`.env` file**: Contains your actual API keys
- **`.env` is in `.gitignore`**: Never committed to GitHub
- **Keep `.env` private**: Never share or upload this file

### Streamlit Cloud Deployment
- **DO NOT** use `.env` on Streamlit Cloud
- **Use Streamlit Secrets** instead (encrypted, secure)
- Go to: App Settings → Secrets → Add your keys

## 🚀 Deployment Steps

### 1. Local Development (Your Computer)
```bash
# .env file already configured with your keys
# Run locally
streamlit run app.py
```

### 2. Streamlit Cloud Deployment

**Step 1: Go to Streamlit Cloud**
- Visit: https://share.streamlit.io
- Sign in with GitHub

**Step 2: Deploy Your App**
- Click "New app"
- Select: `Akshay-17-git/youtube-analytics`
- Main file: `app.py`
- Click "Deploy"

**Step 3: Add Secrets (CRITICAL)**
- Go to App Settings → Secrets
- Add these keys:
```toml
YOUTUBE_API_KEY = "your_youtube_api_key_here"
OPENAI_API_KEY = "your_openai_api_key_here"
```

**Step 4: Restart App**
- Secrets are loaded on app restart

## ⚠️ Security Checklist

- [x] `.env` in `.gitignore` (local keys protected)
- [x] `.streamlit/secrets.toml` in `.gitignore` (cloud keys protected)
- [x] `secrets.toml.example` template provided
- [x] No API keys in source code
- [x] No API keys in README or docs

## 🔄 If Keys Are Exposed

1. **Immediately revoke** the exposed key in Google Cloud Console / OpenAI dashboard
2. **Generate new keys**
3. **Update** `.env` file locally
4. **Update** Streamlit Cloud Secrets
5. **Never commit** the new keys

## 📞 Support

If you accidentally exposed your keys, contact:
- YouTube API Support: https://developers.google.com/youtube/v3/support
- OpenAI Support: https://help.openai.com/
