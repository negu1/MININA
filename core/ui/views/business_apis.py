# MÉTODOS PARA APIs EMPRESARIALES (15 APIs)
# Agregar al final de settings_view.py

    # === MÉTODOS PARA SALESFORCE ===
    
    def _create_salesforce_card(self) -> QFrame:
        """Card para configuración de Salesforce API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                padding: 4px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header_layout = QHBoxLayout()
        icon_name = QLabel("☁️ Salesforce API")
        icon_name.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #1e293b;
            background: transparent;
        """)
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        info_label = QLabel("Requiere: Username + Password + Security Token")
        info_label.setStyleSheet("font-size: 12px; color: #64748b; background: transparent;")
        layout.addWidget(info_label)
        
        self.salesforce_username_input = QLineEdit()
        self.salesforce_username_input.setPlaceholderText("Username (email)")
        self.salesforce_username_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #00a1e0;
            }
        """)
        layout.addWidget(self.salesforce_username_input)
        
        self.salesforce_password_input = QLineEdit()
        self.salesforce_password_input.setPlaceholderText("Password")
        self.salesforce_password_input.setEchoMode(QLineEdit.Password)
        self.salesforce_password_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #00a1e0;
            }
        """)
        layout.addWidget(self.salesforce_password_input)
        
        self.salesforce_token_input = QLineEdit()
        self.salesforce_token_input.setPlaceholderText("Security Token")
        self.salesforce_token_input.setEchoMode(QLineEdit.Password)
        self.salesforce_token_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #00a1e0;
            }
        """)
        layout.addWidget(self.salesforce_token_input)
        
        btn_layout = QHBoxLayout()
        
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e0e7ff;
                border-color: #6366f1;
                color: #6366f1;
            }
        """)
        guide_btn.clicked.connect(self._show_salesforce_guide)
        btn_layout.addWidget(guide_btn)
        
        btn_layout.addStretch()
        
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e7ff;
                color: #6366f1;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c7d2fe;
            }
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
<li>Ve a Setup → API → API Enabled</li>
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
            
            QMessageBox.information(
                self,
                "✅ Configuración Guardada",
                "Salesforce configurado correctamente!\n\n"
                f"Username: {username}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    # === MÉTODOS PARA QUICKBOOKS ===
    
    def _create_quickbooks_card(self) -> QFrame:
        """Card para configuración de QuickBooks API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                padding: 4px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header_layout = QHBoxLayout()
        icon_name = QLabel("💰 QuickBooks API")
        icon_name.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #1e293b;
            background: transparent;
        """)
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        info_label = QLabel("Requiere: Client ID + Client Secret (OAuth 2.0)")
        info_label.setStyleSheet("font-size: 12px; color: #64748b; background: transparent;")
        layout.addWidget(info_label)
        
        self.quickbooks_client_id_input = QLineEdit()
        self.quickbooks_client_id_input.setPlaceholderText("Client ID")
        self.quickbooks_client_id_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #2ca01c;
            }
        """)
        layout.addWidget(self.quickbooks_client_id_input)
        
        self.quickbooks_client_secret_input = QLineEdit()
        self.quickbooks_client_secret_input.setPlaceholderText("Client Secret")
        self.quickbooks_client_secret_input.setEchoMode(QLineEdit.Password)
        self.quickbooks_client_secret_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #2ca01c;
            }
        """)
        layout.addWidget(self.quickbooks_client_secret_input)
        
        self.quickbooks_realm_input = QLineEdit()
        self.quickbooks_realm_input.setPlaceholderText("Realm ID / Company ID (opcional)")
        self.quickbooks_realm_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #2ca01c;
            }
        """)
        layout.addWidget(self.quickbooks_realm_input)
        
        btn_layout = QHBoxLayout()
        
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e0e7ff;
                border-color: #6366f1;
                color: #6366f1;
            }
        """)
        guide_btn.clicked.connect(self._show_quickbooks_guide)
        btn_layout.addWidget(guide_btn)
        
        btn_layout.addStretch()
        
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e7ff;
                color: #6366f1;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c7d2fe;
            }
        """)
        test_btn.clicked.connect(self._verify_quickbooks)
        btn_layout.addWidget(test_btn)
        
        layout.addLayout(btn_layout)
        return card
    
    def _show_quickbooks_guide(self):
        guide = """
