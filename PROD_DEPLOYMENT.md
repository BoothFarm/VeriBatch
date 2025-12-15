# VeriBatch Production Deployment Guide

This guide details the steps to deploy VeriBatch (OriginStack) on an Ubuntu 24.04 server using Nginx, PostgreSQL, and Gunicorn/Uvicorn with Let's Encrypt SSL.

## 1. System Preparation

Update your system and install necessary packages.

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib nginx certbot python3-certbot-nginx unzip acl
```

## 2. Database Setup

Configure PostgreSQL with a dedicated user and database.

```bash
# Switch to the postgres user
sudo -i -u postgres

# Create a user 'originstack' with a password (you will be prompted to enter it)
# We recommend using a strong password. For this guide, we assume 'originstack' matches the default config.
createuser --interactive --pwprompt
# Enter name of role to add: originstack
# Enter password for new role: originstack (or your secure password)
# Shall the new role be a superuser? (y/n) n
# Shall the new role be allowed to create databases? (y/n) y
# Shall the new role be allowed to create more new roles? (y/n) n

# Create the database owned by the new user
createdb -O originstack originstack

# Exit the postgres user session
exit
```

## 3. Application Installation

We will install the application in `/var/www/veribatch`.

### 3.1 Unzip and Permissions

Assuming you have uploaded `VeriBatch.zip` to your home directory:

```bash
# Create target directory
sudo mkdir -p /var/www/veribatch

# Unzip contents (ensure the zip doesn't have a parent folder inside, if so, move contents up)
sudo unzip ~/VeriBatch.zip -d /var/www/veribatch

# Set ownership to your user for now (to make editing easier), 
# later we will give ownership to the www-data group.
sudo chown -R $USER:www-data /var/www/veribatch
sudo chmod -R 775 /var/www/veribatch
```

### 3.2 Python Environment

```bash
cd /var/www/veribatch/backend

# Create virtual environment
python3 -m venv venv

# Activate and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Install Gunicorn (Production Server)
pip install gunicorn

deactivate
```

## 4. Configuration

### 4.1 Environment Variables

Create a `.env` file for the backend.

```bash
nano /var/www/veribatch/backend/.env
```

Paste the following content (update passwords as needed):

```ini
# /var/www/veribatch/backend/.env

# Update 'localhost' if DB is on another server
# Format: postgresql://user:password@host:port/database
DATABASE_URL=postgresql://originstack:originstack@localhost:5432/originstack

# Generate a strong random key: openssl rand -hex 32
SECRET_KEY=change-this-to-a-secure-random-string

# Optional: Set to 'production' to disable debug features if added later
ENVIRONMENT=production
```

## 5. Systemd Service

Create a service file to keep VeriBatch running in the background.

```bash
sudo nano /etc/systemd/system/veribatch.service
```

Add the following configuration:

```ini
[Unit]
Description=Gunicorn instance to serve VeriBatch
After=network.target

[Service]
# User/Group to run as (standard web user)
User=www-data
Group=www-data

# Project root
WorkingDirectory=/var/www/veribatch/backend

# Environment variables
Environment="PATH=/var/www/veribatch/backend/venv/bin"
EnvironmentFile=/var/www/veribatch/backend/.env

# Run command (Gunicorn + Uvicorn Workers)
# -w 4: Number of workers (2 x CPUs + 1 is a good rule of thumb)
# -k: Worker class
# -b: Bind address (localhost only, Nginx will proxy to this)
ExecStart=/var/www/veribatch/backend/venv/bin/gunicorn \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    -b 127.0.0.1:8000 \
    app.main:app

Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable and Start the Service:**

```bash
# Fix ownership before starting
sudo chown -R www-data:www-data /var/www/veribatch

# Start service
sudo systemctl daemon-reload
sudo systemctl start veribatch
sudo systemctl enable veribatch

# Check status
sudo systemctl status veribatch
```

## 6. Nginx Configuration

Configure Nginx to act as a reverse proxy.

```bash
sudo nano /etc/nginx/sites-available/veribatch
```

Add the following (replace `boothfarmenterprises.ca` with your actual domain):

```nginx
server {
    server_name boothfarmenterprises.ca www.boothfarmenterprises.ca;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Serve static files directly (Optional, if you add static assets later)
    # location /static {
    #     alias /var/www/veribatch/frontend/static;
    # }
}
```

**Activate the Site:**

```bash
sudo ln -s /etc/nginx/sites-available/veribatch /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

## 7. SSL Certificate (Let's Encrypt)

Secure your site with HTTPS.

```bash
sudo certbot --nginx -d boothfarmenterprises.ca -d www.boothfarmenterprises.ca
```

Follow the prompts. Certbot will automatically update your Nginx config to force HTTPS.

## 8. Verification & Troubleshooting

- **Check Logs:**
  - App Logs: `sudo journalctl -u veribatch -f`
  - Nginx Error Logs: `sudo tail -f /var/log/nginx/error.log`
- **Restart App:** `sudo systemctl restart veribatch`
- **Database Migration:** 
  If you need to initialize tables manually (though the app does this on startup):
  ```bash
  cd /var/www/veribatch/backend
  source venv/bin/activate
  python3 -c "from app.db.database import Base, engine; Base.metadata.create_all(bind=engine)"
  ```
