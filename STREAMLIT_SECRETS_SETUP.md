# Streamlit Secrets Setup Guide

## Quick Fix for Your Authentication Issue

Your auth system now supports **both** Streamlit Secrets (production) and users.json (local dev).

## For Streamlit Cloud (PRODUCTION)

### Step 1: Go to Your App Settings
1. Open your Streamlit Cloud dashboard
2. Navigate to your deployed app
3. Click **Settings** (gear icon)
4. Click **Secrets** in the left sidebar

### Step 2: Generate Secure Passwords

1. **Locally**, run the password hasher:
   ```bash
   python frontend/scripts/hash_password.py
   ```

2. Enter your desired password when prompted

3. Copy the generated hash (starts with `$2b$12$...`)

4. Repeat for each user account you need

### Step 3: Configure Streamlit Secrets

Paste your user configuration into the Secrets editor in TOML format:

```toml
[users.admin]
password_hash = "YOUR_GENERATED_HASH_HERE"
full_name = "Administrator"
role = "admin"
enabled = true

[users.demo]
password_hash = "YOUR_GENERATED_HASH_HERE"
full_name = "Demo User"
role = "viewer"
enabled = true
```

Click **Save** and your app will automatically restart.

---

## For Local Development

### Create users.json File

1. Generate password hashes using the password hasher:
   ```bash
   python frontend/scripts/hash_password.py
   ```

2. Create `frontend/users.json` with your hashes:
   ```json
   {
     "users": {
       "admin": {
         "password_hash": "YOUR_GENERATED_HASH_HERE",
         "full_name": "Administrator",
         "role": "admin",
         "enabled": true
       },
       "demo": {
         "password_hash": "YOUR_GENERATED_HASH_HERE",
         "full_name": "Demo User",
         "role": "viewer",
         "enabled": true
       }
     }
   }
   ```

3. This file is gitignored and will never be committed to GitHub

---

## How It Works

The updated `auth.py` now checks in this order:

1. **First:** Tries to load from `st.secrets["users"]` (Streamlit Cloud)
2. **Fallback:** Tries to load from `users.json` file (local dev)
3. **Error:** Shows helpful message if neither is found

This means:
- ✅ On Streamlit Cloud: Uses Secrets (users.json not needed)
- ✅ Locally: Uses users.json file
- ✅ users.json stays gitignored (safe!)

---

## User Roles

- **admin**: Full access (queries, translator, Python code, dashboards)
- **analyst**: Queries, translator, dashboards (no Python code)
- **viewer**: Dashboards only (read-only)

---

## Security Notes

⚠️ **Important:**
- Never commit `users.json` to git (it's gitignored)
- Always use strong, unique passwords for production
- Password hashes are irreversible but should still be kept secure
- Backup your production secrets separately (not in git)
- Use a password manager to store your passwords

---

## Troubleshooting

**"No user configuration found" error:**
- On Streamlit Cloud: Add secrets via Settings > Secrets
- Locally: Create `frontend/users.json` with your password hashes

**"Invalid username or password":**
- Verify you're using the correct credentials
- Check that `enabled = true` in the user config
- Ensure password hash is correctly formatted (starts with `$2b$12$`)

**Password hash generation fails:**
- Ensure bcrypt is installed: `pip install bcrypt`
- Use Python 3.8+ (bcrypt requires modern Python)
