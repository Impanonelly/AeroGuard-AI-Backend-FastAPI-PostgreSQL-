# ⚠️ Important: Use Global Python, Not Venv

## 🚨 The Problem
Your venv doesn't have uvicorn installed. Use the **global Python** instead.

## ✅ Solution: Use Global Python

### Step 1: Make Sure You're NOT in Venv
If you see `(venv)` in your prompt, run:
```powershell
deactivate
```

### Step 2: Start Server with Global Python
Run this command:
```powershell
python -m uvicorn main:app --reload
```

**OR** if that doesn't work, use the full path:
```powershell
C:\Python314\python.exe -m uvicorn main:app --reload
```

---

## ✅ What You Should See

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**No `(venv)` in the prompt!**

---

## 🔧 I Also Fixed the Password Error

The error about "password cannot be longer than 72 bytes" is now fixed. 
You can use any password length now - it will automatically handle it.

---

## 🎯 Quick Steps

1. **Make sure no `(venv)` in prompt** (run `deactivate` if you see it)
2. **Run**: `python -m uvicorn main:app --reload`
3. **Wait for**: "Application startup complete"
4. **Open**: http://localhost:8000/docs

---

**Try it now!** 🚀

