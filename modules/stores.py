import streamlit as st
from firebase_admin import firestore
from firebase_config import get_firestore_client

db = get_firestore_client()


class StoreManagement:
    def __init__(self):
        # Exponer el cliente Firestore en la instancia para usos como `store_mgmt.db`
        self.db = db

    def create_store(self, store_name, store_address, owner_email):
        try:
            store_data = {
                'name': store_name,
                'address': store_address,
                'owner_email': owner_email,
                'created_at': firestore.SERVER_TIMESTAMP,
                'active': True
            }
            store_ref = self.db.collection('stores').add(store_data)
            return store_ref[1].id  # Retorna el ID del documento
        except Exception as e:
            st.error(f"Error creando tienda: {e}")
            return None

    def get_store_by_owner(self, owner_email):
        try:
            stores_ref = self.db.collection('stores').where('owner_email', '==', owner_email).get()
            return [store.to_dict() for store in stores_ref]
        except Exception as e:
            st.error(f"Error obteniendo tiendas: {e}")
            return []

    def get_store_by_id(self, store_id):
        try:
            store_ref = self.db.collection('stores').document(store_id).get()
            return store_ref.to_dict() if store_ref.exists else None
        except Exception as e:
            st.error(f"Error obteniendo tienda: {e}")
            return None
