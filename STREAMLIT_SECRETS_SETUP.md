# Streamlit Secrets Setup Guide

## Quick Fix for Your Authentication Issue

Your auth system now supports **both** Streamlit Secrets (production) and users.json (local dev).

## For Streamlit Cloud (PRODUCTION)

### Step 1: Go to Your App Settings
1. Open your Streamlit Cloud dashboard
2. Navigate to your deployed app
3. Click **Settings** (gear icon)
4. Click **Secrets** in the left sidebar

### Step 2: Copy the Secrets Configuration
Copy the entire content from `frontend/secrets.example.toml` and paste it into the Secrets editor:

```toml
[users.admin]
password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TT.vjV4zvJZEp.xrO7eZJ5gsxeOm"
full_name = "Administrator"
role = "admin"
enabled = true

[users.demo]
password_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
full_name = "Demo User"
role = "viewer"
enabled = true
```

### Step 3: Test Your Login

**Test Credentials:**
- Username: `admin` / Password: `admin123`
- Username: `demo` / Password: `demo123`

⚠️ **IMPORTANT:** These are test credentials. Change them before going to production!

### Step 4: Change Passwords (Recommended)

To create your own passwords:

1. **Locally**, run the password hasher:
   ```bash
   cd frontend/scripts
   python hash_password.py
   ```

2. Enter your desired password when prompted

3. Copy the generated hash (starts with `$2b$12$...`)

4. Update the Streamlit Secrets in your dashboard with the new hash

5. Click **Save**

Your app will automatically restart with the new credentials.

---

## For Local Development

### Option 1: Copy Example File
```bash
cd frontend
cp users.example.json users.json
```

Now you can login locally with:
- Username: `admin` / Password: `admin123`
- Username: `demo` / Password: `demo123`

### Option 2: Create Your Own
```bash
cd frontend/scripts
python hash_password.py  # Generate a hash

# Then edit frontend/users.json with your hash
```

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
- Change default passwords before production use
- Password hashes are safe to commit in documentation examples
- Backup your production secrets separately (not in git)

---

## Troubleshooting

**"No user configuration found" error:**
- On Streamlit Cloud: Add secrets via Settings > Secrets
- Locally: Create `frontend/users.json` from the example file

**"Invalid username or password":**
- Verify you're using the correct credentials
- Check that `enabled = true` in the user config
- Ensure password hash is correctly formatted (starts with `$2b$12$`)

**Password hash generation fails:**
- Ensure bcrypt is installed: `pip install bcrypt`
- Use Python 3.8+ (bcrypt requires modern Python)
