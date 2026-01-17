# Raspberry Pi Zero 2W Setup Guide
## Deploy Electrical Shop Management System on Raspberry Pi Zero 2W

---

## 📋 **Hardware Requirements**

- **Raspberry Pi Zero 2W** (512MB RAM)
- **MicroSD Card** (32GB or larger, Class 10)
- **USB Power Supply** (5V/2.5A minimum)
- **USB-C to USB-A Adapter** (for keyboard/mouse)
- **Ethernet Adapter** (optional, or use WiFi)
- **Monitor with HDMI Mini Adapter** (for initial setup)

---

## ⚙️ **Operating System Choice**

### **32-bit vs 64-bit for Pi Zero 2W**

| Feature | 32-bit | 64-bit |
|---------|--------|--------|
| RAM Usage | Lower ✅ | Slightly higher |
| Performance | Excellent | Good |
| Recommended | **YES** | Optional |

**Recommendation:** Use **32-bit OS Lite** for best performance on Pi Zero 2W

---

## 🔧 **Step 1: Install Operating System**

### Using Raspberry Pi Imager (Windows/Mac/Linux)

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Insert microSD card into your computer
3. Open Raspberry Pi Imager
4. Click **"Choose Device"** → Select **Raspberry Pi Zero 2W**
5. Click **"Choose OS"** → Select **Raspberry Pi OS Lite (32-bit)**
6. Click **"Choose Storage"** → Select your microSD card
7. Click **"Write"** and wait for completion
8. Eject the card safely

---

## 🎯 **Step 2: First Boot Setup**

1. Insert microSD card into Raspberry Pi Zero 2W
2. Connect:
   - Power supply via USB
   - Monitor via HDMI mini adapter
   - Keyboard and mouse via USB hub
3. Wait **2-3 minutes** for first boot
4. Login:
   - Username: `pi`
   - Password: `raspberry` (change this immediately!)

---

## ⚙️ **Step 3: Initial Configuration**

### Change Default Password
```bash
passwd
# Enter new password (you'll be prompted twice)
```

### Configure System Settings
```bash
sudo raspi-config
```

**Navigate and configure:**
- **System Options** → **Hostname** → Change to something memorable (e.g., `electrical-shop`)
- **System Options** → **Password** → Update password again
- **Interface Options** → **SSH** → Enable for remote access
- **Localisation Options** → **Timezone** → Set your timezone
- **Finish** and reboot when prompted

### Reboot
```bash
sudo reboot
```

---

## 🌐 **Step 4: Network Configuration**

### Option A: WiFi Setup
```bash
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
```

Add your WiFi credentials at the end:
```
network={
    ssid="YOUR_WIFI_NAME"
    psk="YOUR_WIFI_PASSWORD"
}
```

Save (Ctrl+X → Y → Enter) and reboot:
```bash
sudo reboot
```

### Option B: Ethernet
Connect Ethernet adapter directly - it should work automatically.

### Find Your Pi's IP Address
```bash
hostname -I
```
**Note:** You'll need this IP to connect remotely.

---

## 🔌 **Step 5: Remote Access via SSH (Optional but Recommended)**

From your Windows PC or laptop, open PowerShell and connect:
```bash
ssh pi@192.168.0.XXX
# Replace XXX with your Pi's IP address found above
```

From this point, you can work entirely over SSH without keyboard/mouse/monitor connected.

---

## 🔄 **Step 6: Update System**

```bash
sudo apt update
sudo apt upgrade -y
sudo reboot
```

---

## 🐍 **Step 7: Install Python and Dependencies**

```bash
# Install Python 3, pip, and git
sudo apt install python3 python3-pip python3-venv git -y

# Verify Python version
python3 --version
# Should be Python 3.11 or higher
```

---

## 📦 **Step 8: Clone and Setup Application**

### Create Application Directory
```bash
mkdir -p ~/apps
cd ~/apps
```

### Clone Repository
```bash
git clone https://github.com/VenkatSaiKum/saibabaelec.git
cd saibabaelec
```

### Create Virtual Environment
```bash
python3 -m venv venv
```

### Activate Virtual Environment
```bash
source venv/bin/activate
# Your prompt should now show (venv) prefix
```

### Install Dependencies
```bash
pip install Flask==2.3.3 Flask-CORS==4.0.0 gunicorn==21.2.0 APScheduler==3.10.4
```

### Create Data Directory
```bash
mkdir -p data
```

