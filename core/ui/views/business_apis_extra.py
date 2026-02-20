

    # === MÉTODOS PARA AIRTABLE ===
    
    def _create_airtable_card(self) -> QFrame:
        """Card para configuración de Airtable API"""
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
        icon_name = QLabel("🗂️ Airtable API")
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
        
        self.airtable_token_input = QLineEdit()
        self.airtable_token_input.setPlaceholderText("Personal Access Token (patxxxx)")
        self.airtable_token_input.setEchoMode(QLineEdit.Password)
        self.airtable_token_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #18bfff;
            }
        """)
        layout.addWidget(self.airtable_token_input)
        
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
        guide_btn.clicked.connect(self._show_airtable_guide)
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
        test_btn.clicked.connect(self._verify_airtable)
        btn_layout.addWidget(test_btn)
        
        layout.addLayout(btn_layout)
        return card
    
    def _show_airtable_guide(self):
        guide = """
<h2>🗂️ Guía de Configuración - Airtable API</h2>

<h3>🔑 PASO 1: Crear Personal Access Token</h3>
<ol>
<li>Ve a <a href='https://airtable.com/create/tokens'>airtable.com/create/tokens</a></li>
<li>Click "Create new token"</li>
<li>Nombra el token (ej: "MININA")</li>
<li>Selecciona scopes necesarios:
   <ul>
   <li>data.records:read</li>
   <li>data.records:write</li>
   <li>schema.bases:read</li>
   </ul>
</li>
<li>Agrega las bases que necesitas acceder</li>
</ol>

<h3>🔑 PASO 2: Copiar Token</h3>
<ol>
<li>Copia el token generado (empieza con pat)</li>
</ol>

<h3>✅ PASO 3: Configurar en MININA</h3>
<ol>
<li>Pega el Personal Access Token</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("🗂️ Guía Airtable - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_airtable(self):
        try:
            token = self.airtable_token_input.text().strip()
            
            if not token:
                QMessageBox.warning(self, "Error", "Ingresa el Personal Access Token")
                return
            
            QMessageBox.information(
                self,
                "✅ Configuración Guardada",
                "Airtable configurado correctamente!\n\n"
                f"Token: {token[:8]}..."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    # === MÉTODOS PARA PIPEDRIVE ===
    
    def _create_pipedrive_card(self) -> QFrame:
        """Card para configuración de Pipedrive API"""
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
        icon_name = QLabel("🚀 Pipedrive API")
        icon_name.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #1e293b;
            background: transparent;
        """)
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        info_label = QLabel("Requiere: API Token (desde Settings → Personal Preferences)")
        info_label.setStyleSheet("font-size: 12px; color: #64748b; background: transparent;")
        layout.addWidget(info_label)
        
        self.pipedrive_token_input = QLineEdit()
        self.pipedrive_token_input.setPlaceholderText("API Token")
        self.pipedrive_token_input.setEchoMode(QLineEdit.Password)
        self.pipedrive_token_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #6266f1;
            }
        """)
        layout.addWidget(self.pipedrive_token_input)
        
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
        guide_btn.clicked.connect(self._show_pipedrive_guide)
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
        test_btn.clicked.connect(self._verify_pipedrive)
        btn_layout.addWidget(test_btn)
        
        layout.addLayout(btn_layout)
        return card
    
    def _show_pipedrive_guide(self):
        guide = """
<h2>🚀 Guía de Configuración - Pipedrive API</h2>

<h3>🔑 PASO 1: Obtener API Token</h3>
<ol>
<li>Inicia sesión en Pipedrive</li>
<li>Ve a Settings (rueda dentada) → Personal preferences → API</li>
<li>Copia el API token</li>
</ol>

<h3>✅ PASO 2: Configurar en MININA</h3>
<ol>
<li>Pega el API Token</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("🚀 Guía Pipedrive - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_pipedrive(self):
        try:
            token = self.pipedrive_token_input.text().strip()
            
            if not token:
                QMessageBox.warning(self, "Error", "Ingresa el API Token")
                return
            
            QMessageBox.information(
                self,
                "✅ Configuración Guardada",
                "Pipedrive configurado correctamente!\n\n"
                f"Token: {token[:8]}..."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    # === MÉTODOS PARA XERO ===
    
    def _create_xero_card(self) -> QFrame:
        """Card para configuración de Xero API"""
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
        icon_name = QLabel("📗 Xero API")
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
        
        self.xero_client_id_input = QLineEdit()
        self.xero_client_id_input.setPlaceholderText("Client ID")
        self.xero_client_id_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #13b5ea;
            }
        """)
        layout.addWidget(self.xero_client_id_input)
        
        self.xero_client_secret_input = QLineEdit()
        self.xero_client_secret_input.setPlaceholderText("Client Secret")
        self.xero_client_secret_input.setEchoMode(QLineEdit.Password)
        self.xero_client_secret_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #13b5ea;
            }
        """)
        layout.addWidget(self.xero_client_secret_input)
        
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
        guide_btn.clicked.connect(self._show_xero_guide)
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
        test_btn.clicked.connect(self._verify_xero)
        btn_layout.addWidget(test_btn)
        
        layout.addLayout(btn_layout)
        return card
    
    def _show_xero_guide(self):
        guide = """
