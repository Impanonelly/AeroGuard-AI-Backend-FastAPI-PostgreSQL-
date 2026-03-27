# 🚀 Start Both Servers - Login Will Work!

## ✅ Everything is Ready!

- ✅ Password verification: Working
- ✅ JWT tokens: Working  
- ✅ User in database: Found
- ✅ Login code: Correct

**You just need to start both servers!**

---

## 🎯 Step-by-Step: Start Servers

### Terminal 1: Start Backend

1. **Open VS Code**
2. **Open Terminal** (Terminal → New Terminal, or `` Ctrl + ` ``)
3. **Run these commands:**
   ```powershell
   cd "E:\Study material\Sem 6\Final Year Project\aeroguard_backend"
   C:\Python314\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```

4. **Wait for:**
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000
   INFO:     Application startup complete.
   ```

5. **✅ Backend is running! Keep this terminal open!**

---

### Terminal 2: Start Frontend

1. **Open a NEW terminal** (Click "+" button next to terminal tab)
2. **Run these commands:**
   ```powershell
   cd "E:\Study material\Sem 6\Final Year Project\aeroguard_frontend"
   npm run dev
   ```

3. **Wait for:**
   ```
   VITE v7.x.x  ready in xxx ms
   ➜  Local:   http://localhost:3000/
   ```

4. **✅ Frontend is running! Keep this terminal open!**

---

## 🧪 Test Login

### Test Credentials:
- **Email**: `test_registration@aeroguard.com`
- **Password**: `Test123!`

### Steps:
1. **Open browser**: http://localhost:3000/login
2. **Enter email**: `test_registration@aeroguard.com`
3. **Enter password**: `Test123!`
4. **Click**: "Login"
5. **✅ Should redirect to dashboard!**

---

## ✅ Success Checklist

- [ ] Backend terminal shows "Application startup complete"
- [ ] Frontend terminal shows "Local: http://localhost:3000/"
- [ ] Can access http://127.0.0.1:8000/docs (Swagger UI)
- [ ] Can access http://localhost:3000 (Login page)
- [ ] Login works with test credentials
- [ ] Redirects to dashboard after login

---

## 🐛 If Login Still Doesn't Work

### Check Browser Console (F12):
1. **Press F12** in browser
2. **Click "Console" tab**
3. **Try login**
4. **Look for red errors**
5. **Tell me what error you see**

### Check Network Tab:
1. **Press F12** → **Network tab**
2. **Try login**
3. **Find**: `POST http://127.0.0.1:8000/auth/login`
4. **Click it** → **Check "Response" tab**
5. **What error message?**

---

## 📋 Important Notes

- **Keep both terminals open!** Closing them stops the servers
- **Backend must be on port 8000**
- **Frontend must be on port 3000**
- **Both must run at the same time**

---

**Start both servers now, then try login!** 🚀
