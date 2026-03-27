# 🔧 Fix: Frontend Not Running (ERR_CONNECTION_REFUSED)

## ❌ Problem
You're getting "ERR_CONNECTION_REFUSED" on localhost:3000
**This means the frontend server is NOT running.**

---

## ✅ Solution: Start the Frontend Server

### Step 1: Open New Terminal in VS Code
1. Look at the bottom of VS Code
2. Find the terminal area
3. **Click the "+" button** to open a NEW terminal
   - OR press `Ctrl + Shift + ~` (backtick)

### Step 2: Navigate to Frontend Directory
In the NEW terminal, type:
```powershell
cd "E:\Study material\Sem 6\Final Year Project\aeroguard_frontend"
```

Press Enter.

### Step 3: Check if Dependencies are Installed
```powershell
dir node_modules
```

**If you see a list of folders** → Dependencies are installed ✅
**If you see "cannot find path"** → Run `npm install` first

### Step 4: Install Dependencies (If Needed)
**Only if Step 3 failed:**
```powershell
npm install
```
Wait 2-3 minutes for it to finish.

### Step 5: Start Frontend Server
```powershell
npm run dev
```

**You MUST see this output:**
```
  VITE v7.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
```

**If you see this, the server is running!** ✅

---

## 🎯 Important Notes

1. **Keep the terminal open** - Don't close it! The server runs in that terminal.
2. **You need 2 terminals**:
   - Terminal 1: Backend (port 8000)
   - Terminal 2: Frontend (port 3000)
3. **Both must be running** at the same time!

---

## ✅ Success Checklist

- [ ] Terminal 1: Backend running (shows "Application startup complete")
- [ ] Terminal 2: Frontend running (shows "Local: http://localhost:3000/")
- [ ] Browser: Can open http://localhost:3000
- [ ] See login page (not error page)

---

## 🐛 Common Issues

### Issue: "npm is not recognized"
**Solution**: Node.js might not be in PATH
- Restart VS Code after installing Node.js
- Or use full path to npm

### Issue: "Port 3000 already in use"
**Solution**: 
- Close other applications using port 3000
- Or change port in `vite.config.js`

### Issue: "Cannot find module"
**Solution**:
- Run `npm install` again
- Delete `node_modules` folder and `package-lock.json`
- Run `npm install` again

---

## 🚀 Quick Start Commands

**Copy and paste these one by one:**

```powershell
# Terminal 2 - Frontend
cd "E:\Study material\Sem 6\Final Year Project\aeroguard_frontend"
npm run dev
```

**Wait for:**
```
➜  Local:   http://localhost:3000/
```

**Then open:** http://localhost:3000

---

**Try running `npm run dev` in the frontend directory and tell me what you see!** 🚀