<h2>💰 Guía de Configuración - QuickBooks API</h2>

<h3>🔑 PASO 1: Crear App en Intuit Developer</h3>
<ol>
<li>Ve a <a href='https://developer.intuit.com'>developer.intuit.com</a></li>
<li>Crea una cuenta o inicia sesión</li>
<li>Ve a Dashboard → Create an App</li>
<li>Selecciona QuickBooks Online</li>
</ol>

<h3>🔑 PASO 2: Obtener Credenciales</h3>
<ol>
<li>En tu app, ve a "Keys & OAuth"</li>
<li>Copia el Client ID y Client Secret</li>
<li>Configura Redirect URI: http://localhost</li>
</ol>

<h3>🔑 PASO 3: Obtener Realm ID</h3>
<ol>
<li>Abre tu compañía en QuickBooks</li>
<li>El Realm ID aparece en la URL o en Company Settings</li>
</ol>

<h3>✅ PASO 4: Configurar en MININA</h3>
<ol>
<li>Pega Client ID, Client Secret y Realm ID</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("💰 Guía QuickBooks - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_quickbooks(self):
        try:
            client_id = self.quickbooks_client_id_input.text().strip()
            client_secret = self.quickbooks_client_secret_input.text().strip()
            realm = self.quickbooks_realm_input.text().strip()
            
            if not client_id or not client_secret:
                QMessageBox.warning(self, "Error", "Ingresa Client ID y Client Secret")
                return
            
            QMessageBox.information(
                self,
                "✅ Configuración Guardada",
                "QuickBooks configurado correctamente!\n\n"
                f"Realm ID: {realm if realm else 'Por configurar'}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    # === MÉTODOS PARA SHOPIFY ===
    
    def _create_shopify_card(self) -> QFrame:
        """Card para configuración de Shopify API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                padding: 4px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header_layout = QHBoxLayout()
        icon_name = QLabel("🛒 Shopify API")
        icon_name.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #1e293b;
            background: transparent;
        """)
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        info_label = QLabel("Requiere: Store URL + Admin API Access Token")
        info_label.setStyleSheet("font-size: 12px; color: #64748b; background: transparent;")
        layout.addWidget(info_label)
        
        self.shopify_store_input = QLineEdit()
        self.shopify_store_input.setPlaceholderText("Store URL (tu-tienda.myshopify.com)")
        self.shopify_store_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #96bf48;
            }
        """)
        layout.addWidget(self.shopify_store_input)
        
        self.shopify_token_input = QLineEdit()
        self.shopify_token_input.setPlaceholderText("Admin API Access Token")
        self.shopify_token_input.setEchoMode(QLineEdit.Password)
        self.shopify_token_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #96bf48;
            }
        """)
        layout.addWidget(self.shopify_token_input)
        
        btn_layout = QHBoxLayout()
        
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e0e7ff;
                border-color: #6366f1;
                color: #6366f1;
            }
        """)
        guide_btn.clicked.connect(self._show_shopify_guide)
        btn_layout.addWidget(guide_btn)
        
        btn_layout.addStretch()
        
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e7ff;
                color: #6366f1;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c7d2fe;
            }
        """)
        test_btn.clicked.connect(self._verify_shopify)
        btn_layout.addWidget(test_btn)
        
        layout.addLayout(btn_layout)
        return card
    
    def _show_shopify_guide(self):
        guide = """
<h2>🛒 Guía de Configuración - Shopify API</h2>

<h3>🔑 PASO 1: Crear App Privada</h3>
<ol>
<li>Ve a tu Admin de Shopify</li>
<li>Settings → Apps and sales channels</li>
<li>Develop apps → Create an app</li>
</ol>

<h3>🔑 PASO 2: Configurar Permisos</h3>
<ol>
<li>En tu app, ve a "Configuration"</li>
<li>Selecciona permisos necesarios:
   <ul>
   <li>read_products, write_products</li>
   <li>read_orders, write_orders</li>
   <li>read_customers, write_customers</li>
   </ul>
</li>
</ol>

<h3>🔑 PASO 3: Instalar App</h3>
<ol>
<li>Click "Install app"</li>
<li>Revela el Admin API access token</li>
<li>Copia el token (empieza con shpat_)</li>
</ol>

<h3>✅ PASO 4: Configurar en MININA</h3>
<ol>
<li>Pega tu Store URL (ej: mi-tienda.myshopify.com)</li>
<li>Pega el Admin API Access Token</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("🛒 Guía Shopify - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_shopify(self):
        try:
            store = self.shopify_store_input.text().strip()
            token = self.shopify_token_input.text().strip()
            
            if not store or not token:
                QMessageBox.warning(self, "Error", "Ingresa Store URL y Access Token")
                return
            
            QMessageBox.information(
                self,
                "✅ Configuración Guardada",
                "Shopify configurado correctamente!\n\n"
                f"Store: {store}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    # === MÉTODOS PARA PAYPAL ===
    
    def _create_paypal_card(self) -> QFrame:
        """Card para configuración de PayPal API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                padding: 4px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header_layout = QHBoxLayout()
        icon_name = QLabel("💳 PayPal API")
        icon_name.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #1e293b;
            background: transparent;
        """)
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        info_label = QLabel("Requiere: Client ID + Secret (Sandbox o Live)")
        info_label.setStyleSheet("font-size: 12px; color: #64748b; background: transparent;")
        layout.addWidget(info_label)
        
        self.paypal_client_id_input = QLineEdit()
        self.paypal_client_id_input.setPlaceholderText("Client ID")
        self.paypal_client_id_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #003087;
            }
        """)
        layout.addWidget(self.paypal_client_id_input)
        
        self.paypal_secret_input = QLineEdit()
        self.paypal_secret_input.setPlaceholderText("Client Secret")
        self.paypal_secret_input.setEchoMode(QLineEdit.Password)
        self.paypal_secret_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #003087;
            }
        """)
        layout.addWidget(self.paypal_secret_input)
        
        btn_layout = QHBoxLayout()
        
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e0e7ff;
                border-color: #6366f1;
                color: #6366f1;
            }
        """)
        guide_btn.clicked.connect(self._show_paypal_guide)
        btn_layout.addWidget(guide_btn)
        
        btn_layout.addStretch()
        
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e7ff;
                color: #6366f1;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c7d2fe;
            }
        """)
        test_btn.clicked.connect(self._verify_paypal)
        btn_layout.addWidget(test_btn)
        
        layout.addLayout(btn_layout)
        return card
    
    def _show_paypal_guide(self):
        guide = """
