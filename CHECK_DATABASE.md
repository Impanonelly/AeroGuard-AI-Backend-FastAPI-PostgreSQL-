# ✅ Check Database in pgAdmin

## 🎯 Important: Registration Uses `users` Table, NOT `pilots` Table!

When you register a new user, the data is saved in the **`users`** table, not the `pilots` table.

---

## 📋 How to Check Registration in pgAdmin

### Step 1: Find the `users` Table
1. **Open pgAdmin**
2. **Navigate to**: 
   - `Servers` → `PostgreSQL 16` → `Databases` → `aeroguard_db` → `Schemas` → `public` → `Tables`
3. **Look for**: `users` table (NOT `pilots`)

### Step 2: View the `users` Table Data
1. **Right-click** on `users` table
2. **Select**: "View/Edit Data" → "All Rows"
3. **You should see columns**:
   - `id` (integer, primary key)
   - `email` (varchar)
   - `password_hash` (varchar - encrypted)
   - `full_name` (varchar)
   - `employee_id` (varchar)
   - `role` (varchar)
   - `license_number` (varchar, nullable)
   - `certification_details` (text, nullable)
   - `is_active` (boolean)
   - `mfa_enabled` (boolean)
   - `created_at` (timestamp)
   - `updated_at` (timestamp)

### Step 3: Verify Registration
After registering a new user:
1. **Refresh** the `users` table view (click refresh icon)
2. **You should see** the new user with:
   - Your email address
   - Your full name
   - Your employee ID
   - Your role (aviator, supervisor, etc.)
   - `is_active = true`
   - `created_at` timestamp

---

## 🔍 Quick SQL Query to Check Users

In pgAdmin, you can also run this SQL query:

```sql
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

This will show all registered users, newest first.

---

## ⚠️ If You Don't See the `users` Table

If the `users` table doesn't exist, run this Python command to create it:

```powershell
cd "E:\Study material\Sem 6\Final Year Project\aeroguard_backend"
python -c "from database import engine; from models import Base, User; Base.metadata.create_all(bind=engine); print('✅ users table created!')"
```

---

## 🧪 Test Registration and Verify

1. **Register a new user** in the frontend (http://localhost:3000/register)
2. **Open pgAdmin**
3. **Check the `users` table**
4. **You should see** the new user record!

---

## 📊 Table Structure Comparison

| Table | Purpose | Used For |
|-------|---------|----------|
| `users` | User accounts & authentication | Registration, Login, RBAC |
| `pilots` | Pilot assessment data | Health monitoring, risk assessment |

**Registration saves to `users` table!** ✅

