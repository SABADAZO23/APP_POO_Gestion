import streamlit as st

def employee_dashboard(user, store_mgmt):
    st.title("👨‍💼 Dashboard del Empleado")

    store = store_mgmt.get_store_by_id(user['store_id'])
    if store:
        st.subheader(f"Tienda: {store['name']}")
        st.write("Bienvenido a tu panel de trabajo")

        if user['role'] == 'manager':
            st.write("**Funciones de Gerente:**")
            st.button("Ver Reportes de Ventas")
            st.button("Gestionar Inventario")
            st.button("Ver Horarios")

        elif user['role'] == 'employee':
            st.write("**Funciones de Empleado:**")
            st.button("Registrar Venta")
            st.button("Consultar Inventario")
            st.button("Ver Mi Horario")

        elif user['role'] == 'cashier':
            st.write("**Funciones de Cajero:**")
            st.button("Punto de Venta")
            st.button("Corte de Caja")
