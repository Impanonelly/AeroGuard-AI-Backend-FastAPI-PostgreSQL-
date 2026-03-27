# 🔗 Connect Frontend & Backend - Complete Guide

## ✅ Good News!
Your frontend is **already set up** and ready to connect! I just need to help you start it.

---

## 🚀 Step-by-Step Setup

### Step 1: Make Sure Backend is Running

**In VS Code Terminal (Backend directory):**
```powershell
# Make sure you're in backend directory
cd "E:\Study material\Sem 6\Final Year Project\aeroguard_backend"

# Start backend server
C:\Python314\python.exe -m uvicorn main:app --reload
```

**You should see:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Keep this terminal open!** The backend must stay running.

---

### Step 2: Install Frontend Dependencies (First Time Only)

**Open a NEW terminal in VS Code** (you can have multiple terminals open):

1. **Click the "+" button** next to the terminal tab to open a new terminal
2. **Navigate to frontend directory:**
   ```powershell
   cd "E:\Study material\Sem 6\Final Year Project\aeroguard_frontend"
   ```

3. **Install dependencies:**
   ```powershell
   npm install
   ```

   **This will take a few minutes** - it's installing all React packages.

---

### Step 3: Start Frontend Server

**In the same frontend terminal**, run:
```powershell
npm run dev
```

**You should see:**
```
  VITE v7.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

---

### Step 4: Open in Browser

1. **Open your browser**
2. **Go to**: http://localhost:3000
3. **You should see**: The AeroGuard AI login page!

---

## 🧪 Test the Connection

### Test 1: Register a User
1. Click "Register here" link
2. Fill in the form:
   - Email: `test@aeroguard.com`
   - Password: `TestPass123!`
   - Full Name: `Test User`
   - Employee ID: `EMP001`
   - Role: `Aviator`
3. Click "Register"
4. **Expected**: Redirects to login page

### Test 2: Login
1. Use the email and password you just registered
2. Click "Login"
3. **Expected**: Redirects to dashboard showing your user info

### Test 3: Dashboard
1. You should see your user information
2. You should see "Welcome, Test User (aviator)"
3. Click "Logout" - should redirect to login

---

## ✅ What's Already Configured

- ✅ **CORS** - Backend allows frontend connections
- ✅ **API Client** - Axios configured to connect to backend
- ✅ **Authentication** - Login/Register working
- ✅ **Token Storage** - JWT tokens stored in localStorage
- ✅ **Protected Routes** - Dashboard requires login
- ✅ **Tailwind CSS** - Styling ready
- ✅ **React Router** - Navigation working

---

## 📋 Frontend Dependencies (Already in package.json)

All these are configured:
- ✅ React 19.2.0
- ✅ React Router DOM 6.26.0
- ✅ Axios 1.7.7
- ✅ React Hook Form 7.53.0
- ✅ Tailwind CSS 3.4.19
- ✅ Vite 7.3.1

---

## 🔧 Troubleshooting

### Issue: npm install fails
**Solution**:
- Make sure Node.js is installed: `node --version`
- If not installed, download from: https://nodejs.org/
- After installing Node.js, run `npm install` again

### Issue: Port 3000 already in use
**Solution**:
- Close other applications using port 3000
- Or change port in `vite.config.js`

### Issue: Cannot connect to backend
**Solution**:
- Make sure backend is running on port 8000
- Check backend terminal for errors
- Verify CORS is configured in `main.py`

### Issue: CORS error in browser
**Solution**:
- Backend CORS is already configured
- Make sure backend is running
- Check browser console for specific error

---

## 🎯 Quick Start Commands

**Terminal 1 (Backend):**
```powershell
cd "E:\Study material\Sem 6\Final Year Project\aeroguard_backend"
C:\Python314\python.exe -m uvicorn main:app --reload
```

**Terminal 2 (Frontend):**
```powershell
cd "E:\Study material\Sem 6\Final Year Project\aeroguard_frontend"
npm install  # First time only
npm run dev
```

---

## 📁 Project Structure

```
Final Year Project/
├── aeroguard_backend/     # Backend (FastAPI)
│   └── Running on: http://127.0.0.1:8000
│
└── aeroguard_frontend/    # Frontend (React)
    └── Running on: http://localhost:3000
```

---

## ✅ Success Checklist

- [ ] Backend running on port 8000
- [ ] Frontend dependencies installed (`npm install`)
- [ ] Frontend running on port 3000 (`npm run dev`)
- [ ] Can open http://localhost:3000 in browser
- [ ] Can register a new user
- [ ] Can login with registered user
- [ ] Can see dashboard after login
- [ ] Can logout

---

## 🚀 Next Steps After Connection Works

Once frontend and backend are connected:
1. ✅ Test all authentication flows
2. ✅ Build more dashboard features
3. ✅ Add assessment submission
4. ✅ Add pilot management
5. ✅ Continue with Phase 3 & 4 development

---

**Follow the steps above and let me know if everything works!** 🎉

