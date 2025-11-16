# 🚀 Authentication Quick Start

## Test Login Credentials

```
Username: admin
Password: admin123
```

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

**Change default passwords before production!**

See `AUTH_README.md` for complete documentation.
