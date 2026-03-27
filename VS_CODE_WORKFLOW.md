# Working in VS Code - Step-by-Step Guide

## 🎯 How We'll Work Together

### Process:
1. **I create code** → Following your SRS requirements
2. **You test in VS Code** → Run, test, verify
3. **We fix issues** → If something doesn't work, tell me
4. **Move forward** → When it works, we continue

---

## 📁 VS Code Setup Checklist

### ✅ Current Setup (You Should Have):
- [x] VS Code installed
- [x] Python extension installed
- [x] PostgreSQL running
- [x] Virtual environment (venv) activated
- [x] Project folder open in VS Code

### 🔧 VS Code Extensions Recommended:
1. **Python** (Microsoft) - For Python support
2. **Pylance** - For type checking
3. **PostgreSQL** - For database management (optional)
4. **REST Client** - For testing APIs (optional)

---

## 🚀 Daily Workflow

### Step 1: Open VS Code
```bash
# Navigate to your project
cd "E:\Study material\Sem 6\Final Year Project\aeroguard_backend"

# Open in VS Code
code .
```

### Step 2: Activate Virtual Environment
In VS Code terminal (Ctrl + `):
```bash
# Windows
venv\Scripts\activate

# You should see (venv) in your terminal prompt
```

### Step 3: Install/Update Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables
Create/update `.env` file in root:
```env
DATABASE_URL=postgresql://postgres:impano12@127.0.0.1:5432/aeroguard_db
JWT_SECRET_KEY=your-super-secret-key-minimum-32-characters-change-this
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Step 5: Run the Server
```bash
uvicorn main:app --reload
```

### Step 6: Test in Browser
Open: `http://localhost:8000/docs`

---

## 🧪 Testing Workflow

### Test 1: Check Server is Running
```bash
# In terminal, you should see:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete.
```

### Test 2: Test API Endpoints
1. Open `http://localhost:8000/docs` in browser
2. Try endpoints:
   - `GET /` - Should return welcome message
   - `GET /health` - Should return {"status": "healthy"}
   - `POST /auth/register` - Register a user
   - `POST /auth/login` - Login and get tokens

### Test 3: Test with Different Roles
1. Register as "aviator"
2. Register as "supervisor"
3. Login with each
4. Test access to protected endpoints

---

## 🐛 Common Issues & Solutions

### Issue 1: Module Not Found
**Error**: `ModuleNotFoundError: No module named 'auth'`

**Solution**:
```bash
# Make sure you're in the project root directory
cd "E:\Study material\Sem 6\Final Year Project\aeroguard_backend"

# Check if auth folder exists
dir auth

# If missing, I'll create it for you
```

---

### Issue 2: Database Connection Error
**Error**: `sqlalchemy.exc.OperationalError: could not connect to server`

**Solution**:
1. Check PostgreSQL is running
2. Verify DATABASE_URL in `.env` is correct
3. Test connection:
```bash
psql -U postgres -d aeroguard_db
```

---

### Issue 3: Import Errors
**Error**: `ImportError: cannot import name 'User' from 'models'`

**Solution**:
1. Check `models.py` has User class
2. Restart VS Code
3. Restart the server

---

### Issue 4: JWT Token Invalid
**Error**: `401 Unauthorized`

**Solution**:
1. Check JWT_SECRET_KEY in `.env`
2. Make sure token hasn't expired (15 minutes)
3. Use refresh token to get new access token

---

## 📝 Code Organization in VS Code

### Recommended VS Code Workspace Structure:
```
aeroguard_backend/
├── .vscode/              # VS Code settings (optional)
│   └── settings.json
├── auth/                 # Authentication module
├── routers/              # API routes
├── models.py             # Database models
├── schemas/               # Pydantic schemas
├── main.py               # Main application
├── database.py           # Database config
└── requirements.txt      # Dependencies
```

---

## 🔍 VS Code Features to Use

### 1. Integrated Terminal
- **Open**: Ctrl + ` (backtick)
- **New Terminal**: Ctrl + Shift + `
- **Split Terminal**: Click split icon

### 2. Python Debugger
- Set breakpoints (click left of line number)
- Press F5 to start debugging
- Use Debug Console to inspect variables

### 3. Command Palette
- **Open**: Ctrl + Shift + P
- **Run Python**: Type "Python: Run Python File in Terminal"

### 4. Git Integration
- **View Changes**: Click Source Control icon (Ctrl + Shift + G)
- **Commit**: Write message, click ✓
- **Push**: Click sync icon

---

## 📋 Testing Checklist (After Each Change)

When I create new code, you should:

- [ ] **Check for errors**: Look at VS Code Problems panel (Ctrl + Shift + M)
- [ ] **Run server**: `uvicorn main:app --reload`
- [ ] **Check terminal**: No error messages
- [ ] **Test endpoint**: Use Swagger UI at `/docs`
- [ ] **Test with Postman/curl**: If needed
- [ ] **Check database**: Verify data is saved correctly
- [ ] **Test error cases**: Invalid input, missing data, etc.

---

## 🎯 Current Task: Complete Phase 2

### What I'm Creating Now:
1. `auth/permissions.py` - RBAC system
2. Update endpoints with permissions
3. Test authentication flow

### What You'll Do:
1. **Wait for me to finish** creating the code
2. **Install dependencies** if I add new ones
3. **Run the server**: `uvicorn main:app --reload`
4. **Test the endpoints** in Swagger UI
5. **Tell me if it works** or if there are errors

---

## 💡 Pro Tips

1. **Keep terminal open**: Always have terminal visible
2. **Use Swagger UI**: Easiest way to test APIs
3. **Check logs**: Watch terminal for error messages
4. **Save files**: VS Code auto-saves, but Ctrl+S is good habit
5. **Use Git**: Commit after each working feature

---

## 🚨 When Something Doesn't Work

1. **Check terminal** for error messages
2. **Copy the error** and tell me
3. **Check file exists** - Make sure I created it
4. **Restart server** - Sometimes fixes import issues
5. **Check .env file** - Make sure variables are set

---

## 📞 Communication

**Tell me:**
- ✅ "It works!" - When something is successful
- ❌ "I got this error: [error message]" - When something fails
- ❓ "I don't understand X" - When you need clarification
- 🎯 "Let's move to next task" - When ready to continue

---

**Ready to work?** I'll create the RBAC system now, then you test it in VS Code!

