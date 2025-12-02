# 🚀 Deploying Your RAG Chatbot to Heroku

Complete guide to deploy your AI chatbot application to Heroku with public access.

---

## 📋 Prerequisites

1. **Heroku Account** (Free tier available)
   - Sign up at: https://signup.heroku.com/

2. **Heroku CLI** installed
   - Download: https://devcenter.heroku.com/articles/heroku-cli
   - Or install via Homebrew: `brew tap heroku/brew && brew install heroku`

3. **Git** installed
   - Check: `git --version`

4. **IONOS API Token**
   - You already have this in your `.env` file

---

## 🎯 Quick Deployment (5 Minutes)

### Step 1: Install Heroku CLI

```bash
# On Mac
brew tap heroku/brew && brew install heroku

# On Windows
# Download from: https://devcenter.heroku.com/articles/heroku-cli

# Verify installation
heroku --version
```

### Step 2: Login to Heroku

```bash
heroku login
# This will open a browser window - login with your credentials
```

### Step 3: Prepare Your Application

```bash
# Navigate to your project directory
cd /Users/augustinefarinola/RAG

# Initialize git repository (if not already done)
git init

# Add files
git add .

# Commit
git commit -m "Initial commit - RAG Chatbot"
```

### Step 4: Create Heroku App

```bash
# Create a new Heroku app (choose a unique name)
heroku create your-rag-chatbot-name

# Or let Heroku generate a random name
heroku create
```

### Step 5: Set Environment Variables

```bash
# Add your IONOS API token to Heroku
heroku config:set IONOS_API_TOKEN="your-ionos-token-here"

# Verify it was set
heroku config:get IONOS_API_TOKEN
```

### Step 6: Deploy!

```bash
# Push to Heroku
git push heroku main

# Or if your branch is named master
git push heroku master
```

### Step 7: Open Your App

```bash
# Open in browser
heroku open

# Or check the URL
heroku info
```

Your chatbot is now live at: `https://your-app-name.herokuapp.com` 🎉

---

## 📁 Required Files (Already Created)

Your project now has these Heroku configuration files:

### 1. **Procfile**
```
web: sh setup.sh && streamlit run src/chatbot_app.py --server.port=$PORT --server.address=0.0.0.0
```
- Tells Heroku how to run your app
- Uses dynamic `$PORT` variable
- Runs setup script first

### 2. **setup.sh**
```bash
#!/bin/bash
mkdir -p ~/.streamlit/
# ... Streamlit configuration
```
- Configures Streamlit for Heroku
- Sets headless mode
- Disables CORS

### 3. **runtime.txt**
```
python-3.12.0
```
- Specifies Python version

### 4. **requirements.txt**
```
streamlit>=1.28.0
requests>=2.31.0
python-dotenv>=1.0.0
PyPDF2>=3.0.0
beautifulsoup4>=4.12.0
```
- Lists Python dependencies

### 5. **.gitignore**
- Excludes sensitive files (.env)
- Excludes data files (too large)

---

## ⚙️ Configuration Options

### Choose Which App to Deploy

By default, the Procfile deploys the **Chatbot App**. You can change this:

#### Deploy RAG Search Instead:
Edit `Procfile`:
```
web: sh setup.sh && streamlit run src/rag_gui_with_llm.py --server.port=$PORT --server.address=0.0.0.0
```

#### Deploy Both (Multi-App Setup):
You'll need to create separate Heroku apps:

```bash
# Create first app for chatbot
heroku create my-chatbot --remote chatbot
heroku config:set IONOS_API_TOKEN="token" --app my-chatbot
git push chatbot main

# Create second app for RAG search
heroku create my-rag-search --remote rag-search
heroku config:set IONOS_API_TOKEN="token" --app my-rag-search
# Edit Procfile to use rag_gui_with_llm.py
git push rag-search main
```

---

## 🔒 Security Best Practices

### 1. Environment Variables
✅ **NEVER commit .env to git**
- Already excluded in `.gitignore`
- Use `heroku config:set` instead

### 2. Protect Your Token
```bash
# Rotate token if exposed
# Generate new token in IONOS dashboard
# Update Heroku:
heroku config:set IONOS_API_TOKEN="new-token"
```

### 3. Optional: Add Basic Auth
Create `src/auth.py`:
```python
import streamlit as st

def check_password():
    def password_entered():
        if st.session_state["password"] == "your-secret-password":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

# Use in your app:
# if not check_password():
#     st.stop()
```

---

## 📊 Monitoring & Logs

### View Logs
```bash
# Real-time logs
heroku logs --tail

# Last 100 lines
heroku logs -n 100

# Filter for errors
heroku logs --tail | grep ERROR
```

### Check App Status
```bash
# View app info
heroku info

# Check dynos (servers)
heroku ps

# Restart app
heroku restart
```

### Performance Monitoring
```bash
# View metrics (requires paid plan)
heroku addons:create heroku-metrics
```

