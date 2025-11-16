# Authentication System - User Guide

## Overview

This Streamlit application now has a simple, secure authentication system with username/password login.

## Quick Start

### Setting Up Users

The system requires you to create a `frontend/users.json` file with your user accounts.

**User Roles:**

| Role | Access Level |
|------|--------------|
| `admin` | Full access to all features |
| `viewer` | Read-only access |
| `analyst` | Can run queries and view dashboards |

**⚠️ IMPORTANT: Always use strong, unique passwords!**

## How to Use

### 1. Login

1. Start the Streamlit app: `streamlit run frontend/app.py`
2. You'll see a login page
3. Enter your username and password
4. Click "Login"

### 2. Logout

- Click the **"🚪 Logout"** button in the sidebar (available on all pages)
- You'll be redirected back to the login page

### 3. Navigate Between Pages

- Once logged in, your session persists across all pages
- Navigate using the sidebar menu
- No need to login again on different pages

## User Management

### Adding New Users

Use the password hashing utility to create new users:

```bash
cd frontend/scripts
python hash_password.py
```

This will:
1. Prompt you to enter a password
2. Generate a bcrypt hash
3. Show you the JSON structure to add to `users.json`

### Example: Adding a New User

1. Generate password hash:
```bash
cd frontend/scripts
python hash_password.py
# Enter password: mySecurePassword123
# Confirm password: mySecurePassword123
```

2. Copy the generated hash

3. Edit `frontend/users.json`:
```json
{
  "users": {
    "admin": {
      "password_hash": "$2b$12$...",
      "full_name": "Administrator",
      "role": "admin",
      "enabled": true
    },
    "newuser": {
      "password_hash": "$2b$12$PASTE_YOUR_HASH_HERE",
      "full_name": "New User Name",
      "role": "viewer",
      "enabled": true
    }
  }
}
```

### Changing Passwords

1. Generate a new password hash using the script above
2. Replace the `password_hash` value in `users.json` for that user
3. Save the file
4. User can now login with the new password

### Disabling Users

To temporarily disable a user without deleting them:

```json
{
  "users": {
    "username": {
      "password_hash": "$2b$12$...",
      "full_name": "User Name",
      "role": "viewer",
      "enabled": false  // Set to false to disable
    }
  }
}
```

### Removing Users

Simply delete the user's entire entry from `users.json`.

## User Roles

The system supports 3 roles:

### `admin`
- Full access to all features
- Can run queries
- Can use method chain translator
- Can execute Python code
- Can view all dashboards

### `analyst`
- Can run queries
- Can use method chain translator
- Can view dashboards
- **Cannot** execute Python code (for security)

### `viewer`
- Can view dashboards only
- **Cannot** run queries
- **Cannot** use translator
- **Cannot** execute Python code

## Security Features

✅ **Password Hashing**: Passwords are hashed with bcrypt (12 rounds)
✅ **No Plaintext**: Passwords are never stored in plaintext
✅ **Session-Based**: Uses Streamlit's session state
✅ **Gitignored**: `users.json` is excluded from version control

## File Structure

```
frontend/
├── auth.py                    # Authentication module
├── users.json                 # User credentials (gitignored)
├── users.example.json         # Template file (safe to commit)
├── scripts/
│   └── hash_password.py       # Password hashing utility
└── AUTH_README.md            # This file
```

## Important Security Notes

### 🔒 Production Deployment

Before deploying to production:

1. **Change all default passwords**
2. **Use strong passwords** (12+ characters, mixed case, numbers, symbols)
3. **Never commit `users.json`** to git (already in .gitignore)
4. **Backup `users.json`** securely

### 📁 File Permissions

On production servers, restrict file access:
```bash
chmod 600 frontend/users.json  # Only owner can read/write
```

### 🌐 Streamlit Cloud Deployment

For Streamlit Cloud, use secrets management instead of `users.json`:

1. Go to your app settings on Streamlit Cloud
2. Add secrets in TOML format:

```toml
[auth.users.admin]
password_hash = "$2b$12$..."
full_name = "Administrator"
role = "admin"
enabled = true

[auth.users.demo]
password_hash = "$2b$12$..."
full_name = "Demo User"
role = "viewer"
enabled = true
```

3. Modify `auth.py` to read from `st.secrets` when `users.json` doesn't exist

## Troubleshooting

### "Users file not found"

**Solution**: Copy `users.example.json` to `users.json`
```bash
cp frontend/users.example.json frontend/users.json
```

### "Invalid username or password"

**Possible causes**:
- Wrong username/password
- User account disabled (`enabled: false`)
- Corrupted password hash

### "Module 'bcrypt' not found"

**Solution**: Install bcrypt
```bash
pip install bcrypt
```

### Session not persisting across pages

**Solution**: This is normal Streamlit behavior. Session state should persist. If not:
- Check if you're using the same browser/tab
- Clear browser cache and try again
- Make sure `check_authentication()` is called on every page

## Testing the Authentication

### Test Scenarios

1. **Valid Login**
   - Username: `admin`, Password: `admin123`
   - Should show welcome message and redirect to app

2. **Invalid Login**
   - Try wrong password
   - Should show error message

3. **Logout**
   - Click logout button
   - Should return to login page

4. **Page Navigation**
   - Login once
   - Navigate between pages
   - Should remain logged in

5. **Disabled Account**
   - Set a user's `enabled` to `false`
   - Try to login
   - Should be denied access

## FAQ

**Q: Where are passwords stored?**
A: In `frontend/users.json`, hashed with bcrypt. Never in plaintext.

**Q: Can I use this with a database?**
A: This MVP uses JSON file storage. For 100+ users, consider upgrading to Flask with PostgreSQL.

**Q: How do I reset a forgotten password?**
A: As admin, generate a new hash and update `users.json` manually.

**Q: Is this production-ready?**
A: Yes, for small teams (5-10 users). For larger deployments, consider enterprise authentication (OAuth, LDAP).

**Q: Can multiple users login simultaneously?**
A: Yes, each user gets their own session.

## Support

For issues or questions:
1. Check this README
2. Review `frontend/auth.py` for implementation details
3. See `users.example.json` for file structure reference
