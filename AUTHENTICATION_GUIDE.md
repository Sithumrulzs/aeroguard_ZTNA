# AeroGuard Authentication Integration Guide

## ✅ What Was Done

### **Backend Changes**
1. **Added login endpoint** (`POST /api/v1/login`)
   - Validates username and password against the `admins` table
   - Uses bcrypt password verification (same as setup_db.py)
   - Returns username and device_id on success
   - Returns HTTP 401 for invalid credentials

2. **Added imports**
   - `passlib.context.CryptContext` for password verification
   - Works with existing bcrypt hashes from setup_db.py

3. **Improved startup logging**
   - Better error handling in database initialization
   - Clear console output showing database path and configuration

### **Mobile App Changes**
1. **Created AuthService** (`lib/services/auth_service.dart`)
   - `login(username, password)` - Authenticates with backend
   - `getUsername()` - Retrieves stored username
   - `isAuthenticated()` - Checks if user is logged in
   - `logout()` - Clears authentication data
   - Stores credentials securely using FlutterSecureStorage

2. **Updated SignInPage** (`lib/screens/sign_in_page.dart`)
   - Real backend authentication (was hardcoded delay before)
   - Input validation
   - Error dialogs for failed login attempts
   - Clears sensitive data after successful login

3. **Updated HomeLoadPage** (`lib/screens/home_load_page.dart`)
   - Gets authenticated username from AuthService
   - Uses it to initialize the device enclave
   - No more hardcoded 'sithum.it' username

4. **Updated main.dart**
   - Added AuthWrapper to check authentication on app startup
   - Shows login page if not authenticated
   - Shows home page if authenticated
   - Loading screen during auth check

5. **Updated AdminDashboard** (`lib/screens/admin_dashboard.dart`)
   - Logout button now calls AuthService.logout()
   - Clears stored credentials before navigating to login

---

## 🚀 Testing Workflow

### **Prerequisites**
- Backend running: `python main.py`
- Gateway IP known (e.g., 192.168.1.50)
- Admin users registered in database via `setup_db.py`

### **Step 1: Deploy Backend to VM**
```bash
scp -r backend/ <user>@<vm_ip>:/path/to/vm/
```

### **Step 2: Start Backend**
```bash
cd /path/to/vm/backend
python main.py
```

**Expected output:**
```
======================================================================
AeroGuard ZTNA Gateway Starting
======================================================================
Database: /path/to/backend/aeroguard_offline.db
Listen: 0.0.0.0:8000
CORS: Enabled for all origins (development mode)
======================================================================

[+] Database initialized: /path/to/backend/aeroguard_offline.db
[+] Tables verified / created.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### **Step 3: Deploy App to Mobile**

Get VM IP:
```bash
hostname -I
```

On your development machine:
```bash
cd aeroguard_app
flutter run -d <phone_id> --dart-define=GATEWAY_IP=192.168.1.50
```

**Get phone device ID:**
```bash
flutter devices
```

### **Step 4: Login with Admin Credentials**

Open the app and you'll see the **AEROGUARD COMMAND ACCESS** login screen.

Enter credentials from `setup_db.py`:
```
Username: sithum.it
Password: It@kss69
```

**Or any admin from setup_db.py:**
```
Username: dulshi.it       | Password: It@ds69
Username: yasas.it        | Password: It@syl69
Username: dulen.it        | Password: It@ads69
```

### **Step 5: Verify Device Registration**

After login, the app initializes the device enclave with your username.

Navigate to **VAULT** tab to see:
- **ECDSA PUBLIC KEY** - Copy this for backend registration

On the Linux VM:
```bash
sqlite3 aeroguard_offline.db
INSERT INTO authorized_devices (device_id, username, public_key, is_active)
VALUES ('admin_sithum_it', 'sithum.it', '<COPIED_PUBLIC_KEY>', 1);
.quit
```

**Or use the helper:**
```bash
python register_device.py register admin_sithum_it sithum.it <PUBLIC_KEY>
```

### **Step 6: Test Zero Trust Knock**

On your phone:
1. Navigate to **ACCESS** tab
2. Tap the central "INITIATE KNOCK" button
3. Expected: "GATEWAY OPEN" with green status

### **Step 7: Verify Backend Logs**

On the Linux VM, watch for:
```
[*] INCOMING ADMIN KNOCK FROM: sithum.it
[+] SIGNATURE VERIFIED. TUNNEL OPEN FOR <phone_ip>.
```

### **Step 8: Test Logout**

On your phone:
1. Navigate to **OVERVIEW** tab
2. Scroll down and tap **LOGOUT**
3. App returns to login screen
4. Credentials are cleared from secure storage

---

## 🔐 Credential Storage

- **Username & Device ID** stored securely in FlutterSecureStorage
- **Password** never stored (only sent for login request)
- **Logout** completely clears stored credentials

---

## 🛠️ Backend Endpoints

### **POST /api/v1/login**
**Request:**
```json
{
  "username": "sithum.it",
  "password": "It@kss69"
}
```

**Success (200):**
```json
{
  "status": "success",
  "message": "Authentication successful.",
  "username": "sithum.it",
  "device_id": "admin_sithum_it"
}
```

**Failure (401):**
```json
{
  "detail": "Invalid username or password."
}
```

---

## 📱 App Flow Diagram

```
App Start
  ↓
Check Authentication (AuthService.isAuthenticated())
  ├─ NOT authenticated → SignInPage (Login Form)
  │  └─ User enters credentials
  │     ↓
  │  POST /api/v1/login
  │     ↓
  │  Success → Store username → HomeLoadPage
  │
  └─ Authenticated → HomeLoadPage (Boot Sequence)
     ↓
     Get username from AuthService
     ↓
     Initialize Enclave with username
     ↓
     Device generates keys as admin_<username>
     ↓
     AdminDashboard (Ready for knock)
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **"Invalid username or password"** | Check credentials in setup_db.py match exactly |
| **"Could not reach gateway"** | Verify gateway IP, test `ping <vm_ip>` from phone |
| **Login hangs** | Check network connectivity, ensure backend is running |
| **Device not found after knock** | Register public key in authorized_devices table |
| **Signature verification fails** | Verify clock sync on phone/VM (30-second window) |

---

## 📝 Database Schema Reference

### **admins table** (from setup_db.py)
```sql
id              INTEGER PRIMARY KEY
username        TEXT UNIQUE  -- e.g., sithum.it
password_hash   TEXT         -- bcrypt hash
device_id       TEXT UNIQUE  -- e.g., admin_sithum_it
public_key_pem  TEXT         -- Laptop's public key
mac_address     TEXT UNIQUE  -- Laptop MAC binding
is_active       BOOLEAN      -- Account status
```

### **authorized_devices table** (created by backend)
```sql
id              INTEGER PRIMARY KEY
device_id       TEXT UNIQUE  -- Mobile device ID
username        TEXT         -- Associated username
public_key      TEXT         -- ECDSA public key
is_active       INTEGER      -- Device status
```

---

## ✨ Key Security Features

✅ **Password Hashing**: bcrypt with salts  
✅ **Secure Storage**: FlutterSecureStorage (Android KeyStore, iOS Keychain)  
✅ **ECDSA Signatures**: Hardware-level key material  
✅ **CORS Enabled**: Mobile clients can authenticate  
✅ **Replay Protection**: 30-second timestamp validation  
✅ **Audit Logging**: All login and knock attempts logged  

---

**Ready to test! 🚀**
