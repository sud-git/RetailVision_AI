# Network Access Configuration Guide

## Problem
Frontend works in VS Code preview but not accessible from external browser on `localhost:3000`

## Root Cause
Next.js dev server was binding to `127.0.0.1` (localhost only) instead of `0.0.0.0` (all interfaces)

---

## ✅ SOLUTION APPLIED

### 1. **Updated npm Scripts** ✅

**Before:**
```json
"dev": "next dev -p 3000"
```

**After:**
```json
"dev": "next dev -p 3000 --hostname 0.0.0.0",
"dev:local": "next dev -p 3000 --hostname localhost",
"start": "next start -p 3000 --hostname 0.0.0.0",
"start:local": "next start -p 3000 --hostname localhost"
```

### 2. **Updated next.config.js** ✅
- Added support for all localhost variants
- Added `0.0.0.0` to allowed image sources
- Removed strict localhost binding

### 3. **Created Helper Scripts** ✅

**For Local Development Only:**
- `dev-local.sh` (macOS/Linux)
- `dev-local.bat` (Windows)
- Command: `npm run dev:local`

**For External Browser Access:**
- `dev-external.sh` (macOS/Linux)
- `dev-external.bat` (Windows)
- Auto-detects local IP address
- Command: `npm run dev` (uses `--hostname 0.0.0.0`)

### 4. **Updated Docker Compose** ✅
- Frontend container now starts with `--hostname 0.0.0.0`
- Proper port mapping maintained

---

## 🚀 HOW TO USE

### **Option 1: Direct npm (Recommended for Development)**

Start frontend with external access enabled:

```bash
cd frontend
npm install
npm run dev
```

**Access from any browser on your machine:**
- Local: `http://localhost:3000`
- Network: `http://<your-machine-ip>:3000`

### **Option 2: Using Helper Scripts**

**External Browser Access (Windows):**
```bash
frontend\dev-external.bat
```

**External Browser Access (macOS/Linux):**
```bash
bash frontend/dev-external.sh
```

**Local Only (Windows):**
```bash
frontend\dev-local.bat
```

**Local Only (macOS/Linux):**
```bash
bash frontend/dev-local.sh
```

### **Option 3: Docker Compose**

```bash
docker-compose -f docker-compose.dev.yml up -d frontend
# Access: http://localhost:3000
```

---

## 🔍 VERIFICATION

### Check if frontend is accessible:

```bash
# From your machine
curl http://localhost:3000

# From another device on network
curl http://<machine-ip>:3000
```

### Find your machine's IP:

**Windows:**
```bash
ipconfig | find "IPv4"
```

**macOS/Linux:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

---

## 📝 URL CONFIGURATION

### For Local Development (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### For External Browser Access
If accessing from another machine:
```
NEXT_PUBLIC_API_URL=http://<backend-ip>:8000
NEXT_PUBLIC_WS_URL=ws://<backend-ip>:8000
```

---

## 🔧 TROUBLESHOOTING

### Port 3000 Already in Use

**Windows:**
```bash
netstat -ano | findstr :3000
taskkill /PID <PID> /F
npm run dev
```

**macOS/Linux:**
```bash
lsof -ti:3000 | xargs kill -9
npm run dev
```

### Still Can't Access from External Browser

**Check 1: Verify server is running**
```bash
netstat -an | grep 3000    # Windows
lsof -i :3000              # macOS/Linux
```

**Check 2: Verify binding to 0.0.0.0**
Should see output like:
```
LISTENING 0.0.0.0:3000
```

**Check 3: Check Firewall**
- Windows: Check Windows Defender Firewall
- macOS: Check System Preferences > Security & Privacy > Firewall
- Linux: Check iptables or ufw

**Check 4: Check CORS**
If API calls fail, check backend CORS configuration

**Check 5: Verify API URL in code**
Open browser console and check `window.env` variables

### WebSocket Connection Fails

Ensure `NEXT_PUBLIC_WS_URL` is correct:
```javascript
// In browser console
console.log(process.env.NEXT_PUBLIC_WS_URL)
```

---

## 📋 FILES MODIFIED

| File | Change | Purpose |
|------|--------|---------|
| `package.json` | Added `--hostname 0.0.0.0` | All interfaces binding |
| `next.config.js` | Updated image patterns | Support all localhost variants |
| `.env.local` | Added comments | Clarify IP configuration |
| `docker-compose.dev.yml` | Updated frontend command | Host binding in Docker |
| `dev-external.sh` | **NEW** | Helper script for external access |
| `dev-external.bat` | **NEW** | Helper script for external access |
| `dev-local.sh` | **NEW** | Helper script for local only |
| `dev-local.bat` | **NEW** | Helper script for local only |

---

## 🎯 QUICK START

### **Fastest Way to Fix:**

```bash
# 1. Go to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server (now with external access)
npm run dev

# 4. Open in browser
http://localhost:3000
```

### **Access from other devices on network:**

Get your IP:
```bash
# Windows
ipconfig | find "IPv4"

# macOS/Linux
hostname -I
```

Then open:
```
http://<your-ip>:3000
```

---

## 💡 WHAT CHANGED

### npm Scripts
```diff
- "dev": "next dev -p 3000"
+ "dev": "next dev -p 3000 --hostname 0.0.0.0"
+ "dev:local": "next dev -p 3000 --hostname localhost"

- "start": "next start -p 3000"
+ "start": "next start -p 3000 --hostname 0.0.0.0"
+ "start:local": "next start -p 3000 --hostname localhost"
```

### next.config.js
```diff
images: {
  remotePatterns: [
    { protocol: 'http', hostname: 'localhost' },
+   { protocol: 'http', hostname: '127.0.0.1' },
+   { protocol: 'http', hostname: '0.0.0.0' },
    { protocol: 'https', hostname: '**' },
  ],
}
```

### Docker Command
```diff
- sh -c "npm install && npm run dev"
+ sh -c "npm install && npm run dev -- --hostname 0.0.0.0"
```

---

## ✨ NEXT STEPS

1. ✅ Run `npm run dev`
2. ✅ Access `http://localhost:3000`
3. ✅ Verify external browser access works
4. ✅ Proceed to Phase 2: Video ingestion

---

## 📞 REFERENCE

- Next.js Docs: https://nextjs.org/docs/api-reference/cli#development
- Hostname flag: `--hostname <address>` binds to specified address
- Default: `127.0.0.1` (localhost only)
- For all interfaces: `0.0.0.0` (requires explicit flag)

---

**Your frontend is now accessible from any browser on your machine!** 🎉
