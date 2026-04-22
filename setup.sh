#!/bin/bash

# --- CONFIGURATION ---
APP_NAME="ai-fast"
APP_DIR=$(pwd)
VENV_DIR="$APP_DIR/venv"
PORT=8100
PYTHON_VERSION="python3"
JAVA_VERSION="openjdk-17-jdk"
OLLAMA_MODEL="llama3"

echo "------------------------------------------------"
echo "🚀 Starting Setup for $APP_NAME"
echo "📂 App Directory: $APP_DIR"
echo "------------------------------------------------"

# 1. Update System
echo "🔄 Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Python 3 & Virtual Environment
echo "🐍 Installing Python 3, Pip, and Venv..."
sudo apt-get install -y $PYTHON_VERSION python3-pip python3-venv

# 3. Install Java 17 (Required for LanguageTool)
echo "☕ Installing $JAVA_VERSION..."
sudo apt-get install -y $JAVA_VERSION

# 4. Install Ollama
echo "🧠 Installing Ollama..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "✅ Ollama is already installed."
fi

# 5. Pull Ollama Model
echo "📥 Pulling Ollama model: $OLLAMA_MODEL..."
sudo systemctl start ollama # Ensure ollama is running
ollama pull $OLLAMA_MODEL

# 6. Setup Virtual Environment & Install Requirements
echo "📦 Setting up Python Virtual Environment..."
if [ ! -d "$VENV_DIR" ]; then
    $PYTHON_VERSION -m venv "$VENV_DIR"
fi

echo "📥 Installing dependencies from requirements.txt..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

# 7. Generate SSL Certificates
echo "🔐 Generating Self-Signed SSL Certificates..."
if [ ! -f "$APP_DIR/cert.pem" ] || [ ! -f "$APP_DIR/key.pem" ]; then
    openssl req -x509 -newkey rsa:4096 -keyout "$APP_DIR/key.pem" -out "$APP_DIR/cert.pem" -sha256 -days 3650 -nodes -subj "/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=localhost"
    echo "✅ Certificates generated."
else
    echo "✅ Certificates already exist."
fi

# 8. Create Systemd Service
echo "⚙️ Creating systemd service: $APP_NAME..."
SERVICE_FILE="/etc/systemd/system/$APP_NAME.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=AI-Fast Application Service (FastAPI)
After=network.target ollama.service

[Service]
User=$USER
WorkingDirectory=$APP_DIR
ExecStart=$VENV_DIR/bin/uvicorn app:app --host 0.0.0.0 --port $PORT --ssl-keyfile $APP_DIR/key.pem --ssl-certfile $APP_DIR/cert.pem
Restart=always
Environment=PYTHONPATH=$APP_DIR

[Install]
WantedBy=multi-user.target
EOF

# 9. Reload Systemd and Start Service
echo "🔄 Reloading systemd and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable $APP_NAME
sudo systemctl restart $APP_NAME

echo "------------------------------------------------"
echo "✅ Setup Complete!"
echo "🌐 Your app should be running at https://localhost:$PORT"
echo "📊 Check status with: sudo systemctl status $APP_NAME"
echo "------------------------------------------------"
