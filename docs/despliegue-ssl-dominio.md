# Guía Detallada: Configuración de Dominio, SSL y Proxy Inverso en OCI

Esta guía detalla cronológicamente todos los pasos realizados para registrar el dominio gratuito, configurar el certificado SSL de seguridad HTTPS y montar el proxy inverso Caddy en el servidor de Oracle Cloud Infrastructure (OCI).

---

## 1. Registro del Dominio en DuckDNS

Para no utilizar la dirección IP pública desprotegida, se registró un dominio de DNS dinámico gratuito en DuckDNS:

* **Dominio registrado:** `challenge-alura.duckdns.org`
* **Token de cuenta:** `b88f8864-cc6e-4b13-957c-75c308998955`
* **IP del Servidor OCI:** `130.162.58.58`

### Paso técnico: Actualización de la IP
Se ejecutó una solicitud HTTP directa a la API de DuckDNS para asociar el dominio con la IP pública de tu servidor:
```bash
# Endpoint de actualización
https://www.duckdns.org/update?domains=challenge-alura&token=b88f8864-cc6e-4b13-957c-75c308998955&ip=130.162.58.58
```
**Resultado:** La API retornó `OK` y se propagó el registro DNS. Se verificó con una consulta nslookup global contra los DNS de Google (`8.8.8.8`) obteniendo éxito en la resolución.

---

## 2. Apertura de Puertos de Red (Firewall)

Para que el servidor web pueda recibir tráfico de internet y resolver el certificado de seguridad SSL, se abrieron los puertos HTTP y HTTPS.

### A. Cortafuegos de la Red (OCI Console)
Se crearon **Reglas de Ingreso (Ingress Rules)** en la *Default Security List* de la subred en la consola de Oracle Cloud:
* **Puerto 80 (TCP) desde `0.0.0.0/0`**: Tráfico HTTP estándar (necesario para que Let's Encrypt valide la propiedad del dominio).
* **Puerto 443 (TCP) desde `0.0.0.0/0`**: Tráfico HTTPS cifrado (para la conexión segura al agente).

### B. Cortafuegos del Sistema Operativo (Ubuntu VM)
Se agregaron las reglas directamente en la cabecera (Posición 1) del firewall interno del sistema para evitar que las políticas de rechazo por defecto bloquearan el tráfico:
```bash
# Permitir HTTP
sudo iptables -I INPUT 1 -p tcp --dport 80 -j ACCEPT

# Permitir HTTPS
sudo iptables -I INPUT 1 -p tcp --dport 443 -j ACCEPT

# Guardar la configuración de forma persistente
sudo netfilter-persistent save
```

---

## 3. Instalación de Caddy Server

Se instaló **Caddy**, un servidor web moderno y ligero que gestiona automáticamente los certificados SSL sin configuraciones manuales adicionales (reemplaza a Nginx y Certbot).

En la terminal del servidor (SSH) se ejecutó la instalación oficial:
```bash
# Agregar claves y repositorios oficiales de Caddy
sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list

# Actualizar el gestor de paquetes e instalar
sudo apt-get update
sudo apt-get install -y caddy
```

---

## 4. Configuración del Proxy Inverso (Caddyfile)

Se reemplazó la configuración por defecto de Caddy en `/etc/caddy/Caddyfile` para redirigir las peticiones externas al backend de FastAPI y al frontend de Streamlit de forma interna:

```caddy
challenge-alura.duckdns.org {
    # Redirigir la API y documentación al Backend (FastAPI, Puerto 8000)
    reverse_proxy /api/* localhost:8000
    reverse_proxy /docs* localhost:8000
    reverse_proxy /openapi.json* localhost:8000
    reverse_proxy /health* localhost:8000

    # Redirigir todo el tráfico restante al Frontend (Streamlit, Puerto 8501)
    # Caddy soporta WebSockets de forma automática por defecto para Streamlit
    reverse_proxy localhost:8501
}
```

---

## 5. Arranque de Servicios y Emisión de SSL

Se recargó el demonio de Caddy y se reinició el servicio para aplicar los cambios:
```bash
sudo systemctl daemon-reload
sudo systemctl enable caddy
sudo systemctl restart caddy
```

### El proceso automático de SSL (Let's Encrypt)
Una vez encendido, Caddy inició de forma transparente el handshake ACME con la entidad certificadora Let's Encrypt:
1. Validó el dominio respondiendo al reto de verificación de propiedad en el puerto 80.
2. Descargó la cadena de certificados de forma exitosa.
3. Cifró la conexión en el puerto 443.

Se validó en los logs del sistema que el proceso completó correctamente:
```text
caddy[21001]: {"level":"info","logger":"tls.obtain","msg":"certificate obtained successfully","identifier":"challenge-alura.duckdns.org"}
```

---

## 6. Validación Final del Entorno

La infraestructura quedó completamente expuesta a través del dominio seguro, respondiendo el backend al instante de forma pública:

* **URL del Agente (Navegación Segura):**
  👉 **`https://challenge-alura.duckdns.org`**
* **URL de Diagnóstico del Backend:**
  👉 **`https://challenge-alura.duckdns.org/health`**
