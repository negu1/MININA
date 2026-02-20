"""
MININA v3.0 - Email Skill
Skill para enviar emails usando el EmailManager
"""

from core.api.email_manager import email_manager


def execute(context: dict) -> dict:
    """
    Enviar email usando cuenta configurada
    
    Args:
        context: {
            "account_name": str,      # Nombre de cuenta configurada (default: "default")
            "to": str,                # Email destinatario
            "subject": str,           # Asunto
            "body": str,              # Cuerpo del mensaje
            "html": bool,             # True para HTML, False para texto plano
            "cc": list,               # Lista de CC (opcional)
            "bcc": list               # Lista de BCC (opcional)
        }
    
    Returns:
        {
            "success": bool,
            "message": str,
            "error": str (si falla)
        }
    """
    try:
        # Extraer parámetros
        account_name = context.get("account_name", "default")
        to = context.get("to", "")
        subject = context.get("subject", "")
        body = context.get("body", "")
        html = context.get("html", False)
        cc = context.get("cc", [])
        bcc = context.get("bcc", [])
        
        # Validaciones
        if not to:
            return {
                "success": False,
                "error": "Falta email destinatario (parámetro 'to')"
            }
        
        if not subject:
            return {
                "success": False,
                "error": "Falta asunto (parámetro 'subject')"
            }
        
        if not body:
            return {
                "success": False,
                "error": "Falta cuerpo del mensaje (parámetro 'body')"
            }
        
        # Verificar que existe la cuenta
        account = email_manager.get_account(account_name)
        if not account:
            available = list(email_manager.accounts.keys())
            return {
                "success": False,
                "error": f"Cuenta '{account_name}' no encontrada. Cuentas disponibles: {available}"
            }
        
        # Enviar email
        result = email_manager.send_email(
            account_name=account_name,
            to=to,
            subject=subject,
            body=body,
            html=html,
            cc=cc,
            bcc=bcc
        )
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error en skill de email: {str(e)}"
        }
