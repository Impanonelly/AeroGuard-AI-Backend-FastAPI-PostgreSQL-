# 🔧 Fix "Network Error" - Step by Step

## ❌ Problem
You're seeing "Network Error" when trying to register or login. This means the frontend cannot connect to the backend server.

---

## ✅ Solution: Check Both Servers Are Running

### Step 1: Check Backend Server (Port 8000)

**Open a terminal and check:**

```powershell
# Check if backend is running
# You should see: "Uvicorn running on http://127.0.0.1:8000"
```

**If backend is NOT running:**

1. **Open terminal in VS Code**
2. **Navigate to backend directory:**
   ```powershell
   cd "E:\Study material\Sem 6\Final Year Project\aeroguard_backend"
   ```

3. **Start backend server:**
   ```powershell
   C:\Python314\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```

4. **You should see:**
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000
   INFO:     Application startup complete.
   ```

5. **Test backend:**
   - Open browser: http://127.0.0.1:8000/docs
   - You should see Swagger UI (API documentation)

---

### Step 2: Check Frontend Server (Port 3000)

**Open a NEW terminal and check:**

```powershell
# Check if frontend is running
# You should see: "Local: http://localhost:3000/"
```

**If frontend is NOT running:**

1. **Open a NEW terminal in VS Code** (click "+" button)
2. **Navigate to frontend directory:**
   ```powershell
   cd "E:\Study material\Sem 6\Final Year Project\aeroguard_frontend"
   ```

3. **Start frontend server:**
   ```powershell
   npm run dev
   ```

4. **You should see:**
   ```
   VITE v7.x.x  ready in xxx ms
   ➜  Local:   http://localhost:3000/
   ```

---

## 🎯 Quick Checklist

- [ ] **Backend running?** Check terminal 1 - should show "Uvicorn running on http://127.0.0.1:8000"
- [ ] **Frontend running?** Check terminal 2 - should show "Local: http://localhost:3000/"
- [ ] **Backend accessible?** Open http://127.0.0.1:8000/docs - should see Swagger UI
- [ ] **Frontend accessible?** Open http://localhost:3000 - should see login page
- [ ] **Both terminals open?** Keep both terminals running!

---

## 🔍 Verify Connection

### Test 1: Check Backend API
1. **Open browser**: http://127.0.0.1:8000/docs
2. **Click**: `GET /` endpoint
3. **Click**: "Try it out" → "Execute"
4. **Should see**: `{"message": "AeroGuard AI Backend API"}`

### Test 2: Check Frontend Can Reach Backend
1. **Open browser**: http://localhost:3000
2. **Press F12** (Developer Tools)
3. **Click**: "Network" tab
4. **Try to register** (fill form and submit)
5. **Look for**: Request to `http://127.0.0.1:8000/auth/register`
6. **Check status**: Should be 200 or 201 (not failed/red)

---

## 🐛 Common Issues

### Issue 1: Backend Not Running
**Symptom**: "Network Error" or "Cannot connect to server"
**Solution**: Start backend server (see Step 1 above)

### Issue 2: Frontend Not Running
**Symptom**: Can't access http://localhost:3000
**Solution**: Start frontend server (see Step 2 above)

### Issue 3: Wrong Port
**Symptom**: Backend on different port
**Check**: Backend terminal should show port 8000
**Fix**: Use correct port in command

### Issue 4: CORS Error
**Symptom**: "CORS policy" error in browser console
**Solution**: Backend CORS is configured, but make sure:
- Backend is running on `127.0.0.1:8000`
- Frontend is running on `localhost:3000` or `127.0.0.1:3000`

### Issue 5: Firewall Blocking
**Symptom**: Connection refused
**Solution**: 
- Check Windows Firewall
- Make sure ports 8000 and 3000 are not blocked

---

## 🚀 Quick Start Both Servers

### Terminal 1 (Backend):
```powershell
cd "E:\Study material\Sem 6\Final Year Project\aeroguard_backend"
C:\Python314\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Terminal 2 (Frontend):
```powershell
cd "E:\Study material\Sem 6\Final Year Project\aeroguard_frontend"
npm run dev
```

**Keep both terminals open!**

---

## ✅ Success Indicators

**Backend Terminal:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Frontend Terminal:**
```
VITE v7.x.x  ready in xxx ms
➜  Local:   http://localhost:3000/
```

**Browser:**
- http://127.0.0.1:8000/docs → Shows Swagger UI ✅
- http://localhost:3000 → Shows login page ✅
- Registration works → No "Network Error" ✅

---

## 📋 What to Do Now

1. **Check if backend is running** (Terminal 1)
2. **Check if frontend is running** (Terminal 2)
3. **If not running, start them** (see commands above)
4. **Try registration again**
5. **Check browser console** (F12) for detailed errors

**Tell me:**
- Is backend running? (Check terminal 1)
- Is frontend running? (Check terminal 2)
- What do you see when you open http://127.0.0.1:8000/docs?