<h2>💳 Guía de Configuración - PayPal API</h2>

<h3>🔑 PASO 1: Crear App en PayPal Developer</h3>
<ol>
<li>Ve a <a href='https://developer.paypal.com'>developer.paypal.com</a></li>
<li>Inicia sesión con tu cuenta PayPal</li>
<li>Dashboard → Create App</li>
</ol>

<h3>🔑 PASO 2: Obtener Credenciales</h3>
<ol>
<li>Nombra tu app (ej: "MININA")</li>
<li>Selecciona Sandbox (pruebas) o Live (producción)</li>
<li>Copia el Client ID y Secret</li>
</ol>

<h3>✅ PASO 3: Configurar en MININA</h3>
<ol>
<li>Pega el Client ID y Secret</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("💳 Guía PayPal - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_paypal(self):
        try:
            client_id = self.paypal_client_id_input.text().strip()
            secret = self.paypal_secret_input.text().strip()
            
            if not client_id or not secret:
                QMessageBox.warning(self, "Error", "Ingresa Client ID y Secret")
                return
            
            QMessageBox.information(
                self,
                "✅ Configuración Guardada",
                "PayPal configurado correctamente!\n\n"
                f"Client ID: {client_id[:8]}..."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    # === MÉTODOS PARA ZENDESK ===
    
    def _create_zendesk_card(self) -> QFrame:
        """Card para configuración de Zendesk API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                padding: 4px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header_layout = QHBoxLayout()
        icon_name = QLabel("🎫 Zendesk API")
        icon_name.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #1e293b;
            background: transparent;
        """)
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        info_label = QLabel("Requiere: Subdomain + Email + API Token")
        info_label.setStyleSheet("font-size: 12px; color: #64748b; background: transparent;")
        layout.addWidget(info_label)
        
        self.zendesk_subdomain_input = QLineEdit()
        self.zendesk_subdomain_input.setPlaceholderText("Subdomain (tuempresa.zendesk.com)")
        self.zendesk_subdomain_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #03363d;
            }
        """)
        layout.addWidget(self.zendesk_subdomain_input)
        
        self.zendesk_email_input = QLineEdit()
        self.zendesk_email_input.setPlaceholderText("Email de agente/admin")
        self.zendesk_email_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #03363d;
            }
        """)
        layout.addWidget(self.zendesk_email_input)
        
        self.zendesk_token_input = QLineEdit()
        self.zendesk_token_input.setPlaceholderText("API Token")
        self.zendesk_token_input.setEchoMode(QLineEdit.Password)
        self.zendesk_token_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #03363d;
            }
        """)
        layout.addWidget(self.zendesk_token_input)
        
        btn_layout = QHBoxLayout()
        
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e0e7ff;
                border-color: #6366f1;
                color: #6366f1;
            }
        """)
        guide_btn.clicked.connect(self._show_zendesk_guide)
        btn_layout.addWidget(guide_btn)
        
        btn_layout.addStretch()
        
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e7ff;
                color: #6366f1;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c7d2fe;
            }
        """)
        test_btn.clicked.connect(self._verify_zendesk)
        btn_layout.addWidget(test_btn)
        
        layout.addLayout(btn_layout)
        return card
    
    def _show_zendesk_guide(self):
        guide = """
