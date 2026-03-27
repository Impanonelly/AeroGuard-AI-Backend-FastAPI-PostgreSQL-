# 🚀 Quick Fix - Server Not Starting

## ✅ All Dependencies Installed!
The packages are now installed. Here's how to start the server:

## Method 1: Using VS Code Terminal

1. **Open VS Code Terminal** (Ctrl + `)

2. **Navigate to project folder**:
   ```powershell
   cd "E:\Study material\Sem 6\Final Year Project\aeroguard_backend"
   ```

3. **Start the server**:
   ```powershell
   python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```

4. **You should see**:
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
   INFO:     Started reloader process
   INFO:     Started server process
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   ```

5. **Open browser**: `http://localhost:8000/docs`

## Method 2: Using the Batch File

1. **Double-click** `start_server.bat` in Windows Explorer
2. Server will start automatically

## Method 3: Using Command Prompt

1. Open Command Prompt (not PowerShell)
2. Navigate to project folder
3. Run: `python -m uvicorn main:app --reload`

---

## ✅ What's Fixed

- ✅ All dependencies installed
- ✅ Import errors fixed
- ✅ Schemas reorganized
- ✅ Server code ready

---

## 🧪 Test It

Once server is running:

1. Open: `http://localhost:8000/docs`
2. Try: `GET /health` - Should return `{"status": "healthy"}`
3. Try: `POST /auth/register` - Register a user
4. Try: `POST /auth/login` - Login and get tokens

---

## ❌ If Still Not Working

Check:
1. **Python is in PATH**: `python --version` should work
2. **PostgreSQL is running**: Check if database is accessible
3. **Port 8000 is free**: No other app using port 8000
4. **Check terminal for errors**: Look for error messages

---

**The server should start now!** Try Method 1 above. 🚀

