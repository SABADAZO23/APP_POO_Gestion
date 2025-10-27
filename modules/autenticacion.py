import streamlit as st
from firebase_admin import firestore
from firebase_config import get_firestore_client

db = get_firestore_client()

class AuthenticationSystem:
    def __init__(self):
        self.current_user = None

    def login(self, email, password):
        """Simula un login básico (sin Auth REST API)."""
        try:
            user_ref = db.collection('users').where('email', '==', email).limit(1).get()

            if user_ref:
                user_data = user_ref[0].to_dict()
                if user_data.get('password') == password:  # En producción usar hash
                    self.current_user = {
                        'uid': user_ref[0].id,
                        'email': email,
                        'role': user_data.get('role', 'user'),
                        'store_id': user_data.get('store_id')
                    }
                    return True
            return False
        except Exception as e:
            st.error(f"Error en login: {e}")
            return False

    def register_user(self, email, password, role, store_id=None):
        try:
            user_data = {
                'email': email,
                'password': password,  # En producción: hashear
                'role': role,
                'store_id': store_id,
                'created_at': firestore.SERVER_TIMESTAMP
            }
            db.collection('users').add(user_data)
            return True
        except Exception as e:
            st.error(f"Error registrando usuario: {e}")
            return False

    def logout(self):
        self.current_user = None
        st.session_state.clear()
