# 🚀 Authentication Quick Start

## Setup Login Credentials

First, create your `frontend/users.json` file with secure passwords:

```bash
# Generate a password hash
python frontend/scripts/hash_password.py
# Enter your desired password, copy the hash
```

Then create `frontend/users.json` (see example below in "Add New User" section).

## Start the App

```bash
streamlit run frontend/app.py
```

Open: http://localhost:8501

## Add New User

```bash
cd frontend/scripts
python hash_password.py
# Enter password, copy the hash
```

Edit `frontend/users.json`:
```json
{
  "users": {
    "myuser": {
      "password_hash": "PASTE_HASH_HERE",
      "full_name": "My Name",
      "role": "admin",
      "enabled": true
    }
  }
}
```

## Roles

- **admin**: Full access
- **analyst**: Queries + dashboards
- **viewer**: Read-only

## ⚠️ IMPORTANT

- **Always use strong, unique passwords**
- **Never commit `users.json` to git** (it's gitignored)
- **Use a password manager** to store your credentials

See `AUTH_README.md` for complete documentation.
