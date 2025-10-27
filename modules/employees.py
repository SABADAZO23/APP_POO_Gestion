import streamlit as st
from firebase_admin import firestore
from firebase_config import get_firestore_client
from modules.authentication import AuthenticationSystem

db = get_firestore_client()

class EmployeeManagement:
    def add_employee(self, email, role, store_id, added_by, password: str | None = None):
        """Agrega un empleado y crea el usuario si no existe.

        password: si se proporciona, se usará para crear el usuario;
        de lo contrario se crea con una contraseña temporal.
        """
        try:
            employee_data = {
                'email': email,
                'role': role,
                'store_id': store_id,
                'added_by': added_by,
                'added_at': firestore.SERVER_TIMESTAMP,
                'active': True
            }

            # Verificar si el usuario existe
            user_ref = db.collection('users').where('email', '==', email).limit(1).get()

            if user_ref:
                # Actualizar usuario existente
                db.collection('users').document(user_ref[0].id).update({
                    'store_id': store_id,
                    'role': role
                })
            else:
                # Crear nuevo usuario
                auth_system = AuthenticationSystem()
                passwd = password if password else "temp_password"
                auth_system.register_user(email, passwd, role, store_id)

            # Agregar a la colección de empleados
            db.collection('employees').add(employee_data)
            return True
        except Exception as e:
            st.error(f"Error agregando empleado: {e}")
            return False

    def get_employees_by_store(self, store_id):
        try:
            employees_ref = db.collection('employees').where('store_id', '==', store_id).get()
            return [emp.to_dict() for emp in employees_ref]
        except Exception as e:
            st.error(f"Error obteniendo empleados: {e}")
            return []
