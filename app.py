import streamlit as st
import firebase_admin
from firebase_config import initialize_firebase

from modules.authentication import AuthenticationSystem
from modules.stores import StoreManagement
from modules.employees import EmployeeManagement
from dashboards.owner_dashboard import owner_dashboard
from dashboards.employee_dashboard import employee_dashboard
from modules.theme import load_theme, apply_theme

# Inicializar Firebase
if not firebase_admin._apps:
    initialize_firebase()

def main():
    st.set_page_config(page_title="Sistema de Gestión de Tiendas", layout="wide")

    auth_system = AuthenticationSystem()
    store_mgmt = StoreManagement()
    employee_mgmt = EmployeeManagement()

    if 'user' not in st.session_state:
        st.session_state.user = None

    # Login / Registro
    if not st.session_state.user:
        # Landing / Login styled according to theme
        st.markdown("<div class='landing-container'>", unsafe_allow_html=True)

        # Top-left logo if available
        logo_src = st.session_state.get('theme_logo') if 'theme_logo' in st.session_state else None
        if logo_src:
            st.markdown(f"<img src='{logo_src}' class='top-left-logo' />", unsafe_allow_html=True)

        st.markdown("<div class='landing-hero'>", unsafe_allow_html=True)
        if logo_src:
            st.image(logo_src, width=160)
        st.markdown("<h1>Tu inventario siempre a la mano</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:var(--color2)'>Gestiona tu stock y tu equipo en un solo lugar</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Entrar button shows login form
        if 'show_login' not in st.session_state:
            st.session_state.show_login = False

        if not st.session_state.show_login:
            if st.button("Entrar"):
                st.session_state.show_login = True
                st.experimental_rerun()
        else:
            # Login / Registro inline
            st.markdown("<div class='login-card'>", unsafe_allow_html=True)
            st.subheader("Iniciar Sesión")
            email = st.text_input("Correo:", key="login_email")
            password = st.text_input("Contraseña:", type="password", key="login_password")

            if st.button("Iniciar Sesión"):
                if auth_system.login(email, password):
                    st.session_state.user = auth_system.current_user
                    st.success("¡Login exitoso!")
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")

            st.markdown("<div style='text-align:center;margin-top:8px'>No tienes una cuenta? <a href='#'>Regístrate</a></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Registration as before
        st.markdown("<hr/>", unsafe_allow_html=True)
        st.subheader("Registrar Nueva Tienda")
        owner_email = st.text_input("Email del propietario", key="reg_email")
        owner_password = st.text_input("Password", type="password", key="reg_password")
        store_name = st.text_input("Nombre de la tienda")
        store_address = st.text_input("Dirección de la tienda")

        if st.button("Registrar Tienda"):
            if owner_email and owner_password and store_name:
                if auth_system.register_user(owner_email, owner_password, 'owner'):
                    store_id = store_mgmt.create_store(store_name, store_address, owner_email)
                    if store_id:
                        user_ref = store_mgmt.db.collection('users').where('email', '==', owner_email).limit(1).get()
                        if user_ref:
                            store_mgmt.db.collection('users').document(user_ref[0].id).update({'store_id': store_id})
                        st.success("¡Tienda registrada exitosamente! Ahora puedes iniciar sesión.")
                    else:
                        st.error("Error creando la tienda")
                else:
                    st.error("Error registrando el usuario")
            else:
                st.error("Por favor completa todos los campos")

        st.markdown("</div>", unsafe_allow_html=True)

    # Dashboard
    else:
        user = st.session_state.user
        # Aplicar tema personalizado de la tienda (si existe)
        try:
            theme = None
            if user.get('store_id'):
                theme = load_theme(user.get('store_id'))
            apply_theme(theme)
        except Exception:
            pass
        st.sidebar.title(f"👋 Hola, {user['email']}")
        st.sidebar.write(f"Rol: {user['role']}")

        if st.sidebar.button("Cerrar Sesión"):
            auth_system.logout()
            st.rerun()

        if user['role'] == 'owner':
            owner_dashboard(user, store_mgmt, employee_mgmt)
        elif user['role'] in ['manager', 'employee', 'cashier']:
            employee_dashboard(user, store_mgmt)
        else:
            st.warning("Rol no reconocido")

if __name__ == "__main__":
    main()
