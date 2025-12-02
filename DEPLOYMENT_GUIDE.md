# Deploying RAG GUI to IONOS Cloud Server

## Prerequisites
- IONOS Cloud Server (Ubuntu/Debian recommended)
- SSH access to your server
- Your IONOS API Token

## Step 1: Connect to Your Server

```bash
ssh user@your-server-ip
```

## Step 2: Install Python and Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install git (if needed)
sudo apt install git -y
```

## Step 3: Upload Your Files to the Server

### Option A: Using SCP (from your local machine)

```bash
# Upload the entire RAG directory
scp -r /Users/augustinefarinola/RAG user@your-server-ip:~/
```

### Option B: Using Git

```bash
# On server
cd ~
git clone your-repository-url
cd RAG
```

### Option C: Manual Upload (just essential files)

```bash
# Create directory on server
ssh user@your-server-ip "mkdir -p ~/rag-app"

# Upload files
scp src/rag_gui.py user@your-server-ip:~/rag-app/
scp .env user@your-server-ip:~/rag-app/
scp requirements.txt user@your-server-ip:~/rag-app/
```

## Step 4: Set Up the Application on Server

```bash
# SSH into server
ssh user@your-server-ip

# Navigate to directory
cd ~/rag-app  # or ~/RAG/src

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 5: Configure Environment Variables

```bash
# Edit .env file
nano .env

# Make sure it contains:
# IONOS_API_TOKEN=your_actual_token_here
```

## Step 6: Run the Application

### Option A: Run in Foreground (for testing)

```bash
streamlit run rag_gui.py --server.port 8501 --server.address 0.0.0.0
```

### Option B: Run in Background (production)

```bash
# Using nohup
nohup streamlit run rag_gui.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 &

# Or using screen
screen -S rag-gui
streamlit run rag_gui.py --server.port 8501 --server.address 0.0.0.0
# Press Ctrl+A then D to detach

# Or using tmux
tmux new -s rag-gui
streamlit run rag_gui.py --server.port 8501 --server.address 0.0.0.0
# Press Ctrl+B then D to detach
```

### Option C: Run as System Service (recommended for production)

```bash
# Create service file
sudo nano /etc/systemd/system/rag-gui.service

# Add the following content:
```

```ini
[Unit]
Description=RAG GUI Streamlit Application
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/rag-app
Environment="PATH=/home/your-username/rag-app/venv/bin"
ExecStart=/home/your-username/rag-app/venv/bin/streamlit run rag_gui.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable rag-gui
sudo systemctl start rag-gui

# Check status
sudo systemctl status rag-gui

# View logs
sudo journalctl -u rag-gui -f
```

## Step 7: Configure Firewall

```bash
# Allow Streamlit port
sudo ufw allow 8501/tcp

# Or if using firewalld
sudo firewall-cmd --permanent --add-port=8501/tcp
sudo firewall-cmd --reload
```

## Step 8: Access Your Application

Open your browser and navigate to:
```
http://your-server-ip:8501
```

## Optional: Set Up Nginx Reverse Proxy (for production)

### Install Nginx

```bash
sudo apt install nginx -y
```

### Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/rag-gui
```

Add:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # or your-server-ip

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/rag-gui /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

Now access via: `http://your-domain.com` or `http://your-server-ip`

## Optional: Add SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is set up automatically
```

## Troubleshooting

### Check if app is running
```bash
ps aux | grep streamlit
```

### Check logs
```bash
# If using systemd
sudo journalctl -u rag-gui -f

# If using nohup
tail -f streamlit.log

# If using screen
screen -r rag-gui

# If using tmux
tmux attach -t rag-gui
```

### Restart application
```bash
# If using systemd
sudo systemctl restart rag-gui

# If running in background
pkill -f streamlit
# Then start again
```

### Check port availability
```bash
sudo netstat -tulpn | grep 8501
```

## Security Recommendations

1. **Use HTTPS** (SSL certificate via Let's Encrypt)
2. **Set up firewall** (only allow necessary ports)
3. **Use environment variables** (never hardcode tokens)
4. **Keep .env file secure** (chmod 600 .env)
5. **Regular updates** (apt update && apt upgrade)
6. **Consider authentication** (add Streamlit authentication or Nginx basic auth)

## Managing the Service

```bash
# Start
sudo systemctl start rag-gui

# Stop
sudo systemctl stop rag-gui

# Restart
sudo systemctl restart rag-gui

# Status
sudo systemctl status rag-gui

# Enable auto-start on boot
sudo systemctl enable rag-gui

# Disable auto-start
sudo systemctl disable rag-gui
```

## Done! 🎉

Your RAG GUI is now accessible and ready to query your IONOS vector database collection.
