# ⚡ Quick Deploy to Heroku (5 Minutes)

## 1️⃣ Install Heroku CLI
```bash
brew install heroku  # Mac
# or download from heroku.com/cli
```

## 2️⃣ Login
```bash
heroku login
```

## 3️⃣ Prepare Git
```bash
cd /Users/augustinefarinola/RAG
git init
git add .
git commit -m "Deploy RAG chatbot"
```

## 4️⃣ Create & Configure App
```bash
# Create app
heroku create my-rag-chatbot

# Add your IONOS token
heroku config:set IONOS_API_TOKEN="your-ionos-token-here"
```

## 5️⃣ Deploy
```bash
git push heroku main
```

## 6️⃣ Open
```bash
heroku open
```

## ✅ Done!
Your chatbot is now live at: `https://my-rag-chatbot.herokuapp.com`

---

## 📱 Update App Later
```bash
git add .
git commit -m "Updates"
git push heroku main
```

## 🔍 View Logs
```bash
heroku logs --tail
```

## 🔄 Restart
```bash
heroku restart
```

---

**Full guide:** See `HEROKU_DEPLOYMENT.md`
