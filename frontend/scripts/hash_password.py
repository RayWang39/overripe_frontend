#!/usr/bin/env python3
"""
Simple password hashing utility
Usage: python hash_password.py [password]
If no password provided, will prompt for input
"""
import sys
import bcrypt
import getpass


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')


def main():
    print("=" * 60)
    print("Password Hashing Utility (bcrypt)")
    print("=" * 60)
    print()

    # Get password from command line arg or prompt
    if len(sys.argv) > 1:
        password = sys.argv[1]
        print(f"Hashing password: {password}")
    else:
        password = getpass.getpass("Enter password to hash: ")
        confirm = getpass.getpass("Confirm password: ")

        if password != confirm:
            print("ERROR: Passwords don't match!")
            sys.exit(1)

    # Generate hash
    password_hash = hash_password(password)

    print()
    print("=" * 60)
    print("Password Hash Generated Successfully!")
    print("=" * 60)
    print()
    print("Copy this hash to your users.json file:")
    print()
    print(password_hash)
    print()
    print("Example users.json entry:")
    print("=" * 60)
    print(f'''{{
  "users": {{
    "your_username": {{
      "password_hash": "{password_hash}",
      "full_name": "Your Full Name",
      "role": "admin",
      "enabled": true
    }}
  }}
}}''')
    print("=" * 60)


if __name__ == "__main__":
    main()
