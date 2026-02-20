"""
MININA v3.0 - Email Manager API
Configuración y operaciones SMTP/IMAP para skills de email
"""

import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from datetime import datetime


@dataclass
class EmailConfig:
    """Configuración de cuenta de email"""
    provider: str  # gmail, outlook, yahoo, custom
    smtp_server: str
    smtp_port: int
    imap_server: str
    imap_port: int
    username: str
    password: str
    use_ssl: bool = True
    display_name: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "password": "***"  # Nunca exponer password
        }


class EmailManager:
    """
    Manager de Email para MININA
    
    Soporta:
    - Gmail (SMTP: smtp.gmail.com:587, IMAP: imap.gmail.com:993)
    - Outlook/Hotmail (SMTP: smtp.office365.com:587, IMAP: outlook.office365.com:993)
    - Yahoo (SMTP: smtp.mail.yahoo.com:587, IMAP: imap.mail.yahoo.com:993)
    - Custom SMTP/IMAP
    """
    
    # Configuraciones predefinidas de proveedores
    PROVIDERS = {
        "gmail": {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "imap_server": "imap.gmail.com",
            "imap_port": 993,
            "use_ssl": True
        },
        "outlook": {
            "smtp_server": "smtp.office365.com",
            "smtp_port": 587,
            "imap_server": "outlook.office365.com",
            "imap_port": 993,
            "use_ssl": True
        },
        "yahoo": {
            "smtp_server": "smtp.mail.yahoo.com",
            "smtp_port": 587,
            "imap_server": "imap.mail.yahoo.com",
            "imap_port": 993,
            "use_ssl": True
        },
        "custom": {
            "smtp_server": "",
            "smtp_port": 587,
            "imap_server": "",
            "imap_port": 993,
            "use_ssl": True
        }
    }
    
    def __init__(self, config_path: str = "data/email_config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.accounts: Dict[str, EmailConfig] = {}
        self._load_accounts()
    
    def _load_accounts(self):
        """Cargar cuentas guardadas"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for acc_name, acc_data in data.get("accounts", {}).items():
                        self.accounts[acc_name] = EmailConfig(**acc_data)
            except Exception as e:
                print(f"Error cargando configuración email: {e}")
    
    def _save_accounts(self):
        """Guardar cuentas"""
        try:
            data = {
                "updated_at": datetime.now().isoformat(),
                "accounts": {}
            }
            for name, config in self.accounts.items():
                data["accounts"][name] = asdict(config)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuración email: {e}")
    
    def add_account(
        self,
        account_name: str,
        provider: str,
        username: str,
        password: str,
        display_name: str = "",
        custom_smtp_server: str = "",
        custom_smtp_port: int = 587,
        custom_imap_server: str = "",
        custom_imap_port: int = 993
    ) -> Dict[str, Any]:
        """Agregar cuenta de email"""
        
        if provider not in self.PROVIDERS:
            return {"success": False, "error": f"Proveedor '{provider}' no soportado"}
        
        provider_config = self.PROVIDERS[provider].copy()
        
        # Si es custom, usar servidores personalizados
        if provider == "custom":
            provider_config["smtp_server"] = custom_smtp_server
            provider_config["smtp_port"] = custom_smtp_port
            provider_config["imap_server"] = custom_imap_server
            provider_config["imap_port"] = custom_imap_port
        
        config = EmailConfig(
            provider=provider,
            display_name=display_name or username,
            username=username,
            password=password,
            **provider_config
        )
        
        self.accounts[account_name] = config
        self._save_accounts()
        
        return {
            "success": True,
            "message": f"Cuenta '{account_name}' agregada exitosamente",
            "account": config.to_dict()
        }
    
    def remove_account(self, account_name: str) -> Dict[str, Any]:
        """Eliminar cuenta"""
        if account_name not in self.accounts:
            return {"success": False, "error": f"Cuenta '{account_name}' no existe"}
        
        del self.accounts[account_name]
        self._save_accounts()
        
        return {"success": True, "message": f"Cuenta '{account_name}' eliminada"}
    
    def get_account(self, account_name: str) -> Optional[EmailConfig]:
        """Obtener configuración de cuenta"""
        return self.accounts.get(account_name)
    
    def list_accounts(self) -> List[Dict[str, Any]]:
        """Listar todas las cuentas"""
        return [
            {
                "name": name,
                **config.to_dict()
            }
            for name, config in self.accounts.items()
        ]
    
    def test_connection(self, account_name: str) -> Dict[str, Any]:
        """Probar conexión SMTP e IMAP"""
        config = self.get_account(account_name)
        if not config:
            return {"success": False, "error": f"Cuenta '{account_name}' no encontrada"}
        
        results = {
            "smtp": False,
            "imap": False,
            "errors": []
        }
        
        # Test SMTP
        try:
            if config.use_ssl:
                server = smtplib.SMTP(config.smtp_server, config.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(config.smtp_server, config.smtp_port)
            
            server.login(config.username, config.password)
            server.quit()
            results["smtp"] = True
        except Exception as e:
            results["errors"].append(f"SMTP: {str(e)}")
        
        # Test IMAP
        try:
            if config.use_ssl:
                mail = imaplib.IMAP4_SSL(config.imap_server, config.imap_port)
            else:
                mail = imaplib.IMAP4(config.imap_server, config.imap_port)
            
            mail.login(config.username, config.password)
            mail.select('inbox')
            mail.logout()
            results["imap"] = True
        except Exception as e:
            results["errors"].append(f"IMAP: {str(e)}")
        
        results["success"] = results["smtp"] and results["imap"]
        return results
    
    def send_email(
        self,
        account_name: str,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
        cc: List[str] = None,
        bcc: List[str] = None
    ) -> Dict[str, Any]:
        """Enviar email"""
        
        config = self.get_account(account_name)
        if not config:
            return {"success": False, "error": f"Cuenta '{account_name}' no encontrada"}
        
        try:
            msg = MIMEMultipart()
            msg['From'] = f"{config.display_name} <{config.username}>" if config.display_name else config.username
            msg['To'] = to
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)
            
            # Adjuntar cuerpo
            content_type = 'html' if html else 'plain'
            msg.attach(MIMEText(body, content_type, 'utf-8'))
            
            # Conectar y enviar
            if config.use_ssl:
                server = smtplib.SMTP(config.smtp_server, config.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(config.smtp_server, config.smtp_port)
            
            server.login(config.username, config.password)
            
            recipients = [to]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            server.send_message(msg, config.username, recipients)
            server.quit()
            
            return {
                "success": True,
                "message": f"Email enviado exitosamente a {to}",
                "account": account_name,
                "subject": subject
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error enviando email: {str(e)}"
            }
    
    def read_emails(
        self,
        account_name: str,
        folder: str = "inbox",
        limit: int = 10,
        unread_only: bool = False
    ) -> Dict[str, Any]:
        """Leer emails de bandeja de entrada"""
        
        config = self.get_account(account_name)
        if not config:
            return {"success": False, "error": f"Cuenta '{account_name}' no encontrada"}
        
        try:
            # Conectar a IMAP
            if config.use_ssl:
                mail = imaplib.IMAP4_SSL(config.imap_server, config.imap_port)
            else:
                mail = imaplib.IMAP4(config.imap_server, config.imap_port)
            
            mail.login(config.username, config.password)
            mail.select(folder)
            
            # Buscar emails
            search_criteria = 'UNSEEN' if unread_only else 'ALL'
            _, data = mail.search(None, search_criteria)
            
            email_ids = data[0].split()
            if limit:
                email_ids = email_ids[-limit:]
            
            emails = []
            for e_id in email_ids:
                _, msg_data = mail.fetch(e_id, '(RFC822)')
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Extraer información
                subject = msg['subject'] or "(Sin asunto)"
                from_addr = msg['from'] or "(Desconocido)"
                date = msg['date'] or ""
                
                # Extraer cuerpo
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                else:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                
                emails.append({
                    "id": e_id.decode(),
                    "subject": subject,
                    "from": from_addr,
                    "date": date,
                    "body": body[:500] + "..." if len(body) > 500 else body
                })
            
            mail.logout()
            
            return {
                "success": True,
                "account": account_name,
                "folder": folder,
                "count": len(emails),
                "emails": emails
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error leyendo emails: {str(e)}"
            }


# Singleton para uso global
email_manager = EmailManager()