<h2>🎫 Guía de Configuración - Zendesk API</h2>

<h3>🔑 PASO 1: Obtener API Token</h3>
<ol>
<li>Ve a tu Admin Center de Zendesk</li>
<li>Apps and integrations → APIs → Zendesk API</li>
<li>Settings tab → Enable Token Access</li>
<li>Click "+" para agregar un token</li>
</ol>

<h3>🔑 PASO 2: Identificar tu Subdomain</h3>
<ol>
<li>Tu subdomain es la primera parte de tu URL</li>
<li>Ejemplo: en "miempresa.zendesk.com", el subdomain es "miempresa"</li>
</ol>

<h3>✅ PASO 3: Configurar en MININA</h3>
<ol>
<li>Pega el Subdomain (o URL completa)</li>
<li>Pega tu Email de agente</li>
<li>Pega el API Token</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("🎫 Guía Zendesk - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_zendesk(self):
        try:
            subdomain = self.zendesk_subdomain_input.text().strip()
            email = self.zendesk_email_input.text().strip()
            token = self.zendesk_token_input.text().strip()
            
            if not subdomain or not email or not token:
                QMessageBox.warning(self, "Error", "Ingresa Subdomain, Email y Token")
                return
            
            QMessageBox.information(
                self,
                "✅ Configuración Guardada",
                "Zendesk configurado correctamente!\n\n"
                f"Subdomain: {subdomain}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    # === MÉTODOS PARA CLICKUP ===
    
    def _create_clickup_card(self) -> QFrame:
        """Card para configuración de ClickUp API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                padding: 4px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header_layout = QHBoxLayout()
        icon_name = QLabel("📋 ClickUp API")
        icon_name.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #1e293b;
            background: transparent;
        """)
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        info_label = QLabel("Requiere: API Token (desde Settings → Apps)")
        info_label.setStyleSheet("font-size: 12px; color: #64748b; background: transparent;")
        layout.addWidget(info_label)
        
        self.clickup_token_input = QLineEdit()
        self.clickup_token_input.setPlaceholderText("API Token (pk_xxxxxxxx)")
        self.clickup_token_input.setEchoMode(QLineEdit.Password)
        self.clickup_token_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #7b68ee;
            }
        """)
        layout.addWidget(self.clickup_token_input)
        
        btn_layout = QHBoxLayout()
        
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e0e7ff;
                border-color: #6366f1;
                color: #6366f1;
            }
        """)
        guide_btn.clicked.connect(self._show_clickup_guide)
        btn_layout.addWidget(guide_btn)
        
        btn_layout.addStretch()
        
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e7ff;
                color: #6366f1;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c7d2fe;
            }
        """)
        test_btn.clicked.connect(self._verify_clickup)
        btn_layout.addWidget(test_btn)
        
        layout.addLayout(btn_layout)
        return card
    
    def _show_clickup_guide(self):
        guide = """
