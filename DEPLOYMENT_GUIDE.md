# Deployment Troubleshooting Guide

## Why Nothing Shows During Deployment

Your app was **failing silently** because API keys weren't configured. I've added error messages so you can now see what's wrong.

---

## ✅ Required Configuration

Before deploying, ensure these 4 secrets are set:

### Local Development (`.streamlit/secrets.toml`)
```toml
MONDAY_API_TOKEN = "your_monday_api_token_here"
GROQ_API_KEY = "your_groq_api_key_here"
WO_BOARD_ID = "12345678"  # Replace with your Work Orders board ID
DEALS_BOARD_ID = "87654321"  # Replace with your Deals board ID
```

### On Deployment Platforms

#### **Streamlit Cloud**
1. Go to your app settings
2. Select **Secrets** from the sidebar
3. Paste this and replace values:
```
MONDAY_API_TOKEN = "your_monday_api_token"
GROQ_API_KEY = "your_groq_api_key"
WO_BOARD_ID = "12345678"
DEALS_BOARD_ID = "87654321"
```
4. Deploy

#### **Heroku**
```bash
heroku config:set MONDAY_API_TOKEN="your_token"
heroku config:set GROQ_API_KEY="your_key"
heroku config:set WO_BOARD_ID="12345678"
heroku config:set DEALS_BOARD_ID="87654321"
```

#### **GitHub Actions / Docker**
Add these to environment variables in your deployment config.

---

## 🔍 How to Get Your API Keys & Board IDs

### Monday.com API Token
1. Go to https://monday.com/
2. Account Settings → Developers → API Tokens
3. Create a new token (copy the full key)
4. This token needs **Read** access to your boards

### Groq API Key
1. Go to https://console.groq.com/
2. Create an API key (free tier available)
3. Copy the full key

### Board IDs (Work Orders & Deals)
1. Go to your Monday.com board
2. Look at the URL: `https://monday.com/boards/12345678`
3. The number is your Board ID
4. Find both your Work Orders and Deals board IDs

---

## 🐛 Debugging Checklist

If the app still shows an error after deployment:

- [ ] **Check the error message** - It now shows exactly what's missing
- [ ] **Verify API tokens** - Are they valid and not expired?
- [ ] **Check board IDs** - Are they correct? Can you access them in Monday.com?
- [ ] **Check network** - Can the deployment platform reach Monday.com API?
- [ ] **Check permissions** - Does the Monday API token have read access to those boards?

---

## 📝 What I Fixed

1. Added missing `connection_error` state tracking
2. Enhanced error display with specific guidance
3. Changed validation to check for missing secrets upfront
4. Error messages now appear instead of infinite "Connecting..." state

---

## 🚀 Testing Locally First

Before deploying to production:

```bash
# Create .streamlit/secrets.toml with your real values
streamlit run app.py
```

You should see:
- ✅ "Connected to Monday.com!"
- ✅ Number of work orders loaded
- ✅ Number of deals loaded
- ✅ Chat interface appears

Only then deploy to your platform.