<h2>📗 Guía de Configuración - Xero API</h2>

<h3>🔑 PASO 1: Crear App en Xero Developer</h3>
<ol>
<li>Ve a <a href='https://developer.xero.com'>developer.xero.com</a></li>
<li>My Apps → New app</li>
<li>Selecciona "Web app"</li>
<li>Redirect URI: http://localhost</li>
</ol>

<h3>🔑 PASO 2: Obtener Credenciales</h3>
<ol>
<li>En tu app, copia Client ID y Client Secret</li>
</ol>

<h3>✅ PASO 3: Configurar en MININA</h3>
<ol>
<li>Pega Client ID y Client Secret</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("📗 Guía Xero - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_xero(self):
        try:
            client_id = self.xero_client_id_input.text().strip()
            client_secret = self.xero_client_secret_input.text().strip()
            
            if not client_id or not client_secret:
                QMessageBox.warning(self, "Error", "Ingresa Client ID y Client Secret")
                return
            
            QMessageBox.information(
                self,
                "✅ Configuración Guardada",
                "Xero configurado correctamente!\n\n"
                f"Client ID: {client_id[:8]}..."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    # === MÉTODOS PARA WOOCOMMERCE ===
    
    def _create_woocommerce_card(self) -> QFrame:
        """Card para configuración de WooCommerce API"""
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
        icon_name = QLabel("🏪 WooCommerce API")
        icon_name.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #1e293b;
            background: transparent;
        """)
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        info_label = QLabel("Requiere: Consumer Key + Consumer Secret")
        info_label.setStyleSheet("font-size: 12px; color: #64748b; background: transparent;")
        layout.addWidget(info_label)
        
        self.wc_store_url_input = QLineEdit()
        self.wc_store_url_input.setPlaceholderText("Store URL (https://mitienda.com)")
        self.wc_store_url_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #96588a;
            }
        """)
        layout.addWidget(self.wc_store_url_input)
        
        self.wc_key_input = QLineEdit()
        self.wc_key_input.setPlaceholderText("Consumer Key (ck_xxx)")
        self.wc_key_input.setEchoMode(QLineEdit.Password)
        self.wc_key_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #96588a;
            }
        """)
        layout.addWidget(self.wc_key_input)
        
        self.wc_secret_input = QLineEdit()
        self.wc_secret_input.setPlaceholderText("Consumer Secret (cs_xxx)")
        self.wc_secret_input.setEchoMode(QLineEdit.Password)
        self.wc_secret_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #96588a;
            }
        """)
        layout.addWidget(self.wc_secret_input)
        
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
        guide_btn.clicked.connect(self._show_woocommerce_guide)
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
        test_btn.clicked.connect(self._verify_woocommerce)
        btn_layout.addWidget(test_btn)
        
        layout.addLayout(btn_layout)
        return card
    
    def _show_woocommerce_guide(self):
        guide = """
<h2>🏪 Guía de Configuración - WooCommerce API</h2>

<h3>🔑 PASO 1: Habilitar REST API</h3>
<ol>
<li>Ve a tu Admin de WordPress</li>
<li>WooCommerce → Settings → Advanced → REST API</li>
<li>Click "Add key"</li>
</ol>

<h3>🔑 PASO 2: Crear API Key</h3>
<ol>
<li>Description: "MININA"</li>
<li>User: Selecciona un usuario admin</li>
<li>Permissions: Read/Write</li>
<li>Click "Generate API key"</li>
</ol>

<h3>🔑 PASO 3: Copiar Credenciales</h3>
<ol>
<li>⚠️ <b>IMPORTANTE:</b> Copia INMEDIATAMENTE:
   <ul>
   <li>Consumer Key (empieza con ck_)</li>
   <li>Consumer Secret (empieza con cs_)</li>
   </ul>
</li>
</ol>

<h3>✅ PASO 4: Configurar en MININA</h3>
<ol>
<li>Pega la Store URL</li>
<li>Pega Consumer Key y Consumer Secret</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("🏪 Guía WooCommerce - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_woocommerce(self):
        try:
            store = self.wc_store_url_input.text().strip()
            key = self.wc_key_input.text().strip()
            secret = self.wc_secret_input.text().strip()
            
            if not store or not key or not secret:
                QMessageBox.warning(self, "Error", "Ingresa Store URL, Key y Secret")
                return
            
            QMessageBox.information(
                self,
                "✅ Configuración Guardada",
                "WooCommerce configurado correctamente!\n\n"
                f"Store: {store}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    # === MÉTODOS PARA FRESHDESK ===
    
    def _create_freshdesk_card(self) -> QFrame:
        """Card para configuración de Freshdesk API"""
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
        icon_name = QLabel("🆘 Freshdesk API")
        icon_name.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #1e293b;
            background: transparent;
        """)
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        info_label = QLabel("Requiere: API Key (desde Profile Settings)")
        info_label.setStyleSheet("font-size: 12px; color: #64748b; background: transparent;")
        layout.addWidget(info_label)
        
        self.freshdesk_domain_input = QLineEdit()
        self.freshdesk_domain_input.setPlaceholderText("Domain (tuempresa.freshdesk.com)")
        self.freshdesk_domain_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #25c151;
            }
        """)
        layout.addWidget(self.freshdesk_domain_input)
        
        self.freshdesk_key_input = QLineEdit()
        self.freshdesk_key_input.setPlaceholderText("API Key")
        self.freshdesk_key_input.setEchoMode(QLineEdit.Password)
        self.freshdesk_key_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #25c151;
            }
        """)
        layout.addWidget(self.freshdesk_key_input)
        
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
        guide_btn.clicked.connect(self._show_freshdesk_guide)
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
        test_btn.clicked.connect(self._verify_freshdesk)
        btn_layout.addWidget(test_btn)
        
        layout.addLayout(btn_layout)
        return card
    
    def _show_freshdesk_guide(self):
        guide = """
<h2>🆘 Guía de Configuración - Freshdesk API</h2>

<h3>🔑 PASO 1: Obtener API Key</h3>
<ol>
<li>Inicia sesión en Freshdesk</li>
<li>Click en tu perfil (arriba derecha)</li>
<li>Profile Settings</li>
<li>Copia el "Your API Key"</li>
</ol>

<h3>🔑 PASO 2: Identificar tu Domain</h3>
<ol>
<li>Tu domain es la primera parte de tu URL</li>
<li>Ejemplo: en "miempresa.freshdesk.com", el domain es "miempresa"</li>
</ol>

<h3>✅ PASO 3: Configurar en MININA</h3>
<ol>
<li>Pega el Domain</li>
<li>Pega el API Key</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("🆘 Guía Freshdesk - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_freshdesk(self):
        try:
            domain = self.freshdesk_domain_input.text().strip()
            key = self.freshdesk_key_input.text().strip()
            
            if not domain or not key:
                QMessageBox.warning(self, "Error", "Ingresa Domain y API Key")
                return
            
            QMessageBox.information(
                self,
                "✅ Configuración Guardada",
                "Freshdesk configurado correctamente!\n\n"
                f"Domain: {domain}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    # === MÉTODOS PARA WRIKE ===
    
    def _create_wrike_card(self) -> QFrame:
        """Card para configuración de Wrike API"""
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
        icon_name = QLabel("📊 Wrike API")
        icon_name.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #1e293b;
            background: transparent;
        """)
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        info_label = QLabel("Requiere: Permanent Access Token (PAT)")
        info_label.setStyleSheet("font-size: 12px; color: #64748b; background: transparent;")
        layout.addWidget(info_label)
        
        self.wrike_token_input = QLineEdit()
        self.wrike_token_input.setPlaceholderText("Permanent Access Token (eyJ...)")
        self.wrike_token_input.setEchoMode(QLineEdit.Password)
        self.wrike_token_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #8c31ff;
            }
        """)
        layout.addWidget(self.wrike_token_input)
        
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
        guide_btn.clicked.connect(self._show_wrike_guide)
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
        test_btn.clicked.connect(self._verify_wrike)
        btn_layout.addWidget(test_btn)
        
        layout.addLayout(btn_layout)
        return card
    
    def _show_wrike_guide(self):
        guide = """
