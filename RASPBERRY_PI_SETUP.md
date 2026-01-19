# Raspberry Pi 5 Setup Guide
## Deploy Electrical Shop Management System on Raspberry Pi 5

---

## 📋 **Hardware Requirements**

- **Raspberry Pi 5** (4GB or 8GB RAM recommended)
- **USB-C Power Supply** (5A, 27W official adapter recommended)
- **MicroSD Card** (64GB or larger, Class 10 or better)
- **Ethernet Cable** (recommended for stability) OR WiFi
- **Keyboard, Mouse, Monitor** (for initial setup only)

---

## 🔧 **Step 1: Install Operating System**

### Option A: Ubuntu Server 24.04 LTS (Recommended)
1. Download [Ubuntu Server 24.04 LTS for Raspberry Pi](https://ubuntu.com/download/raspberry-pi)
2. Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to flash the image to your microSD card
3. Insert the microSD card into Raspberry Pi and power it on
4. Complete initial setup (username, password, WiFi/Ethernet)

### Option B: Raspberry Pi OS (64-bit)
1. Download [Raspberry Pi OS Lite (64-bit)](https://www.raspberrypi.com/software/operating-systems/)
2. Flash using Raspberry Pi Imager
3. Boot and complete setup

---

## 🌐 **Step 2: Initial Configuration**

### SSH into Raspberry Pi
```bash
# From your Windows PC, find the Pi's IP address
# Then connect via SSH (use PowerShell or Command Prompt)
ssh pi@192.168.0.XXX
# Default password: raspberry (change this immediately!)
```

### Update System
```bash
sudo apt update
sudo apt upgrade -y
sudo reboot
```

### Set Static IP Address (Optional but Recommended)
```bash
# Edit network config
sudo nano /etc/netplan/50-cloud-init.yaml

# Add static IP configuration:
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: no
      addresses:
        - 192.168.0.100/24
      gateway4: 192.168.0.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]

# Apply changes
sudo netplan apply
```

---

## 🐍 **Step 3: Install Python and Dependencies**

```bash
# Install Python 3.11+ and pip
sudo apt install python3 python3-pip python3-venv git -y

# Verify Python version
python3 --version  # Should be 3.11 or higher
```

---

## 📦 **Step 4: Clone and Setup Application**

```bash
# Create app directory
mkdir -p ~/apps
cd ~/apps

# Clone your repository
git clone https://github.com/VenkatSaiKum/saibabaelec.git
cd saibabaelec

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies (ONLY Flask, no PostgreSQL)
pip install Flask==2.3.3 Flask-CORS==4.0.0 gunicorn==21.2.0 APScheduler==3.10.4

# Create data directory
mkdir -p data
```

---

## 🗄️ **Step 5: Database Configuration**

Your app already uses **SQLite by default** when `DATABASE_URL` is not set. SQLite is perfect for Raspberry Pi:
- ✅ No extra setup needed
- ✅ Data stored in `data/electrical_shop.db`
- ✅ Persists forever (even after reboot)
- ✅ Fast enough for small business use

**No PostgreSQL installation needed!** The app will automatically use SQLite.

---

## 🚀 **Step 6: Create Systemd Service (Auto-Start on Boot)**

```bash
# Create service file
sudo nano /etc/systemd/system/electrical-shop.service
```

**Paste this content:**
```ini
[Unit]
Description=Electrical Shop Management System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/apps/saibabaelec
Environment="PATH=/home/pi/apps/saibabaelec/venv/bin"
ExecStart=/home/pi/apps/saibabaelec/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start the service:**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable electrical-shop

# Start the service now
sudo systemctl start electrical-shop

# Check status
sudo systemctl status electrical-shop
```

---

## 🌍 **Step 7: Access Your Application**

### From the Same WiFi Network:
- **On PC/Laptop:** `http://192.168.0.100:5000` (replace with your Pi's IP)
- **On Mobile:** `http://192.168.0.100:5000`

### From the Raspberry Pi itself:
- `http://localhost:5000`

---

## 🔒 **Step 8: Optional - Setup Nginx Reverse Proxy**

For better performance and to run on port 80 (http://192.168.0.100):

```bash
# Install Nginx
sudo apt install nginx -y

# Create Nginx config
sudo nano /etc/nginx/sites-available/electrical-shop
```

**Paste this:**
```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /home/pi/apps/saibabaelec/static;
    }
}
```

**Enable and restart:**
```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/electrical-shop /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

Now access at: `http://192.168.0.100` (no port needed!)

---

## 🔄 **Step 9: Update Application (Pull Latest Changes)**

```bash
# Stop the service
sudo systemctl stop electrical-shop

# Navigate to app directory
cd ~/apps/saibabaelec

# Pull latest code
git pull origin main

# Activate venv and update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl start electrical-shop

# Check logs if needed
sudo journalctl -u electrical-shop -f
```

---

## 💾 **Step 10: Backup Your Database**

```bash
# Create backup script
nano ~/backup-db.sh
```

**Paste this:**
```bash
#!/bin/bash
BACKUP_DIR="/home/pi/backups"
DB_PATH="/home/pi/apps/saibabaelec/data/electrical_shop.db"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
cp $DB_PATH $BACKUP_DIR/electrical_shop_$DATE.db

# Keep only last 30 backups
ls -t $BACKUP_DIR/electrical_shop_*.db | tail -n +31 | xargs -r rm

echo "Backup completed: electrical_shop_$DATE.db"
```

**Make executable and schedule:**
```bash
chmod +x ~/backup-db.sh

# Add to crontab (daily backup at 2 AM)
crontab -e

# Add this line:
0 2 * * * /home/pi/backup-db.sh
```

---

## 🛠️ **Troubleshooting**

### Check Service Status
```bash
sudo systemctl status electrical-shop
```

### View Logs
```bash
# Live logs
sudo journalctl -u electrical-shop -f

# Last 100 lines
sudo journalctl -u electrical-shop -n 100
```

### Restart Service
```bash
sudo systemctl restart electrical-shop
```

### Check if Port is Open
```bash
sudo netstat -tulpn | grep :5000
```

### Test Database
```bash
cd ~/apps/saibabaelec
source venv/bin/activate
python3
>>> from database import Database
>>> db = Database()
>>> products = db.fetch_all("SELECT * FROM products")
>>> print(products)
```

---

## 📱 **Mobile Access**

1. **Same WiFi:** Just enter `http://192.168.0.100:5000` on your phone browser
2. **Add to Home Screen:** 
   - Android: Tap menu → "Add to Home screen"
   - iOS: Tap Share → "Add to Home Screen"

---

## 🎯 **Key Benefits of Raspberry Pi Setup**

✅ **Persistent Data** - SQLite database stays on disk forever  
✅ **24/7 Availability** - Auto-starts on boot, always running  
✅ **No Monthly Costs** - One-time hardware purchase (~₹6000)  
✅ **Local Network Only** - Secure, no internet exposure  
✅ **Low Power** - Uses only ~5W (cheaper than cloud hosting)  
✅ **Full Control** - You own all the hardware and data  

---

## ⚠️ **Important Notes**

- **Power Supply:** Always use the official 27W USB-C adapter to avoid crashes
- **Cooling:** Consider adding a heatsink or fan for 24/7 operation
- **Backups:** Run the backup script regularly (automated via cron)
- **Updates:** Pull code updates using `git pull` and restart service
- **Security:** Change default passwords, use strong passwords
- **Network:** Use Ethernet for better stability than WiFi

---

## 🆘 **Support Commands**

```bash
# Restart Raspberry Pi
sudo reboot

# Shutdown Raspberry Pi
sudo shutdown now

# Check disk space
df -h

# Check memory usage
free -h

# Check CPU temperature
vcgencmd measure_temp

# Update system packages
sudo apt update && sudo apt upgrade -y
```

---

**🎉 Your Electrical Shop System is now running 24/7 on Raspberry Pi 5!**
