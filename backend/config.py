import os

# --- NETWORK CONFIGURATION ---
LISTEN_IP = "0.0.0.0" 
KNOCK_PORT = 8000
WIFI_INTERFACE = "wlan0"  

# --- FILE PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(BASE_DIR, "logs", "access.log")