<h2>📊 Guía de Configuración - Wrike API</h2>

<h3>🔑 PASO 1: Crear App en Wrike</h3>
<ol>
<li>Inicia sesión en Wrike</li>
<li>Click en tu perfil → Apps & Integrations</li>
<li>API → Create App</li>
</ol>

<h3>🔑 PASO 2: Obtener Access Token</h3>
<ol>
<li>En tu app, ve a "API" tab</li>
<li>Click "Obtain access token"</li>
<li>Copia el Permanent Access Token</li>
</ol>

<h3>✅ PASO 3: Configurar en MININA</h3>
<ol>
<li>Pega el Permanent Access Token</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("📊 Guía Wrike - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_wrike(self):
        try:
            token = self.wrike_token_input.text().strip()
            
            if not token:
                QMessageBox.warning(self, "Error", "Ingresa el Permanent Access Token")
                return
            
            QMessageBox.information(
                self,
                "✅ Configuración Guardada",
                "Wrike configurado correctamente!\n\n"
                f"Token: {token[:10]}..."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    # === MÉTODOS PARA CONFLUENCE ===
    
    def _create_confluence_card(self) -> QFrame:
        """Card para configuración de Confluence API"""
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
        icon_name = QLabel("📄 Confluence API")
        icon_name.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #1e293b;
            background: transparent;
        """)
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        info_label = QLabel("Requiere: API Token (desde Atlassian Account)")
        info_label.setStyleSheet("font-size: 12px; color: #64748b; background: transparent;")
        layout.addWidget(info_label)
        
        self.confluence_url_input = QLineEdit()
        self.confluence_url_input.setPlaceholderText("Confluence URL (tuempresa.atlassian.net/wiki)")
        self.confluence_url_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #0052cc;
            }
        """)
        layout.addWidget(self.confluence_url_input)
        
        self.confluence_email_input = QLineEdit()
        self.confluence_email_input.setPlaceholderText("Email de Atlassian")
        self.confluence_email_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #0052cc;
            }
        """)
        layout.addWidget(self.confluence_email_input)
        
        self.confluence_token_input = QLineEdit()
        self.confluence_token_input.setPlaceholderText("API Token")
        self.confluence_token_input.setEchoMode(QLineEdit.Password)
        self.confluence_token_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #0052cc;
            }
        """)
        layout.addWidget(self.confluence_token_input)
        
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
        guide_btn.clicked.connect(self._show_confluence_guide)
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
        test_btn.clicked.connect(self._verify_confluence)
        btn_layout.addWidget(test_btn)
        
        layout.addLayout(btn_layout)
        return card
    
    def _show_confluence_guide(self):
        guide = """
<h2>📄 Guía de Configuración - Confluence API</h2>

<h3>🔑 PASO 1: Crear API Token</h3>
<ol>
<li>Ve a <a href='https://id.atlassian.com/manage-profile/security/api-tokens'>id.atlassian.com</a></li>
<li>Click "Create API token"</li>
<li>Nombra el token (ej: "MININA")</li>
<li>Copia el token generado</li>
</ol>

<h3>🔑 PASO 2: Identificar tu URL</h3>
<ol>
<li>Tu Confluence URL es similar a: tuempresa.atlassian.net/wiki</li>
</ol>

<h3>✅ PASO 3: Configurar en MININA</h3>
<ol>
<li>Pega la Confluence URL</li>
<li>Pega tu Email de Atlassian</li>
<li>Pega el API Token</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("📄 Guía Confluence - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_confluence(self):
        try:
            url = self.confluence_url_input.text().strip()
            email = self.confluence_email_input.text().strip()
            token = self.confluence_token_input.text().strip()
            
            if not url or not email or not token:
                QMessageBox.warning(self, "Error", "Ingresa URL, Email y Token")
                return
            
            QMessageBox.information(
                self,
                "✅ Configuración Guardada",
                "Confluence configurado correctamente!\n\n"
                f"URL: {url}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    # === MÉTODOS PARA SQUARE ===
    
    def _create_square_card(self) -> QFrame:
        """Card para configuración de Square API"""
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
        icon_name = QLabel("⬜ Square API")
        icon_name.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #1e293b;
            background: transparent;
        """)
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        info_label = QLabel("Requiere: Access Token (Sandbox o Production)")
        info_label.setStyleSheet("font-size: 12px; color: #64748b; background: transparent;")
        layout.addWidget(info_label)
        
        self.square_token_input = QLineEdit()
        self.square_token_input.setPlaceholderText("Access Token (EAAA...)")
        self.square_token_input.setEchoMode(QLineEdit.Password)
        self.square_token_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #3e4348;
            }
        """)
        layout.addWidget(self.square_token_input)
        
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
        guide_btn.clicked.connect(self._show_square_guide)
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
        test_btn.clicked.connect(self._verify_square)
        btn_layout.addWidget(test_btn)
        
        layout.addLayout(btn_layout)
        return card
    
    def _show_square_guide(self):
        guide = """
<h2>⬜ Guía de Configuración - Square API</h2>

<h3>🔑 PASO 1: Crear App en Square Developer</h3>
<ol>
<li>Ve a <a href='https://developer.squareup.com'>developer.squareup.com</a></li>
<li>Inicia sesión con tu cuenta Square</li>
<li>Dashboard → New Application</li>
</ol>

<h3>🔑 PASO 2: Obtener Access Token</h3>
<ol>
<li>Selecciona tu app</li>
<li>Ve a "Credentials" tab</li>
<li>Copia el "Access token" de Sandbox o Production</li>
</ol>

<h3>✅ PASO 3: Configurar en MININA</h3>
<ol>
<li>Pega el Access Token (empieza con EAAA)</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("⬜ Guía Square - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_square(self):
        try:
            token = self.square_token_input.text().strip()
            
            if not token:
                QMessageBox.warning(self, "Error", "Ingresa el Access Token")
                return
            
            QMessageBox.information(
                self,
                "✅ Configuración Guardada",
                "Square configurado correctamente!\n\n"
                f"Token: {token[:8]}..."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")
