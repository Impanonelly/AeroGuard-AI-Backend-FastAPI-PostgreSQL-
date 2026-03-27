# 🚀 Start Both Servers - Complete Guide

## ❌ Problem
Frontend server is NOT running, so you get "ERR_CONNECTION_REFUSED"

---

## ✅ Solution: Start Frontend Server

### Method 1: Using Batch File (Easiest!)

1. **Open Windows File Explorer**
2. **Navigate to**: `E:\Study material\Sem 6\Final Year Project\aeroguard_frontend`
3. **Double-click**: `start_frontend.bat`
4. **Wait for**: "Local: http://localhost:3000/"
5. **Keep the window open!**

---

### Method 2: Using VS Code Terminal

**Step 1: Open NEW Terminal**
- Click the **"+"** button next to terminal tab
- OR press `Ctrl + Shift + ~`

**Step 2: Navigate to Frontend**
```powershell
cd "E:\Study material\Sem 6\Final Year Project\aeroguard_frontend"
```

**Step 3: Verify Directory**
```powershell
dir package.json
```
Should show `package.json` ✅

**Step 4: Install Dependencies (First Time)**
```powershell
npm install
```
Wait 2-3 minutes...

**Step 5: Start Server**
```powershell
npm run dev
```

**You MUST see:**
```
VITE v7.x.x  ready in xxx ms
➜  Local:   http://localhost:3000/
```

---

## 🎯 What You Should Have

**Terminal 1 (Backend):**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Terminal 2 (Frontend):**
```
VITE v7.x.x  ready in xxx ms
➜  Local:   http://localhost:3000/
```

**Both terminals must stay open!**

---

## 🌐 Then Open Browser

1. **Open browser**
2. **Go to**: http://localhost:3000
3. **You should see**: AeroGuard AI Login page!

---

## 🔧 Troubleshooting

### Issue: "npm is not recognized"
**Solution**: 
- Node.js might not be in PATH
- Restart VS Code
- Or use full path: `C:\Program Files\nodejs\npm.cmd run dev`

### Issue: "Cannot find module"
**Solution**:
```powershell
cd "E:\Study material\Sem 6\Final Year Project\aeroguard_frontend"
npm install
npm run dev
```

### Issue: Port 3000 already in use
**Solution**:
- Close other apps using port 3000
- Or change port in `vite.config.js`

---

## ✅ Quick Checklist

- [ ] Backend running? (Check Terminal 1)
- [ ] Frontend directory correct? (`aeroguard_frontend`)
- [ ] Dependencies installed? (`npm install` completed)
- [ ] Frontend server started? (See "Local: http://localhost:3000/")
- [ ] Browser opened? (http://localhost:3000)
- [ ] See login page? (Not error page)

---

**Try the batch file method first - it's the easiest!** 🚀