---

## 💰 Heroku Pricing

### Free Tier (Hobby)
- ✅ Perfect for testing/demos
- ✅ 550-1000 free dyno hours/month
- ⚠️ App sleeps after 30 min of inactivity
- ⚠️ Cold start (~30 seconds on first visit)

### Eco Dyno ($5/month)
- ✅ Shared resources
- ✅ App doesn't sleep
- ✅ Better for regular use

### Basic Dyno ($7/month)
- ✅ Dedicated resources
- ✅ Custom domains
- ✅ SSL certificates

### Standard/Performance ($25-500/month)
- For production apps with high traffic

**Recommendation:** Start with **Free tier** for testing, upgrade to **Eco ($5/month)** for production.

---

## 🔧 Troubleshooting

### Error: "Application Error"
```bash
# Check logs
heroku logs --tail

# Common issue: Missing buildpack
heroku buildpacks:set heroku/python
```

### Error: "ModuleNotFoundError"
```bash
# Check requirements.txt is correct
cat requirements.txt

# Force rebuild
git commit --allow-empty -m "Rebuild"
git push heroku main
```

### App is Slow/Times Out
```bash
# Increase timeout in setup.sh
# Add to config.toml:
[server]
maxUploadSize = 500
```

### Environment Variable Not Working
```bash
# List all config vars
heroku config

# Set variable again
heroku config:set IONOS_API_TOKEN="your-token"

# Restart
heroku restart
```

---

## 🚀 Advanced: Custom Domain

### Add Custom Domain (Requires paid plan)

```bash
# Add domain
heroku domains:add www.your-domain.com

# Get DNS target
heroku domains

# Add CNAME record in your DNS provider:
# CNAME: www.your-domain.com → your-app-name.herokuapp.com
```

---

## 📈 Scaling

### Scale Dynos
```bash
# Scale up to 2 dynos (requires paid plan)
heroku ps:scale web=2

# Scale down to 1
heroku ps:scale web=1
```

### Performance Tips
1. **Enable Response Caching** in your app
2. **Optimize LLM calls** - use smaller models for simple queries
3. **Reduce document retrieval** - start with 2-3 sources
4. **Add loading indicators** - improve perceived performance

---

## 🔄 Updating Your App

### Deploy Updates
```bash
# Make changes to your code
# Commit changes
git add .
git commit -m "Updated chatbot response logic"

# Deploy
git push heroku main

# View deployment
heroku logs --tail
```

### Rollback if Needed
```bash
# List releases
heroku releases

# Rollback to previous version
heroku rollback
```

---

## 📱 Alternative Deployment Options

If Heroku doesn't work for you:

### 1. **Streamlit Cloud** (Easiest)
- https://streamlit.io/cloud
- Free tier available
- Connects directly to GitHub
- Automatic deployments

### 2. **Railway** (Heroku Alternative)
- https://railway.app/
- Similar to Heroku
- Better free tier

### 3. **Render**
- https://render.com/
- Free tier with 750 hours/month
- No credit card required

### 4. **Fly.io**
- https://fly.io/
- Good performance
- Free tier available

### 5. **IONOS Cloud Server** (Already have!)
- Follow `DEPLOYMENT_GUIDE.md`
- Full control
- Use systemd service

---

## ✅ Deployment Checklist

Before deploying:

- [ ] Test app locally (http://localhost:8503)
- [ ] Verify IONOS API token works
- [ ] Check all dependencies in requirements.txt
- [ ] Create Heroku account
- [ ] Install Heroku CLI
- [ ] Initialize git repository
- [ ] Create `.gitignore` (exclude .env)
- [ ] Create Heroku app
- [ ] Set environment variables
- [ ] Deploy to Heroku
- [ ] Test deployed app
- [ ] Monitor logs for errors
- [ ] Share URL with users!

---

## 🎊 Your App is Live!

Once deployed, you'll have:

✅ **Public URL:** `https://your-app-name.herokuapp.com`
✅ **Accessible anywhere:** No VPN or special access needed
✅ **Automatic HTTPS:** Free SSL certificate
✅ **Easy updates:** Just `git push heroku main`
✅ **Professional:** Share with anyone via link

---

## 📞 Support

### Heroku Issues
- Docs: https://devcenter.heroku.com/
- Status: https://status.heroku.com/
- Support: https://help.heroku.com/

### App Issues
- Check logs: `heroku logs --tail`
- Restart: `heroku restart`
- GitHub issues: Create issue in your repo

---

## 🎯 Next Steps After Deployment

1. **Test thoroughly** - Try multiple queries
2. **Monitor usage** - Check Heroku metrics
3. **Gather feedback** - Share with beta users
4. **Optimize costs** - Upgrade if needed
5. **Add features** - Custom branding, analytics, etc.

**Your RAG chatbot is ready for the world!** 🌍🤖
