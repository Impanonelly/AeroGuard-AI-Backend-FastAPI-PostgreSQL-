# Step 4: Test Protected Endpoint - Detailed Guide

## 🎯 What You Need
- Your `access_token` from Step 3 (login)
- Browser open to http://localhost:8000/docs

---

## 📝 Step-by-Step Instructions

### Step 4.1: Find the Authorize Button
1. Look at the **top right** of the Swagger UI page
2. You'll see a **lock icon** 🔒 with text "Authorize" next to it
3. Click on it

### Step 4.2: Enter Your Token
1. A popup window will appear
2. You'll see a field labeled **"Value"** or **"Bearer"**
3. In that field, paste your `access_token` from Step 3
   - **Important**: Don't add "Bearer" or quotes - just paste the token directly
   - The token looks like: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (long string)

### Step 4.3: Authorize
1. Click the **"Authorize"** button in the popup
2. You should see a checkmark ✅ or "Authorized" message
3. Click **"Close"** to close the popup

### Step 4.4: Test the Endpoint
1. Scroll down to find **`GET /auth/me`**
2. Click on it to expand
3. Click the **"Try it out"** button
4. Click the **"Execute"** button (blue button)
5. **Expected Result**: 
   - Status: `200 OK`
   - Response body shows your user information (email, name, role, etc.)

---

## 🔍 Visual Guide

```
┌─────────────────────────────────────────┐
│  Swagger UI Page                        │
│                                         │
│  [🔒 Authorize]  ← Click this button   │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  Popup Window                     │ │
│  │                                   │ │
│  │  Value: [paste token here]       │ │
│  │                                   │ │
│  │  [Authorize] [Close]             │ │
│  └───────────────────────────────────┘ │
│                                         │
│  GET /auth/me                           │
│  [Try it out] ← Click this              │
│  [Execute] ← Then click this            │
└─────────────────────────────────────────┘
```

---

## ❓ Troubleshooting

### Problem: Can't find Authorize button
**Solution**: 
- Look at the very top of the page, right side
- It might say "Authorize" or show a lock icon 🔒
- If you still can't find it, try refreshing the page

### Problem: Token doesn't work
**Solution**:
1. Make sure you copied the **entire** token (it's very long)
2. Make sure there are **no spaces** before or after
3. Don't include quotes or "Bearer"
4. Try logging in again to get a fresh token

### Problem: Getting 401 Unauthorized
**Solution**:
1. Make sure you clicked "Authorize" after pasting the token
2. Make sure you clicked "Close" after authorizing
3. Try the token again - tokens expire after 15 minutes
4. Get a new token by logging in again

### Problem: Getting 403 Forbidden
**Solution**:
- This means your user doesn't have permission
- This is normal for some endpoints
- Try with a different role (supervisor or administrator)

---

## ✅ Success Looks Like This

When it works, you'll see:

```json
{
  "id": 1,
  "email": "test@aeroguard.com",
  "full_name": "Test User",
  "employee_id": "EMP001",
  "role": "aviator",
  "is_active": true,
  "mfa_enabled": false,
  "created_at": "2026-03-05T..."
}
```

---

## 🎯 Quick Checklist

- [ ] Found the Authorize button (lock icon)
- [ ] Clicked it
- [ ] Pasted access_token in the Value field
- [ ] Clicked "Authorize" button
- [ ] Clicked "Close"
- [ ] Found GET /auth/me endpoint
- [ ] Clicked "Try it out"
- [ ] Clicked "Execute"
- [ ] Got 200 OK response with user data

---

**If you're still stuck, tell me:**
- What do you see when you click the Authorize button?
- What error message do you get (if any)?
- Can you see the GET /auth/me endpoint?

