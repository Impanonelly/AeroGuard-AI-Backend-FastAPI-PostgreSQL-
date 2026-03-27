# 🔧 Fix Login - Complete Guide

## ✅ What I've Checked

1. **Password Verification**: ✅ Working correctly
2. **User in Database**: ✅ Found test user
3. **Login Code**: ✅ Looks correct

---

## 🚨 Most Likely Issue: Servers Not Running

**Before trying to login, make sure BOTH servers are running!**

### Step 1: Start Backend Server

**Open Terminal 1:**
```powershell
cd "E:\Study material\Sem 6\Final Year Project\aeroguard_backend"
C:\Python314\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**Wait for:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Step 2: Start Frontend Server

**Open Terminal 2 (NEW terminal):**
```powershell
cd "E:\Study material\Sem 6\Final Year Project\aeroguard_frontend"
npm run dev
```

**Wait for:**
```
VITE v7.x.x  ready in xxx ms
➜  Local:   http://localhost:3000/
```

---

## 🧪 Test Login

### Test Credentials:
- **Email**: `test_registration@aeroguard.com`
- **Password**: `Test123!`

### Steps:
1. **Open**: http://localhost:3000/login
2. **Enter email**: `test_registration@aeroguard.com`
3. **Enter password**: `Test123!`
4. **Click**: Login
5. **Expected**: Redirects to dashboard

---

## 🐛 If Login Still Fails

### Check 1: Browser Console (F12)
1. **Press F12** in browser
2. **Click "Console" tab**
3. **Try login again**
4. **Look for red error messages**
5. **Tell me what error you see**

### Check 2: Network Tab (F12)
1. **Press F12** in browser
2. **Click "Network" tab**
3. **Try login again**
4. **Find request**: `POST http://127.0.0.1:8000/auth/login`
5. **Click on it**
6. **Check "Response" tab** - what error message?

### Check 3: Backend Terminal
- Look at backend terminal
- Do you see any error messages when you try to login?

---

## 🔍 Common Login Errors

### Error 1: "Network Error"
**Cause**: Backend server not running
**Solution**: Start backend server (see Step 1 above)

### Error 2: "Incorrect email or password"
**Cause**: Wrong credentials or user doesn't exist
**Solution**: 
- Use: `test_registration@aeroguard.com` / `Test123!`
- Or register a new user first

### Error 3: "Cannot connect to server"
**Cause**: Backend not running or wrong URL
**Solution**: 
- Check backend is running on port 8000
- Check http://127.0.0.1:8000/docs works

### Error 4: "User account is inactive"
**Cause**: User's `is_active` is False
**Solution**: Check database, set `is_active = true`

---

## ✅ Quick Test

1. **Start backend** (Terminal 1)
2. **Start frontend** (Terminal 2)
3. **Open**: http://localhost:3000/login
4. **Login with**: `test_registration@aeroguard.com` / `Test123!`
5. **Should work!**

---

**Start both servers first, then try login!** 🚀

