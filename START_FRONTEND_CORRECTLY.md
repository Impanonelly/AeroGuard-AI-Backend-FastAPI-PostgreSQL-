# 🚀 Start Frontend - Correct Directory

## ❌ Problem
You're trying to run `npm run dev` from the **backend** directory.
You need to be in the **frontend** directory!

---

## ✅ Solution

### Step 1: Open a NEW Terminal
In VS Code:
1. **Click the "+" button** next to the terminal tab
   - This opens a **completely new terminal**
2. OR press `Ctrl + Shift + ~` (backtick)

### Step 2: Navigate to Frontend Directory
In the **NEW terminal**, type:
```powershell
cd "E:\Study material\Sem 6\Final Year Project\aeroguard_frontend"
```

**Press Enter.**

**Important**: Make sure you're in `aeroguard_frontend` (not `aeroguard_backend`)

### Step 3: Verify You're in the Right Place
Type:
```powershell
dir package.json
```

**You should see**: `package.json` listed
**If you see error**: You're in the wrong directory!

### Step 4: Start Frontend Server
```powershell
npm run dev
```

**You should see:**
```
VITE v7.x.x  ready in xxx ms
➜  Local:   http://localhost:3000/
```

---

## 🎯 You Need 2 Separate Terminals

**Terminal 1 (Backend):**
- Directory: `aeroguard_backend`
- Command: `C:\Python314\python.exe -m uvicorn main:app --reload`
- Running on: http://127.0.0.1:8000

**Terminal 2 (Frontend):**
- Directory: `aeroguard_frontend` ← **Different directory!**
- Command: `npm run dev`
- Running on: http://localhost:3000

---

## ✅ Quick Copy-Paste Commands

**For Terminal 2 (Frontend):**
```powershell
cd "E:\Study material\Sem 6\Final Year Project\aeroguard_frontend"
npm run dev
```

---

## 🔍 How to Know You're in the Right Directory

**Backend directory path ends with:**
```
...\aeroguard_backend>
```

**Frontend directory path ends with:**
```
...\aeroguard_frontend>
```

---

**Open a NEW terminal, navigate to frontend directory, then run `npm run dev`!** 🚀

