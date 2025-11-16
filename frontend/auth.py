"""
Simple authentication module for Streamlit app
MVP version - just login/logout with bcrypt password hashing
Supports both Streamlit Secrets (production) and users.json (local dev)
"""
import streamlit as st
import bcrypt
import json
import os
from typing import Optional, Dict

# Path to users file (fallback for local development)
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")


def load_users() -> Dict:
    """
    Load users from Streamlit Secrets (primary) or users.json (fallback)

    Priority:
    1. st.secrets["users"] - for Streamlit Cloud deployment
    2. users.json file - for local development

    Returns:
        Dictionary of users with structure: {username: {password_hash, full_name, role, enabled}}
    """
    # Try loading from Streamlit Secrets first (production)
    try:
        if hasattr(st, 'secrets') and "users" in st.secrets:
            # Convert secrets to dict format
            users = {}
            for username in st.secrets["users"]:
                user_data = st.secrets["users"][username]
                users[username] = {
                    "password_hash": user_data.get("password_hash", ""),
                    "full_name": user_data.get("full_name", username),
                    "role": user_data.get("role", "viewer"),
                    "enabled": user_data.get("enabled", True)
                }
            if users:
                return users
    except Exception as e:
        # Secrets not available or error reading them - continue to file fallback
        pass

    # Fallback to users.json file (local development)
    if not os.path.exists(USERS_FILE):
        st.error(f"⚠️ No user configuration found!")
        st.info("**For Streamlit Cloud:** Configure users in Streamlit Secrets")
        st.info("**For Local Development:** Create a users.json file")
        st.markdown("See documentation for setup instructions.")
        return {}

    try:
        with open(USERS_FILE, 'r') as f:
            data = json.load(f)
            return data.get('users', {})
    except json.JSONDecodeError:
        st.error("Error loading users file - invalid JSON format")
        return {}
    except Exception as e:
        st.error(f"Error loading users: {str(e)}")
        return {}


def verify_password(username: str, password: str) -> bool:
    """
    Verify username and password

    Args:
        username: Username to check
        password: Password to verify

    Returns:
        True if credentials are valid, False otherwise
    """
    users = load_users()

    if not users:
        return False

    # Check if username exists
    if username not in users:
        return False

    user = users[username]

    # Check if account is enabled
    if not user.get("enabled", True):
        return False

    # Verify password against stored hash
    stored_hash = user["password_hash"]

    try:
        # bcrypt.checkpw expects bytes
        return bcrypt.checkpw(
            password.encode('utf-8'),
            stored_hash.encode('utf-8')
        )
    except Exception as e:
        st.error(f"Password verification error: {str(e)}")
        return False


def show_login_page():
    """Display the login form"""
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("## 🔐 Authentication Required")
        st.markdown("Please enter your credentials to access the application")
        st.markdown("---")

        # Create login form
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                key="login_username"
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password"
            )

            col_a, col_b, col_c = st.columns([1, 2, 1])
            with col_b:
                submit = st.form_submit_button(
                    "🔓 Login",
                    type="primary",
                    use_container_width=True
                )

            if submit:
                if not username or not password:
                    st.error("⚠️ Please enter both username and password")
                    return

                # Verify credentials
                if verify_password(username, password):
                    # Load user data
                    users = load_users()
                    user_data = users[username]

                    # Set session state
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_role = user_data.get("role", "viewer")
                    st.session_state.full_name = user_data.get("full_name", username)

                    st.success(f"✅ Welcome back, {st.session_state.full_name}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")

        # Footer
        st.markdown("---")
        st.caption("🔒 Secure authentication with bcrypt password hashing")


def check_authentication() -> bool:
    """
    Check if user is authenticated
    Shows login page if not authenticated

    Returns:
        True if authenticated, False otherwise
    """
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    # Check if authenticated
    if not st.session_state.authenticated:
        show_login_page()
        return False

    return True


def logout():
    """Clear session state and log out"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_role = None
    st.session_state.full_name = None


def show_logout_button():
    """Display logout button and user info in sidebar"""
    if st.session_state.get('authenticated', False):
        st.markdown("---")
        st.markdown("### 👤 User Info")
        st.markdown(f"**Name:** {st.session_state.get('full_name', 'Unknown')}")
        st.markdown(f"**Username:** {st.session_state.get('username', 'Unknown')}")
        st.markdown(f"**Role:** {st.session_state.get('user_role', 'viewer')}")

        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            logout()
            st.rerun()


def get_current_user() -> Optional[str]:
    """Get current logged in username"""
    return st.session_state.get('username')


def get_user_role() -> str:
    """Get current user's role"""
    return st.session_state.get('user_role', 'viewer')
