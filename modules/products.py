import logging
from typing import Optional, Dict, Any

from firebase_admin import firestore
from firebase_config import get_firestore_client

logger = logging.getLogger(__name__)

db = get_firestore_client()


class ProductManagement:
    """Gestión básica de productos, inventario y movimientos.

    Colecciones usadas:
    - products: metadatos del producto
    - inventory: entradas por store_id/product_id con cantidad
    - movements: historial de cambios de stock
    """

    def create_product(self, store_id: str, sku: str, name: str, price: float, description: str = "", initial_quantity: int = 0) -> Optional[str]:
        try:
            product_data = {
                'store_id': store_id,
                'sku': sku,
                'name': name,
                'price': float(price),
                'description': description,
                'created_at': firestore.SERVER_TIMESTAMP,
                'active': True,
            }
            prod_ref = db.collection('products').add(product_data)
            product_id = prod_ref[1].id

            # Si se indica cantidad inicial, crear/actualizar inventario y movimiento
            if initial_quantity and int(initial_quantity) != 0:
                self._set_inventory(product_id, store_id, int(initial_quantity))
                self._add_movement(product_id, store_id, int(initial_quantity), 'initial', 'system')

            return product_id
        except Exception as e:
            logger.exception("Error creando producto: %s", e)
            return None

    def get_products_by_store(self, store_id: str) -> list:
        try:
            products_ref = db.collection('products').where('store_id', '==', store_id).get()
            return [{**p.to_dict(), 'id': p.id} for p in products_ref]
        except Exception as e:
            logger.exception("Error obteniendo productos: %s", e)
            return []

    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        try:
            p = db.collection('products').document(product_id).get()
            if p.exists:
                data = p.to_dict()
                data['id'] = p.id
                return data
            return None
        except Exception:
            logger.exception("Error obteniendo producto por id")
            return None

    def update_product(self, product_id: str, updates: Dict[str, Any]) -> bool:
        try:
            db.collection('products').document(product_id).update(updates)
            return True
        except Exception:
            logger.exception("Error actualizando producto")
            return False

    def _set_inventory(self, product_id: str, store_id: str, quantity: int):
        # Guardar/actualizar el documento inventory identificado por product_id+store_id
        try:
            q = db.collection('inventory').where('product_id', '==', product_id).where('store_id', '==', store_id).limit(1).get()
            if q:
                db.collection('inventory').document(q[0].id).update({'quantity': quantity})
            else:
                inv = {
                    'product_id': product_id,
                    'store_id': store_id,
                    'quantity': quantity,
                    'updated_at': firestore.SERVER_TIMESTAMP,
                }
                db.collection('inventory').add(inv)
        except Exception:
            logger.exception("Error seteando inventario")

    def adjust_stock(self, product_id: str, store_id: str, change: int, reason: str, user_email: str) -> bool:
        """Ajusta el stock (positivo o negativo) y registra un movimiento."""
        try:
            # obtener inventario actual
            q = db.collection('inventory').where('product_id', '==', product_id).where('store_id', '==', store_id).limit(1).get()
            if q:
                doc = q[0]
                current = doc.to_dict().get('quantity', 0)
                new_qty = int(current) + int(change)
                db.collection('inventory').document(doc.id).update({'quantity': new_qty, 'updated_at': firestore.SERVER_TIMESTAMP})
            else:
                # crear con la cantidad indicada
                db.collection('inventory').add({
                    'product_id': product_id,
                    'store_id': store_id,
                    'quantity': int(change),
                    'updated_at': firestore.SERVER_TIMESTAMP,
                })

            # Registrar movimiento
            self._add_movement(product_id, store_id, int(change), reason, user_email)
            return True
        except Exception:
            logger.exception("Error ajustando stock")
            return False

    def _add_movement(self, product_id: str, store_id: str, change: int, reason: str, user_email: str):
        try:
            mov = {
                'product_id': product_id,
                'store_id': store_id,
                'change': int(change),
                'reason': reason,
                'user': user_email,
                'timestamp': firestore.SERVER_TIMESTAMP,
            }
            db.collection('movements').add(mov)
        except Exception:
            logger.exception("Error registrando movimiento")

    def get_movements_by_store(self, store_id: str, limit: int = 50) -> list:
        try:
            mov_ref = db.collection('movements').where('store_id', '==', store_id).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit).get()
            results = []
            for m in mov_ref:
                d = m.to_dict()
                # attach product name if available
                prod = db.collection('products').document(d.get('product_id')).get() if d.get('product_id') else None
                prod_name = prod.to_dict().get('name') if prod and prod.exists else None
                results.append({
                    'id': m.id,
                    'product_id': d.get('product_id'),
                    'product_name': prod_name,
                    'change': d.get('change'),
                    'reason': d.get('reason'),
                    'user': d.get('user'),
                    'timestamp': d.get('timestamp'),
                })
            return results
        except Exception as exc:
            # Manejar errores de índice de Firestore (requiere index compuesto)
            try:
                from google.api_core.exceptions import FailedPrecondition
            except Exception:
                FailedPrecondition = None

            if FailedPrecondition and isinstance(exc, FailedPrecondition):
                logger.error("Firestore requiere un índice compuesto para esta consulta: %s", exc)
                # Intentar lectura alternativa: movimientos como subcolección bajo stores/{store_id}/movements
                try:
                    alt_ref = db.collection('stores').document(store_id).collection('movements').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit).get()
                    results = []
                    for m in alt_ref:
                        d = m.to_dict()
                        prod = db.collection('products').document(d.get('product_id')).get() if d.get('product_id') else None
                        prod_name = prod.to_dict().get('name') if prod and prod.exists else None
                        results.append({
                            'id': m.id,
                            'product_id': d.get('product_id'),
                            'product_name': prod_name,
                            'change': d.get('change'),
                            'reason': d.get('reason'),
                            'user': d.get('user'),
                            'timestamp': d.get('timestamp'),
                        })
                    if results:
                        logger.info("Movements leídos desde subcolección stores/%s/movements como fallback", store_id)
                        return results
                except Exception:
                    logger.exception("Error intentando leer movimientos desde subcolección como fallback")

                # Devolver lista vacía para evitar crash en la UI; el mensaje detallado se mostrará en logs.
                return []

            logger.exception("Error obteniendo movimientos: %s", exc)
            return []

    def get_inventory_for_store(self, store_id: str) -> list:
        try:
            inv_ref = db.collection('inventory').where('store_id', '==', store_id).get()
            results = []
            for inv in inv_ref:
                d = inv.to_dict()
                # obtener producto
                prod = db.collection('products').document(d['product_id']).get()
                prod_data = prod.to_dict() if prod.exists else {}
                results.append({
                    'product_id': d['product_id'],
                    'sku': prod_data.get('sku'),
                    'name': prod_data.get('name'),
                    'quantity': d.get('quantity', 0),
                })
            return results
        except Exception:
            logger.exception("Error obteniendo inventario")
            return []
