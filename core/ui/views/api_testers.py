
    # ==========================================================================
    # MÉTODOS DE TESTING ESPECÍFICOS POR API
    # ==========================================================================
    
    # ---------- PRODUCTIVITY APIs ----------
    
    def _test_asana(self, credentials):
        """Test Asana API connection"""
        try:
            token = credentials.get("personal_access_token") or credentials.get("access_token")
            if not token:
                return {"success": False, "error": "Se requiere Personal Access Token"}
            
            manager = AsanaManager()
            manager.access_token = token
            
            if manager._test_auth():
                return {"success": True, "details": "Token válido. Acceso confirmado a Asana."}
            else:
                return {"success": False, "error": "Token inválido o expirado"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_notion(self, credentials):
        """Test Notion API connection"""
        try:
            token = credentials.get("integration_token")
            if not token:
                return {"success": False, "error": "Se requiere Integration Token"}
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28"
            }
            
            response = requests.get(
                "https://api.notion.com/v1/users",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                user_count = len(data.get("results", []))
                return {
                    "success": True, 
                    "details": f"Conectado a Notion. {user_count} usuarios encontrados."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Token inválido. Verifica tu Integration Token."}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Notion API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_trello(self, credentials):
        """Test Trello API connection"""
        try:
            api_key = credentials.get("api_key")
            token = credentials.get("token")
            
            if not api_key or not token:
                return {"success": False, "error": "Se requieren API Key y Token"}
            
            params = {
                "key": api_key,
                "token": token
            }
            
            response = requests.get(
                "https://api.trello.com/1/members/me",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                username = data.get("username", "unknown")
                return {
                    "success": True,
                    "details": f"Conectado como @{username}. API funcionando correctamente."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Credenciales inválidas. Verifica API Key y Token."}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Trello API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_monday(self, credentials):
        """Test Monday.com API connection"""
        try:
            token = credentials.get("api_token")
            if not token:
                return {"success": False, "error": "Se requiere API Token"}
            
            headers = {"Authorization": token}
            
            # Query GraphQL simple
            query = {"query": "query { me { name } }"}
            
            response = requests.post(
                "https://api.monday.com/v2",
                headers=headers,
                json=query,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "me" in data["data"]:
                    name = data["data"]["me"].get("name", "User")
                    return {
                        "success": True,
                        "details": f"Conectado como {name}. API GraphQL funcionando."
                    }
                elif "errors" in data:
                    return {"success": False, "error": data["errors"][0].get("message", "Error desconocido")}
            elif response.status_code == 401:
                return {"success": False, "error": "Token inválido. Verifica tu API Token."}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Monday API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_jira(self, credentials):
        """Test Jira API connection"""
        try:
            email = credentials.get("email")
            token = credentials.get("api_token")
            domain = credentials.get("domain", "")
            
            if not email or not token:
                return {"success": False, "error": "Se requieren Email y API Token"}
            
            # Construir URL base
            base_url = f"https://{domain}.atlassian.net" if domain else "https://atlassian.net"
            
            headers = {
                "Accept": "application/json"
            }
            
            response = requests.get(
                f"{base_url}/rest/api/3/myself",
                headers=headers,
                auth=(email, token),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                display_name = data.get("displayName", "User")
                return {
                    "success": True,
                    "details": f"Conectado como {display_name}. Jira API v3 funcionando."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Credenciales inválidas o dominio incorrecto"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Jira API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ---------- COMMUNICATION APIs ----------
    
    def _test_slack(self, credentials):
        """Test Slack API connection"""
        try:
            token = credentials.get("bot_token") or credentials.get("access_token")
            if not token:
                return {"success": False, "error": "Se requiere Bot Token"}
            
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(
                "https://slack.com/api/auth.test",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    team = data.get("team", "Unknown")
                    user = data.get("user", "Bot")
                    return {
                        "success": True,
                        "details": f"Conectado a workspace '{team}' como {user}."
                    }
                else:
                    error = data.get("error", "Error desconocido")
                    return {"success": False, "error": f"Slack API Error: {error}"}
            else:
                return {"success": False, "error": f"HTTP Error {response.status_code}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Slack API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_discord(self, credentials):
        """Test Discord API connection"""
        try:
            token = credentials.get("bot_token")
            if not token:
                return {"success": False, "error": "Se requiere Bot Token"}
            
            headers = {"Authorization": f"Bot {token}"}
            
            response = requests.get(
                "https://discord.com/api/v10/users/@me",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                username = data.get("username", "Bot")
                discriminator = data.get("discriminator", "0000")
                return {
                    "success": True,
                    "details": f"Bot conectado: {username}#{discriminator}"
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Bot Token inválido"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Discord API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_zoom(self, credentials):
        """Test Zoom API connection"""
        try:
            account_id = credentials.get("account_id")
            client_id = credentials.get("client_id")
            client_secret = credentials.get("client_secret")
            
            if not all([account_id, client_id, client_secret]):
                return {"success": False, "error": "Se requieren Account ID, Client ID y Client Secret"}
            
            # Obtener access token con Server-to-Server OAuth
            auth_str = f"{client_id}:{client_secret}"
            auth_bytes = auth_str.encode('ascii')
            import base64
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "account_credentials",
                "account_id": account_id
            }
            
            response = requests.post(
                "https://zoom.us/oauth/token",
                headers=headers,
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                scope = token_data.get("scope", "unknown")
                return {
                    "success": True,
                    "details": f"OAuth Server-to-Server funcionando. Scope: {scope}"
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Credenciales OAuth inválidas"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Zoom API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_email(self, credentials):
        """Test Email SMTP connection"""
        try:
            host = credentials.get("smtp_host")
            port = int(credentials.get("smtp_port", 587))
            username = credentials.get("username")
            password = credentials.get("password")
            
            if not all([host, username, password]):
                return {"success": False, "error": "Se requieren SMTP Host, Username y Password"}
            
            import smtplib
            
            # Probar conexión SMTP
            server = smtplib.SMTP(host, port, timeout=10)
            server.starttls()
            server.login(username, password)
            server.quit()
            
            return {
                "success": True,
                "details": f"Conexión SMTP exitosa a {host}:{port}"
            }
            
        except smtplib.SMTPAuthenticationError:
            return {"success": False, "error": "Autenticación SMTP fallida. Verifica usuario/contraseña."}
        except smtplib.SMTPConnectError:
            return {"success": False, "error": f"No se pudo conectar a {host}:{port}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_twilio(self, credentials):
        """Test Twilio API connection"""
        try:
            account_sid = credentials.get("account_sid")
            auth_token = credentials.get("auth_token")
            
            if not account_sid or not auth_token:
                return {"success": False, "error": "Se requieren Account SID y Auth Token"}
            
            # Twilio API endpoint para cuenta
            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}.json"
            
            response = requests.get(
                url,
                auth=(account_sid, auth_token),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                friendly_name = data.get("friendly_name", "Account")
                status = data.get("status", "unknown")
                return {
                    "success": True,
                    "details": f"Cuenta: {friendly_name}. Status: {status}."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Credenciales Twilio inválidas"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Twilio API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ---------- STORAGE / GOOGLE APIs ----------
    
    def _test_dropbox(self, credentials):
        """Test Dropbox API connection"""
        try:
            token = credentials.get("access_token")
            if not token:
                return {"success": False, "error": "Se requiere Access Token"}
            
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.post(
                "https://api.dropboxapi.com/2/users/get_current_account",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                name = data.get("name", {}).get("display_name", "User")
                email = data.get("email", "unknown")
                return {
                    "success": True,
                    "details": f"Conectado como {name} ({email})."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Access Token inválido o expirado"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Dropbox API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_google_calendar(self, credentials):
        """Test Google Calendar API"""
        return self._test_google_api(credentials, "calendar")
    
    def _test_google_drive(self, credentials):
        """Test Google Drive API"""
        return self._test_google_api(credentials, "drive")
    
    def _test_google_api(self, credentials, service_name):
        """Helper para testear APIs de Google con OAuth2"""
        try:
            # En implementación real, necesitaríamos el refresh_token
            # Aquí simulamos el test verificando que el formato de credenciales sea correcto
            client_id = credentials.get("client_id")
            client_secret = credentials.get("client_secret")
            refresh_token = credentials.get("refresh_token")
            
            if not all([client_id, client_secret]):
                return {"success": False, "error": f"Se requieren Client ID y Client Secret para Google {service_name}"}
            
            # Verificar formato de credenciales
            if not client_id.endswith(".apps.googleusercontent.com"):
                return {"success": False, "error": "Client ID parece inválido. Debe terminar en .apps.googleusercontent.com"}
            
            # Intentar obtener access token con refresh token si está disponible
            if refresh_token:
                token_url = "https://oauth2.googleapis.com/token"
                data = {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token"
                }
                
                response = requests.post(token_url, data=data, timeout=10)
                
                if response.status_code == 200:
                    token_data = response.json()
                    scopes = token_data.get("scope", "")
                    return {
                        "success": True,
                        "details": f"OAuth2 funcionando. Scopes: {scopes[:100]}..."
                    }
                elif response.status_code == 401:
                    return {"success": False, "error": "Refresh token inválido o expirado"}
                else:
                    return {"success": False, "error": f"Error OAuth: {response.status_code}"}
            else:
                return {
                    "success": True,
                    "details": f"Credenciales formato válido. Para test completo, agrega Refresh Token."
                }
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Google OAuth"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ---------- DEVELOPMENT APIs ----------
    
    def _test_github(self, credentials):
        """Test GitHub API connection"""
        try:
            token = credentials.get("personal_access_token") or credentials.get("access_token")
            if not token:
                return {"success": False, "error": "Se requiere Personal Access Token"}
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.get(
                "https://api.github.com/user",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                login = data.get("login", "user")
                name = data.get("name", login)
                return {
                    "success": True,
                    "details": f"Conectado como {name} (@{login}). API v3 funcionando."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Token inválido. Verifica tu PAT."}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con GitHub API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ---------- MARKETING APIs ----------
    
    def _test_mailchimp(self, credentials):
        """Test Mailchimp API connection"""
        try:
            api_key = credentials.get("api_key")
            if not api_key:
                return {"success": False, "error": "Se requiere API Key"}
            
            # Extraer datacenter del API key (formato: key-dc)
            if "-" in api_key:
                dc = api_key.split("-")[-1]
            else:
                return {"success": False, "error": "API Key inválida. Debe tener formato 'key-dc'"}
            
            url = f"https://{dc}.api.mailchimp.com/3.0/"
            
            response = requests.get(
                url,
                auth=("anystring", api_key),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                account_name = data.get("account_name", "Account")
                total_subscribers = data.get("total_subscribers", 0)
                return {
                    "success": True,
                    "details": f"Cuenta: {account_name}. Total suscriptores: {total_subscribers}."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "API Key inválida"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Mailchimp API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_hubspot(self, credentials):
        """Test HubSpot API connection"""
        try:
            token = credentials.get("access_token") or credentials.get("api_key")
            if not token:
                return {"success": False, "error": "Se requiere Access Token o API Key"}
            
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(
                "https://api.hubapi.com/integrations/v1/me",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                hub_id = data.get("hubId", "unknown")
                app_name = data.get("appName", "Unknown")
                return {
                    "success": True,
                    "details": f"Conectado a Hub {hub_id}. App: {app_name}."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Token inválido"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con HubSpot API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ---------- FINANCIAL APIs ----------
    
    def _test_stripe(self, credentials):
        """Test Stripe API connection"""
        try:
            secret_key = credentials.get("secret_key") or credentials.get("api_key")
            if not secret_key:
                return {"success": False, "error": "Se requiere Secret Key"}
            
            # Stripe API usa Basic auth con la API key
            response = requests.get(
                "https://api.stripe.com/v1/account",
                auth=(secret_key, ""),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                account_name = data.get("settings", {}).get("dashboard", {}).get("display_name", "Account")
                charges_enabled = data.get("charges_enabled", False)
                status = "✅ Pagos habilitados" if charges_enabled else "⚠️ Pagos no habilitados"
                return {
                    "success": True,
                    "details": f"Cuenta: {account_name}. {status}."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Secret Key inválida"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Stripe API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ---------- MEDIA / SOCIAL APIs ----------
    
    def _test_twitter(self, credentials):
        """Test Twitter/X API connection"""
        try:
            bearer_token = credentials.get("bearer_token")
            api_key = credentials.get("api_key")
            api_secret = credentials.get("api_secret")
            
            if not bearer_token and not (api_key and api_secret):
                return {"success": False, "error": "Se requiere Bearer Token o API Key + Secret"}
            
            headers = {}
            if bearer_token:
                headers["Authorization"] = f"Bearer {bearer_token}"
            else:
                # Para OAuth 1.0a necesitaríamos más credenciales
                return {"success": False, "error": "Bearer Token requerido para API v2"}
            
            response = requests.get(
                "https://api.twitter.com/2/users/me",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                user_data = data.get("data", {})
                username = user_data.get("username", "unknown")
                name = user_data.get("name", username)
                return {
                    "success": True,
                    "details": f"Conectado como @{username} ({name}). API v2 funcionando."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Bearer Token inválido"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Twitter API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_spotify(self, credentials):
        """Test Spotify API connection"""
        try:
            client_id = credentials.get("client_id")
            client_secret = credentials.get("client_secret")
            
            if not client_id or not client_secret:
                return {"success": False, "error": "Se requieren Client ID y Client Secret"}
            
            # Spotify OAuth: obtener access token con client credentials
            auth_str = f"{client_id}:{client_secret}"
            auth_bytes = auth_str.encode('ascii')
            import base64
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {"grant_type": "client_credentials"}
            
            response = requests.post(
                "https://accounts.spotify.com/api/token",
                headers=headers,
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                token_type = token_data.get("token_type", "Bearer")
                expires_in = token_data.get("expires_in", 3600)
                return {
                    "success": True,
                    "details": f"OAuth Client Credentials funcionando. Token válido por {expires_in}s."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Client ID o Secret inválidos"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Spotify API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ---------- UTILITIES APIs ----------
    
    def _test_web_search(self, credentials):
        """Test Google Custom Search API"""
        try:
            api_key = credentials.get("api_key")
            cx = credentials.get("cx") or credentials.get("search_engine_id")
            
            if not api_key:
                return {"success": False, "error": "Se requiere API Key"}
            
            # Hacer una búsqueda de prueba
            params = {
                "key": api_key,
                "q": "test"
            }
            if cx:
                params["cx"] = cx
            
            response = requests.get(
                "https://www.googleapis.com/customsearch/v1",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                total_results = data.get("searchInformation", {}).get("totalResults", "0")
                return {
                    "success": True,
                    "details": f"API funcionando. Resultados totales disponibles: {total_results}."
                }
            elif response.status_code == 400:
                return {"success": False, "error": "CX (Search Engine ID) requerido para Custom Search"}
            elif response.status_code == 401:
                return {"success": False, "error": "API Key inválida"}
            elif response.status_code == 403:
                return {"success": False, "error": "API Key no tiene permisos para Custom Search API"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Google Search API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ---------- AI PROVIDERS ----------
    
    def _test_openai(self, credentials):
        """Test OpenAI API connection"""
        try:
            api_key = credentials.get("api_key")
            if not api_key:
                return {"success": False, "error": "Se requiere API Key"}
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Usar endpoint de modelos (más ligero que completions)
            response = requests.get(
                "https://api.openai.com/v1/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                model_count = len(data.get("data", []))
                return {
                    "success": True,
                    "details": f"Conectado a OpenAI. {model_count} modelos disponibles."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "API Key inválida"}
            elif response.status_code == 429:
                return {"success": False, "error": "Rate limit excedido. Revisa tu plan."}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con OpenAI API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_groq(self, credentials):
        """Test Groq API connection"""
        try:
            api_key = credentials.get("api_key")
            if not api_key:
                return {"success": False, "error": "Se requiere API Key"}
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                model_count = len(data.get("data", []))
                return {
                    "success": True,
                    "details": f"Conectado a Groq. {model_count} modelos disponibles (Llama, Mixtral, etc.)."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "API Key inválida"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Groq API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_gemini(self, credentials):
        """Test Google Gemini API connection"""
        try:
            api_key = credentials.get("api_key")
            if not api_key:
                return {"success": False, "error": "Se requiere API Key"}
            
            # Gemini usa la API key como parámetro de query
            response = requests.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "").split("/")[-1] for m in data.get("models", [])]
                gemini_models = [m for m in models if "gemini" in m.lower()]
                return {
                    "success": True,
                    "details": f"Conectado a Gemini. {len(gemini_models)} modelos Gemini disponibles."
                }
            elif response.status_code == 400:
                return {"success": False, "error": "API Key inválida"}
            elif response.status_code == 403:
                return {"success": False, "error": "API Key no tiene acceso a Gemini API"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Gemini API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_ollama(self, credentials):
        """Test Ollama local server"""
        try:
            base_url = credentials.get("base_url", "http://localhost:11434")
            
            # Intentar conectar al servidor local de Ollama
            response = requests.get(
                f"{base_url}/api/tags",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                model_names = [m.get("name", "unknown") for m in models]
                model_list = ", ".join(model_names[:3])
                if len(model_names) > 3:
                    model_list += f" y {len(model_names) - 3} más"
                return {
                    "success": True,
                    "details": f"Ollama corriendo en {base_url}. Modelos: {model_list}."
                }
            else:
                return {"success": False, "error": f"Ollama respondió con error {response.status_code}"}
                
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": f"No se pudo conectar a Ollama en {base_url}. ¿Está el servidor corriendo?"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": f"Timeout al conectar con Ollama en {base_url}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ==========================================================================
# FIN DE MÉTODOS DE TESTING
# ==========================================================================
