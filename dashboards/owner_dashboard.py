import streamlit as st

from modules.autenticacion import AuthenticationSystem
from modules.products import ProductManagement
from modules.theme import save_theme, load_theme, apply_theme


def owner_dashboard(user, store_mgmt, employee_mgmt):
    st.title("🏪 Dashboard del Propietario")

    stores = store_mgmt.get_store_by_owner(user['email'])
    if not stores:
        st.warning("No tienes tiendas registradas")
        return

    store = stores[0]
    store_id = user['store_id']

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Resumen", "👥 Gestión de Empleados", "⚙️ Configuración", "🛒 Productos"])

    with tab1:
        st.subheader(f"Tienda: {store['name']}")
        st.write(f"**Dirección:** {store['address']}")
        st.write(f"**Estado:** {'Activa' if store.get('active', True) else 'Inactiva'}")

        employees = employee_mgmt.get_employees_by_store(store_id)
        st.metric("Total Empleados", len(employees))

    with tab2:
        st.subheader("Gestión de Empleados")
        # Formulario para crear usuario + empleado (con contraseña opcional)
        with st.form("create_user_employee_form"):
            st.write("Crear Usuario y Agregar como Empleado")
            cu_email = st.text_input("Email del usuario")
            cu_password = st.text_input("Password (opcional)", type="password")
            cu_role = st.selectbox("Rol", ["manager", "employee", "cashier"]) 
            if st.form_submit_button("Crear y Agregar"):
                if cu_email:
                    ok = employee_mgmt.add_employee(cu_email, cu_role, store_id, user['email'], password=cu_password if cu_password else None)
                    if ok:
                        st.success(f"Usuario/Empleado {cu_email} creado agregado exitosamente")
                    else:
                        st.error("Error creando usuario/empleado")
                else:
                    st.error("Por favor ingresa un email")

        st.subheader("Lista de Empleados")
        employees = employee_mgmt.get_employees_by_store(store_id)
        if employees:
            for emp in employees:
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"**Email:** {emp['email']}")
                with col2:
                    st.write(f"**Rol:** {emp['role']}")
                with col3:
                    status = "Activo" if emp.get('active', True) else "Inactivo"
                    st.write(f"**{status}**")
                st.divider()
        else:
            st.info("No hay empleados registrados")

    with tab3:
        st.subheader("Configuración de la Tienda")
        st.write("Configuraciones adicionales de la tienda...")
        # Theme settings
        st.markdown("---")
        st.subheader("Apariencia y Tema")
        theme = load_theme(store_id) or {}
        current_palette = theme.get('palette', [])
        current_dark = theme.get('dark_mode', False)
        st.write("Configura hasta 6 colores para la paleta, sube un logo y elige modo oscuro/claro.")
        num_colors = st.selectbox("Número de colores en la paleta", options=[1,2,3,4,5,6], index=min(len(current_palette)-1,5) if current_palette else 2)
        palette = []
        for i in range(int(num_colors)):
            default = current_palette[i] if i < len(current_palette) else ("#%06x" % (0x100000 + i * 10000))[1:]
            col = st.color_picker(f"Color {i+1}", value=current_palette[i] if i < len(current_palette) else "#%06x" % (0x808080 + i*0x10101))
            palette.append(col)

        logo_file = st.file_uploader("Subir logo (PNG/JPG)", type=["png", "jpg", "jpeg"])
        dark_mode = st.checkbox("Modo oscuro", value=current_dark)

        if st.button("Guardar Apariencia"):
            logo_bytes = None
            if logo_file is not None:
                logo_bytes = logo_file.read()
            ok = save_theme(store_id, palette, dark_mode, logo_bytes)
            if ok:
                st.success("Tema guardado")
                # Aplicar inmediatamente
                theme_saved = load_theme(store_id)
                apply_theme(theme_saved)
            else:
                st.error("Error guardando tema")

        # Mostrar preview del logo si existe
        if 'theme_logo' in st.session_state:
            st.image(st.session_state['theme_logo'], use_column_width=False, caption="Logo actual", output_format='PNG', clamp=False)
    # Productos: crear/listar y ajustar stock
    with tab4:
        st.subheader("Gestión de Productos y Stock")
        prod_mgmt = ProductManagement()

        with st.form("add_product_form"):
            st.write("Agregar Nuevo Producto")
            p_sku = st.text_input("SKU")
            p_name = st.text_input("Nombre")
            p_price = st.number_input("Precio", min_value=0.0, format="%.2f")
            p_description = st.text_area("Descripción")
            p_initial = st.number_input("Cantidad inicial", min_value=0, value=0)

            if st.form_submit_button("Crear Producto"):
                if p_name and p_sku:
                    product_id = prod_mgmt.create_product(store_id, p_sku, p_name, p_price, p_description, int(p_initial))
                    if product_id:
                        st.success(f"Producto '{p_name}' creado (id: {product_id})")
                    else:
                        st.error("Error al crear producto")
                else:
                    st.error("SKU y Nombre son obligatorios")

        # Edición de producto
        st.markdown("---")
        st.subheader("Editar Producto")
        prods = prod_mgmt.get_products_by_store(store_id)
        if prods:
            prod_options = {f"{p.get('name')} ({p.get('sku')})": p.get('id') for p in prods}
            sel = st.selectbox("Selecciona producto", options=list(prod_options.keys()))
            sel_id = prod_options.get(sel)
            if sel_id:
                p_data = prod_mgmt.get_product_by_id(sel_id)
                if p_data:
                    with st.form("edit_product_form"):
                        e_name = st.text_input("Nombre", value=p_data.get('name'))
                        e_sku = st.text_input("SKU", value=p_data.get('sku'))
                        e_price = st.number_input("Precio", min_value=0.0, value=float(p_data.get('price', 0.0)), format="%.2f")
                        e_desc = st.text_area("Descripción", value=p_data.get('description', ''))
                        if st.form_submit_button("Guardar Cambios"):
                            updates = {'name': e_name, 'sku': e_sku, 'price': float(e_price), 'description': e_desc}
                            if prod_mgmt.update_product(sel_id, updates):
                                st.success("Producto actualizado")
                            else:
                                st.error("Error actualizando producto")
        else:
            st.info("No hay productos para editar")

        st.markdown("---")
        st.subheader("Inventario actual")
        inv = prod_mgmt.get_inventory_for_store(store_id)
        if inv:
            for item in inv:
                cols = st.columns([3, 1, 1, 2])
                with cols[0]:
                    st.write(f"**{item.get('name') or item.get('sku')}**")
                    st.write(f"SKU: {item.get('sku')}")
                with cols[1]:
                    st.write(f"Cantidad: {item.get('quantity')}")
                with cols[2]:
                    change = st.number_input(f"Ajuste {item.get('product_id')}", value=0, step=1, key=f"chg_{item.get('product_id')}")
                with cols[3]:
                    if st.button("Aplicar", key=f"btn_{item.get('product_id')}"):
                        if change != 0:
                            ok = prod_mgmt.adjust_stock(item['product_id'], store_id, change, 'manual_adjust', user['email'])
                            if ok:
                                st.success("Ajuste aplicado")
                            else:
                                st.error("Error aplicando ajuste")
                        else:
                            st.info("Ingrese una cantidad distinta de 0 para ajustar")
                st.divider()
        else:
            st.info("No hay inventario registrado para esta tienda")

        st.markdown("---")
        st.subheader("Historial de Movimientos")
        movements = prod_mgmt.get_movements_by_store(store_id, limit=100)
        if movements:
            for m in movements:
                t = m.get('timestamp')
                # timestamp may be a Firestore sentinel; pretty-print if possible
                time_str = str(t) if t is not None else "-"
                prod_label = m.get('product_name') or m.get('product_id') or '—'
                st.write(f"Producto: **{prod_label}** — Cambio: {m.get('change')} — Usuario: {m.get('user')} — {m.get('reason')} — {time_str}")
                st.divider()
        else:
            st.info("No hay movimientos registrados")
