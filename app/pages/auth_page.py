import streamlit as st
from app.auth import signup, login


def render_auth_page():
    _, center, _ = st.columns([1, 3, 1])
    with center:
        st.markdown("""
            <div style="text-align:center; margin-top:2rem; margin-bottom:0.5rem;">
                <div class="auth-title">OptionViz</div>
                <div class="auth-subtitle">Options Strategy Builder & Visualizer</div>
            </div>
        """, unsafe_allow_html=True)

        tab_login, tab_signup = st.tabs(["Log In", "Sign Up"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Log In", use_container_width=True)

                if submitted:
                    if not email or not password:
                        st.error("Please enter your email and password.")
                    else:
                        user, error = login(email, password)
                        if error:
                            st.error(error)
                        else:
                            st.session_state.user = {
                                "id": user["id"],
                                "email": user["email"],
                                "is_verified": True,
                                "guest": False,
                            }
                            st.rerun()

        with tab_signup:
            with st.form("signup_form"):
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("Password", type="password", help="Min 8 chars, 1 uppercase, 1 lowercase, 1 number")
                confirm = st.text_input("Confirm Password", type="password")
                submitted = st.form_submit_button("Sign Up", use_container_width=True)

                if submitted:
                    if not email or not password or not confirm:
                        st.error("Please fill in all fields.")
                    elif password != confirm:
                        st.error("Passwords do not match.")
                    else:
                        user, error = signup(email, password)
                        if user is None:
                            st.error(error)
                        else:
                            st.session_state.user = {
                                "id": user["id"],
                                "email": user["email"],
                                "is_verified": True,
                                "guest": False,
                            }
                            st.success("Account created!")
                            st.rerun()

        st.markdown("---")
        if st.button("Continue as Guest", use_container_width=True, key="guest_btn"):
            st.session_state.user = {
                "id": None,
                "email": "Guest",
                "guest": True,
            }
            st.rerun()
        st.caption("Browse freely without an account. Sign in anytime to save strategies and track trades.")


def _is_guest():
    user = st.session_state.get("user")
    return user is not None and user.get("guest", False)


def render_user_sidebar():
    user = st.session_state.get("user")
    if not user:
        return

    with st.sidebar:
        st.markdown("---")
        if user.get("guest"):
            st.markdown('<span class="user-badge">Guest</span>', unsafe_allow_html=True)
            if st.button("Sign In", key="signin_btn"):
                del st.session_state.user
                st.rerun()
        else:
            st.markdown(f'<span class="user-badge">{user["email"]}</span>', unsafe_allow_html=True)
            if st.button("Log Out", key="logout_btn"):
                del st.session_state.user
                st.rerun()
