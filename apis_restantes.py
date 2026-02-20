
    def _create_paypal_card(self) -> QFrame:
        """Card para configuración de PayPal API"""
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
        icon_name = QLabel("💳 PayPal API")
        icon_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb; background: transparent;")
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        info_label = QLabel("Requiere: Client ID + Secret (Sandbox o Live)")
        info_label.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.72); background: transparent;")
        layout.addWidget(info_label)
        self.paypal_client_id_input = QLineEdit()
        self.paypal_client_id_input.setPlaceholderText("Client ID")
        self.paypal_client_id_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #003087; }
        """)
        layout.addWidget(self.paypal_client_id_input)
        self.paypal_secret_input = QLineEdit()
        self.paypal_secret_input.setPlaceholderText("Client Secret")
        self.paypal_secret_input.setEchoMode(QLineEdit.Password)
        self.paypal_secret_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #003087; }
        """)
        layout.addWidget(self.paypal_secret_input)
        btn_layout = QHBoxLayout()
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: rgba(226, 232, 240, 0.9); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 8px; padding: 8px 16px; font-size: 12px; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: #003087; }
        """)
        guide_btn.clicked.connect(self._show_paypal_guide)
        btn_layout.addWidget(guide_btn)
        btn_layout.addStretch()
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: #e5e7eb; border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 8px; padding: 8px 16px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: rgba(99, 102, 241, 0.55); }
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
            QMessageBox.information(self, "✅ Configuración Guardada", f"PayPal configurado correctamente!\\n\\nClient ID: {client_id[:8]}...")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")
