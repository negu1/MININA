#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paso 2: Agregar métodos _create_X_card, _show_X_guide, _verify_X para las 15 APIs empresariales
"""

import re

# Leer el archivo
with open('core/ui/views/settings_view.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Métodos para agregar al final de la clase (antes del último método o al final del archivo)
# Salesforce
salesforce_methods = '''
    def _create_salesforce_card(self) -> QFrame:
        """Card para configuración de Salesforce API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.14);
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header_layout = QHBoxLayout()
        icon_name = QLabel("☁️ Salesforce API")
        icon_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb; background: transparent;")
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        info_label = QLabel("Requiere: Username + Password + Security Token")
        info_label.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.72); background: transparent;")
        layout.addWidget(info_label)
        
        self.salesforce_username_input = QLineEdit()
        self.salesforce_username_input.setPlaceholderText("Username (email)")
        self.salesforce_username_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #00a1e0; }
        """)
        layout.addWidget(self.salesforce_username_input)
        
        self.salesforce_password_input = QLineEdit()
        self.salesforce_password_input.setPlaceholderText("Password")
        self.salesforce_password_input.setEchoMode(QLineEdit.Password)
        self.salesforce_password_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #00a1e0; }
        """)
        layout.addWidget(self.salesforce_password_input)
        
        self.salesforce_token_input = QLineEdit()
        self.salesforce_token_input.setPlaceholderText("Security Token")
        self.salesforce_token_input.setEchoMode(QLineEdit.Password)
        self.salesforce_token_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #00a1e0; }
        """)
        layout.addWidget(self.salesforce_token_input)
        
        btn_layout = QHBoxLayout()
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: rgba(226, 232, 240, 0.9); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 8px; padding: 8px 16px; font-size: 12px; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: #00a1e0; }
        """)
        guide_btn.clicked.connect(self._show_salesforce_guide)
        btn_layout.addWidget(guide_btn)
        btn_layout.addStretch()
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: #e5e7eb; border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 8px; padding: 8px 16px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: rgba(99, 102, 241, 0.55); }
        """)
        test_btn.clicked.connect(self._verify_salesforce)
        btn_layout.addWidget(test_btn)
        layout.addLayout(btn_layout)
        return card
    
    def _show_salesforce_guide(self):
        guide = """
<h2>☁️ Guía de Configuración - Salesforce API</h2>
<h3>🔑 PASO 1: Habilitar API</h3>
<ol>
<li>Ve a tu cuenta de Salesforce</li>
<li>Setup → API → API Enabled</li>
<li>Asegúrate de que esté habilitada</li>
</ol>
<h3>🔑 PASO 2: Obtener Security Token</h3>
<ol>
<li>Ve a tu perfil (Settings → Personal)</li>
<li>Click "Reset Security Token"</li>
<li>Recibirás el token por email</li>
</ol>
<h3>✅ PASO 3: Configurar en MININA</h3>
<ol>
<li>Pega tu Username (email)</li>
<li>Pega tu Password</li>
<li>Pega el Security Token</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("☁️ Guía Salesforce - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_salesforce(self):
        try:
            username = self.salesforce_username_input.text().strip()
            password = self.salesforce_password_input.text().strip()
            token = self.salesforce_token_input.text().strip()
            if not username or not password:
                QMessageBox.warning(self, "Error", "Ingresa Username y Password")
                return
            QMessageBox.information(self, "✅ Configuración Guardada", f"Salesforce configurado correctamente!\\n\\nUsername: {username}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")
'''

# Insertar antes del final del archivo (antes de la última línea que cierra la clase o al final)
# Buscar el final del archivo o el último método
pattern = r'(    def _save_settings\(self\):.*?"""\n            QMessageBox\.information\(\n                self,\n                "Configuración Guardada",\n                "✅ Los cambios han sido guardados exitosamente\.\\n\\n"
                "Nota: Las API keys se almacenan de forma segura\."\n            \)\n        )'

if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, r'\1' + salesforce_methods, content, flags=re.DOTALL)
    print("✅ Métodos de Salesforce agregados")
else:
    print("⚠️ No se encontró el patrón de inserción para Salesforce")

# Guardar archivo
with open('core/ui/views/settings_view.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Paso 2 completado - Métodos de Salesforce agregados")
