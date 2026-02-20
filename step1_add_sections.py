#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para agregar las 15 APIs empresariales a settings_view.py de forma limpia
"""

import re

# Leer el archivo original
with open('core/ui/views/settings_view.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. AGREGAR SECCIONES DE APIs EMPRESARIALES EN _setup_ui
# Buscar donde termina la sección de Telegram y agregar antes de main_split.addLayout

business_sections = '''        # === APIs EMPRESARIALES / NEGOCIO ===
        
        # Salesforce
        salesforce_section = self._create_section("☁️ Salesforce")
        salesforce_section.layout().addWidget(self._create_salesforce_card())
        right_column.addWidget(salesforce_section)
        
        # QuickBooks
        quickbooks_section = self._create_section("💰 QuickBooks")
        quickbooks_section.layout().addWidget(self._create_quickbooks_card())
        right_column.addWidget(quickbooks_section)
        
        # Shopify
        shopify_section = self._create_section("🛒 Shopify")
        shopify_section.layout().addWidget(self._create_shopify_card())
        right_column.addWidget(shopify_section)
        
        # PayPal
        paypal_section = self._create_section("💳 PayPal")
        paypal_section.layout().addWidget(self._create_paypal_card())
        right_column.addWidget(paypal_section)
        
        # Zendesk
        zendesk_section = self._create_section("🎫 Zendesk")
        zendesk_section.layout().addWidget(self._create_zendesk_card())
        right_column.addWidget(zendesk_section)
        
        # ClickUp
        clickup_section = self._create_section("📋 ClickUp")
        clickup_section.layout().addWidget(self._create_clickup_card())
        right_column.addWidget(clickup_section)
        
        # GitLab
        gitlab_section = self._create_section("🦊 GitLab")
        gitlab_section.layout().addWidget(self._create_gitlab_card())
        right_column.addWidget(gitlab_section)
        
        # Airtable
        airtable_section = self._create_section("🗂️ Airtable")
        airtable_section.layout().addWidget(self._create_airtable_card())
        right_column.addWidget(airtable_section)
        
        # Pipedrive
        pipedrive_section = self._create_section("🚀 Pipedrive")
        pipedrive_section.layout().addWidget(self._create_pipedrive_card())
        right_column.addWidget(pipedrive_section)
        
        # Xero
        xero_section = self._create_section("📗 Xero")
        xero_section.layout().addWidget(self._create_xero_card())
        right_column.addWidget(xero_section)
        
        # WooCommerce
        woocommerce_section = self._create_section("🏪 WooCommerce")
        woocommerce_section.layout().addWidget(self._create_woocommerce_card())
        right_column.addWidget(woocommerce_section)
        
        # Freshdesk
        freshdesk_section = self._create_section("🆘 Freshdesk")
        freshdesk_section.layout().addWidget(self._create_freshdesk_card())
        right_column.addWidget(freshdesk_section)
        
        # Wrike
        wrike_section = self._create_section("📊 Wrike")
        wrike_section.layout().addWidget(self._create_wrike_card())
        right_column.addWidget(wrike_section)
        
        # Confluence
        confluence_section = self._create_section("📄 Confluence")
        confluence_section.layout().addWidget(self._create_confluence_card())
        right_column.addWidget(confluence_section)
        
        # Square
        square_section = self._create_section("⬜ Square")
        square_section.layout().addWidget(self._create_square_card())
        right_column.addWidget(square_section)
        
'''

# Insertar antes de main_split.addLayout(right_column, 6)
pattern = r'(        main_split\.addLayout\(right_column, 6\))'
replacement = business_sections + r'\1'
content = re.sub(pattern, replacement, content)

print("✅ Secciones de APIs empresariales agregadas")

# Guardar archivo
with open('core/ui/views/settings_view.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Archivo guardado correctamente")
