# 🔍 Debug Registration Issue

## Steps to Find the Problem

### 1. Check Browser Console
1. Open browser (http://localhost:3000)
2. Press `F12` to open Developer Tools
3. Click **"Console"** tab
4. Try to register again
5. **Look for red error messages**
6. **Copy the error message** and tell me what it says

### 2. Check Network Tab
1. In Developer Tools, click **"Network"** tab
2. Try to register again
3. Find the request to `/auth/register`
4. Click on it
5. Check:
   - **Status Code** (should be 200 or 201 for success)
   - **Response** tab - what error message is shown?
   - **Request Payload** - is the data being sent correctly?

### 3. Check Backend Terminal
Look at the backend terminal where `uvicorn` is running.
- Do you see any error messages?
- What does it say when you try to register?

### 4. Test Backend Directly
Open: http://127.0.0.1:8000/docs

1. Click on **POST /auth/register**
2. Click **"Try it out"**
3. Fill in the form:
   ```json
   {
     "email": "test@example.com",
     "password": "Test123!",
     "full_name": "Test User",
     "employee_id": "TEST001",
     "role": "aviator"
   }
   ```
4. Click **"Execute"**
5. **What error do you see?**

---

## Common Issues

### Issue 1: Password Too Weak
**Error**: "Password must contain at least one..."
**Solution**: Use a password like: `Test123!` (has uppercase, lowercase, number, special char)

### Issue 2: Email Already Exists
**Error**: "Email already registered"
**Solution**: Use a different email address

### Issue 3: Employee ID Already Exists
**Error**: "Employee ID already registered"
**Solution**: Use a different employee ID

### Issue 4: Database Connection Error
**Error**: "Registration failed: ..."
**Solution**: Check if PostgreSQL is running

### Issue 5: CORS Error
**Error**: "CORS policy" or "Network Error"
**Solution**: Backend CORS is configured, but check if backend is running on port 8000

---

## Quick Test

Try registering with this exact data:
- **Email**: `test123@aeroguard.com`
- **Password**: `Test123!`
- **Full Name**: `Test User`
- **Employee ID**: `TEST123`
- **Role**: `aviator`

**Tell me what error message you see!**