---

## 🗄️ **Step 9: Database Configuration**

Your app **uses SQLite by default** - no additional setup needed!

✅ **Advantages for Pi Zero 2W:**
- No database server to run
- Uses minimal RAM and CPU
- Data stored in `data/electrical_shop.db`
- Persists forever (even after reboot)
- Perfect for single-user/small business use

**That's it!** Your database is ready.

---

## 🚀 **Step 10: Create Systemd Service (Auto-Start on Boot)**

Create a systemd service file so your app starts automatically on reboot:

```bash
sudo nano /etc/systemd/system/electrical-shop.service
```

**Paste the following content:**
```ini
[Unit]
Description=Electrical Shop Management System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/apps/saibabaelec
Environment="PATH=/home/pi/apps/saibabaelec/venv/bin"
ExecStart=/home/pi/apps/saibabaelec/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 1 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Important:** `--workers 1` is optimized for Pi Zero 2W's limited resources.

### Save and Exit
Press `Ctrl+X` → `Y` → `Enter`

### Enable and Start Service
```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable electrical-shop

# Start the service immediately
sudo systemctl start electrical-shop

# Check if service is running
sudo systemctl status electrical-shop
```

You should see:
```
● electrical-shop.service - Electrical Shop Management System
     Loaded: loaded (/etc/systemd/system/electrical-shop.service)
     Active: active (running)
```

---

## 🌍 **Step 11: Access Your Application**

### From Windows PC / Laptop / Mobile (Same WiFi Network)
```
http://192.168.0.XXX:5000
```
Replace `XXX` with your Pi's IP address found in Step 4.

### From Raspberry Pi Itself
```
http://localhost:5000
```

---

## 🔍 **Step 12: Useful Commands for Management**

### Check Service Status
```bash
sudo systemctl status electrical-shop
```

### View Application Logs
```bash
sudo journalctl -u electrical-shop -n 50 -f
```
(Use `Ctrl+C` to exit logs)

### Restart Service
```bash
sudo systemctl restart electrical-shop
```

### Stop Service
```bash
sudo systemctl stop electrical-shop
```

### Start Service
```bash
sudo systemctl start electrical-shop
```

### Disable Auto-Start (if needed)
```bash
sudo systemctl disable electrical-shop
```

---

## 🔒 **Step 13: Optional - Setup Nginx Reverse Proxy**

To run on port 80 (no port number needed):

### Install Nginx
```bash
sudo apt install nginx -y
```

### Create Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/electrical-shop
```

**Paste this content:**
```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 60s;
    }

    location /static {
        alias /home/pi/apps/saibabaelec/static;
        expires 30d;
    }
}
```

### Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/electrical-shop /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site
```

### Test and Restart Nginx
```bash
sudo nginx -t
sudo systemctl restart nginx
```

### Access Without Port Number
Now visit: `http://192.168.0.XXX` (no `:5000` needed)

---

## 🛠️ **Step 14: Troubleshooting**

### App Not Starting?
```bash
sudo systemctl status electrical-shop
sudo journalctl -u electrical-shop -n 20
```

### Can't Access from Browser?
1. Check Pi's IP: `hostname -I`
2. Check firewall isn't blocking port 5000
3. Check service is running: `sudo systemctl status electrical-shop`

### Low Disk Space?
```bash
df -h
```

### High CPU Usage?
This is normal on Pi Zero 2W - consider reducing `--workers` value further (already at 1).

### SSH Connection Issues?
```bash
sudo systemctl restart ssh
sudo systemctl status ssh
```

---

## 📝 **Quick Reference - Commands Summary**

```bash
# SSH into Pi
ssh pi@192.168.0.XXX

# Activate virtual environment
source ~/apps/saibabaelec/venv/bin/activate

# Check service status
sudo systemctl status electrical-shop

# View logs
sudo journalctl -u electrical-shop -f

# Restart app
sudo systemctl restart electrical-shop

# Find Pi's IP
hostname -I

# Reboot Pi
sudo reboot

# Shutdown Pi
sudo shutdown -h now
```

---

## ✅ **Setup Complete!**

Your Electrical Shop Management System is now running on Raspberry Pi Zero 2W! 

- **Access URL:** `http://192.168.0.XXX:5000`
- **Auto-starts on boot** via systemd service
- **Uses SQLite** (no database server needed)
- **Optimized for Pi Zero 2W** with 1 worker process

**Happy billing! 🎉**
