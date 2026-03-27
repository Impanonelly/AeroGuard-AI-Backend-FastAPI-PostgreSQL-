# 📊 How to Check Registration in pgAdmin

## ⚠️ IMPORTANT: Registration Uses `users` Table, NOT `pilots`!

When you register a new user through the frontend, the data is saved in the **`users`** table, not the `pilots` table.

---

## 🎯 Step-by-Step: Check Registration in pgAdmin

### Step 1: Open pgAdmin and Navigate to Database
1. **Open pgAdmin**
2. **Expand**: `Servers` → `PostgreSQL 16` → `Databases` → `aeroguard_db`
3. **Expand**: `Schemas` → `public` → `Tables`

### Step 2: Find the `users` Table
1. **Look for**: `users` table (NOT `pilots`)
2. You should see:
   - `pilots` table (for health assessments)
   - `users` table (for user accounts) ← **This is where registration saves!**

### Step 3: View Registration Data
1. **Right-click** on `users` table
2. **Select**: `View/Edit Data` → `All Rows`
3. **You should see columns**:
   - `id` - Primary key (auto-increment)
   - `email` - User's email address
   - `password_hash` - Encrypted password (you won't see the actual password)
   - `full_name` - User's full name
   - `employee_id` - Employee ID
   - `role` - User role (aviator, supervisor, safety_officer, administrator)
   - `license_number` - Optional license number
   - `certification_details` - Optional certification details
   - `is_active` - Account status (true/false)
   - `mfa_enabled` - Multi-factor authentication status
   - `created_at` - Registration timestamp
   - `updated_at` - Last update timestamp

### Step 4: Verify After Registration
1. **Register a new user** in the frontend (http://localhost:3000/register)
2. **Go back to pgAdmin**
3. **Right-click** `users` table → `Refresh` (or press F5)
4. **You should see** the new user with:
   - Your email address
   - Your full name
   - Your employee ID
   - Your role
   - `is_active = true`
   - `created_at` = current timestamp

---

## 🔍 Quick SQL Query

You can also run this SQL query in pgAdmin's Query Tool:

```sql
-- View all registered users
SELECT 
    id,
    email,
    full_name,
    employee_id,
    role,
    is_active,
    created_at
FROM users
ORDER BY created_at DESC;
```

This shows all users, newest first.

---

## 📋 Table Comparison

| Table | Purpose | When Data is Saved |
|-------|---------|-------------------|
| **`users`** | User accounts & authentication | When user registers or admin creates account |
| **`pilots`** | Pilot health & assessment data | When health assessment is submitted |

**Registration → `users` table** ✅  
**Health Assessment → `pilots` table** ✅

---

## 🧪 Test Registration

1. **Run the test script**:
   ```powershell
   cd "E:\Study material\Sem 6\Final Year Project\aeroguard_backend"
   python test_registration_db.py
   ```

2. **Check pgAdmin**:
   - Open `users` table
   - You should see a test user: `test_registration@aeroguard.com`

3. **Try registering in frontend**:
   - Go to http://localhost:3000/register
   - Fill in the form
   - Submit
   - Check `users` table in pgAdmin
   - You should see your new user!

---

## ✅ Verification Checklist

- [ ] `users` table exists in pgAdmin
- [ ] Can see table structure (columns)
- [ ] Test registration script runs successfully
- [ ] Can see test user in `users` table
- [ ] Frontend registration saves to `users` table
- [ ] New users appear with correct data

---

## 🐛 Troubleshooting

### Issue: `users` table doesn't exist
**Solution**: Run this command:
```powershell
cd "E:\Study material\Sem 6\Final Year Project\aeroguard_backend"
python -c "from database import engine; from models import Base, User; Base.metadata.create_all(bind=engine); print('✅ users table created!')"
```

### Issue: No data appears after registration
**Check**:
1. Is backend server running? (port 8000)
2. Check backend terminal for errors
3. Check browser console (F12) for errors
4. Verify database connection in `database.py`

---

**Remember: Registration saves to `users` table, not `pilots`!** 🎯

