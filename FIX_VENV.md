# Fix Virtual Environment - Step by Step

## Your venv is corrupted. Let's fix it!

### Option 1: Recreate Virtual Environment (Recommended)

**Run these commands in your VS Code terminal:**

1. **Deactivate current venv:**
   ```powershell
   deactivate
   ```

2. **Delete the old venv:**
   ```powershell
   Remove-Item -Recurse -Force venv
   ```

3. **Create a new venv:**
   ```powershell
   python -m venv venv
   ```

4. **Activate the new venv:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

5. **Upgrade pip:**
   ```powershell
   python -m pip install --upgrade pip
   ```

6. **Install all dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

   OR install manually:
   ```powershell
   pip install uvicorn[standard] fastapi sqlalchemy psycopg2-binary python-dotenv pydantic passlib[bcrypt] python-jose[cryptography] python-multipart email-validator
   ```

7. **Start the server:**
   ```powershell
   python -m uvicorn main:app --reload
   ```

---

### Option 2: Use Global Python (Quick Fix)

Since packages are already installed globally, you can use that:

1. **Deactivate venv:**
   ```powershell
   deactivate
   ```

2. **Start server with global Python:**
   ```powershell
   python -m uvicorn main:app --reload
   ```

---

## I recommend Option 1 for a clean setup!

