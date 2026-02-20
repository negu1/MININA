"""
MININA v3.0 - Stripe Skill
Skill para operaciones con Stripe
"""

from core.api.stripe_manager import stripe_manager


def execute(context: dict) -> dict:
    """
    Operaciones con Stripe
    
    Args:
        context: {
            "action": str,           # create_payment, create_customer, get_customer, create_product, list_payments, refund
            "amount": int,         # Monto en centavos (ej: 1000 = $10.00)
            "currency": str,        # Moneda (default: usd)
            "customer_id": str,     # ID del cliente
            "email": str,          # Email del cliente (para create_customer)
            "name": str,          # Nombre del cliente (para create_customer)
            "description": str,   # Descripción
            "product_name": str,  # Nombre del producto
            "price": int,         # Precio en centavos (para create_product)
            "charge_id": str,     # ID del cargo (para refund)
            "limit": int          # Límite de resultados (default 10)
        }
    
    Returns:
        {
            "success": bool,
            "result": dict,
            "error": str (si falla)
        }
    """
    try:
        action = context.get("action", "")
        
        # Verificar que Stripe está configurado
        if not stripe_manager.is_configured():
            return {
                "success": False,
                "error": "Stripe no configurado. Ve a Configuración → Stripe para agregar tu API Key."
            }
        
        if action == "create_payment":
            amount = context.get("amount", 0)
            currency = context.get("currency", "usd")
            customer_id = context.get("customer_id")
            description = context.get("description")
            
            if not amount or amount <= 0:
                return {"success": False, "error": "Falta amount (en centavos, ej: 1000 = $10.00)"}
            
            return stripe_manager.create_payment_intent(amount, currency, customer_id, description)
        
        elif action == "create_customer":
            email = context.get("email", "")
            name = context.get("name")
            description = context.get("description")
            
            if not email:
                return {"success": False, "error": "Falta email"}
            
            return stripe_manager.create_customer(email, name, description)
        
        elif action == "get_customer":
            customer_id = context.get("customer_id", "")
            if not customer_id:
                return {"success": False, "error": "Falta customer_id"}
            return stripe_manager.get_customer(customer_id)
        
        elif action == "create_product":
            name = context.get("product_name", "")
            description = context.get("description")
            price = context.get("price")
            currency = context.get("currency", "usd")
            
            if not name:
                return {"success": False, "error": "Falta product_name"}
            
            return stripe_manager.create_product(name, description, price, currency)
        
        elif action == "list_payments":
            limit = context.get("limit", 10)
            return stripe_manager.list_payments(limit)
        
        elif action == "refund":
            charge_id = context.get("charge_id", "")
            amount = context.get("amount")  # Opcional: monto parcial
            
            if not charge_id:
                return {"success": False, "error": "Falta charge_id"}
            
            return stripe_manager.refund_charge(charge_id, amount)
        
        else:
            return {
                "success": False,
                "error": f"Acción '{action}' no válida. Usa: create_payment, create_customer, get_customer, create_product, list_payments, refund"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error en skill de Stripe: {str(e)}"
        }
