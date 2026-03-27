# 🔧 Fix Registration Error - Step by Step

## ✅ What I've Fixed

1. **Better Error Handling**: Backend now shows detailed error messages
2. **Frontend Error Display**: Frontend now shows the actual backend error message
3. **Database Check**: Verified database connection and users table exists

---

## 🔍 How to Find the Exact Error

### Step 1: Open Browser Developer Tools
1. Open http://localhost:3000/register
2. Press **F12** (or right-click → Inspect)
3. Click **"Console"** tab
4. Try to register again
5. **Look for red error messages** - copy them!

### Step 2: Check Network Request
1. In Developer Tools, click **"Network"** tab
2. Try to register again
3. Find the request: `POST http://127.0.0.1:8000/auth/register`
4. Click on it
5. Check:
   - **Status**: What status code? (400, 500, etc.)
   - **Response** tab: What error message?
   - **Request Payload**: Is data correct?

### Step 3: Check Backend Terminal
Look at the terminal where `uvicorn` is running.
- Do you see any error messages?
- What does it say when registration fails?

---

## 🧪 Test Registration Directly in Backend

1. **Open**: http://127.0.0.1:8000/docs
2. **Find**: `POST /auth/register`
3. **Click**: "Try it out"
4. **Fill in**:
   ```json
   {
     "email": "test@example.com",
     "password": "Test123!",
     "full_name": "Test User",
     "employee_id": "TEST001",
     "role": "aviator"
   }
   ```
5. **Click**: "Execute"
6. **What error do you see?**

---

## 🎯 Common Issues & Solutions

### Issue 1: Password Validation Failed
**Error**: "Password must contain at least one..."
**Solution**: 
- Use: `Test123!` (has uppercase, lowercase, number, special char)
- Minimum 8 characters

### Issue 2: Email Already Exists
**Error**: "Email already registered"
**Solution**: Use a different email (e.g., `test2@example.com`)

### Issue 3: Employee ID Already Exists
**Error**: "Employee ID already registered"
**Solution**: Use a different employee ID (e.g., `TEST002`)

### Issue 4: Database Error
**Error**: "Registration failed: ..."
**Solution**: 
- Check if PostgreSQL is running
- Check database connection in `database.py`

### Issue 5: CORS Error
**Error**: "CORS policy" or "Network Error"
**Solution**: 
- Backend CORS is configured
- Make sure backend is running on port 8000
- Make sure frontend is running on port 3000

---

## ✅ Quick Test

Try registering with this **exact** data:
- **Email**: `test123@aeroguard.com`
- **Password**: `Test123!` (must have uppercase, lowercase, number, special char)
- **Full Name**: `Test User`
- **Employee ID**: `TEST123`
- **Role**: `aviator` (from dropdown)

---

## 📋 What to Tell Me

After trying to register, tell me:
1. **What error message appears on the page?**
2. **What error appears in browser console?** (F12 → Console)
3. **What error appears in Network tab?** (F12 → Network → Click request → Response)
4. **What error appears in backend terminal?**

This will help me fix it quickly! 🚀