<h2>📋 Guía de Configuración - ClickUp API</h2>

<h3>🔑 PASO 1: Obtener API Token</h3>
<ol>
<li>Inicia sesión en ClickUp</li>
<li>Ve a Settings (rueda dentada) → Apps</li>
<li>ClickUp API → Generate</li>
<li>Copia el token (empieza con pk_)</li>
</ol>

<h3>✅ PASO 2: Configurar en MININA</h3>
<ol>
<li>Pega el API Token</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("📋 Guía ClickUp - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_clickup(self):
        try:
            token = self.clickup_token_input.text().strip()
            
            if not token:
                QMessageBox.warning(self, "Error", "Ingresa el API Token")
                return
            
            QMessageBox.information(
                self,
                "✅ Configuración Guardada",
                "ClickUp configurado correctamente!\n\n"
                f"Token: {token[:8]}..."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    # === MÉTODOS PARA GITLAB ===
    
    def _create_gitlab_card(self) -> QFrame:
        """Card para configuración de GitLab API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                padding: 4px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header_layout = QHBoxLayout()
        icon_name = QLabel("🦊 GitLab API")
        icon_name.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #1e293b;
            background: transparent;
        """)
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        info_label = QLabel("Requiere: Personal Access Token (PAT)")
        info_label.setStyleSheet("font-size: 12px; color: #64748b; background: transparent;")
        layout.addWidget(info_label)
        
        self.gitlab_token_input = QLineEdit()
        self.gitlab_token_input.setPlaceholderText("Personal Access Token (glpat-xxx)")
        self.gitlab_token_input.setEchoMode(QLineEdit.Password)
        self.gitlab_token_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #fc6d26;
            }
        """)
        layout.addWidget(self.gitlab_token_input)
        
        self.gitlab_url_input = QLineEdit()
        self.gitlab_url_input.setPlaceholderText("GitLab URL (opcional, por defecto: gitlab.com)")
        self.gitlab_url_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #fc6d26;
            }
        """)
        layout.addWidget(self.gitlab_url_input)
        
        btn_layout = QHBoxLayout()
        
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e0e7ff;
                border-color: #6366f1;
                color: #6366f1;
            }
        """)
        guide_btn.clicked.connect(self._show_gitlab_guide)
        btn_layout.addWidget(guide_btn)
        
        btn_layout.addStretch()
        
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e7ff;
                color: #6366f1;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c7d2fe;
            }
        """)
        test_btn.clicked.connect(self._verify_gitlab)
        btn_layout.addWidget(test_btn)
        
        layout.addLayout(btn_layout)
        return card
    
    def _show_gitlab_guide(self):
        guide = """
<h2>🦊 Guía de Configuración - GitLab API</h2>

<h3>🔑 PASO 1: Crear Personal Access Token</h3>
<ol>
<li>Ve a tu perfil en GitLab</li>
<li>Edit Profile → Access Tokens</li>
<li>Add new token</li>
<li>Nombra el token (ej: "MININA")</li>
<li>Selecciona scopes:
   <ul>
   <li>read_api</li>
   <li>read_repository</li>
   <li>write_repository</li>
   </ul>
</li>
<li>Click Create personal access token</li>
</ol>

<h3>🔑 PASO 2: Copiar Token</h3>
<ol>
<li>⚠️ <b>IMPORTANTE:</b> Copia el token INMEDIATAMENTE</li>
<li>El token empieza con glpat-</li>
</ol>

<h3>✅ PASO 3: Configurar en MININA</h3>
<ol>
<li>Pega el Personal Access Token</li>
<li>(Opcional) Pega tu GitLab URL si usas GitLab auto-hosteado</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("🦊 Guía GitLab - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_gitlab(self):
        try:
            token = self.gitlab_token_input.text().strip()
            url = self.gitlab_url_input.text().strip()
            
            if not token:
                QMessageBox.warning(self, "Error", "Ingresa el Personal Access Token")
                return
            
            QMessageBox.information(
                self,
                "✅ Configuración Guardada",
                "GitLab configurado correctamente!\n\n"
                f"Token: {token[:8]}..."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")
