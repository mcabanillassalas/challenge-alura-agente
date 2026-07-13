# Guía de despliegue en Oracle OCI Free Tier sin Docker

## Resumen ejecutivo

Esta guía cubre el despliegue del Agente RAG de Exactus en una instancia de **Oracle Cloud Infrastructure (OCI) Free Tier** sin usar Docker.

> Si prefieres desplegar con Docker, consulta [deploy-OCI-Docker.md](deploy-OCI-Docker.md).

## ¿Por qué desplegar sin Docker?

**Opcionalmente recomendable** cuando:

- Quieres reducir overhead de recursos
- Prefieres un despliegue más directo y simple
- Tu instancia tiene capacidad suficiente

**Ventaja**: menos complejidad.
**Desventaja**: más frágil ante cambios de dependencias.

---

## Requisitos previos

- Cuenta Oracle Cloud Free Tier activa
- SSH configurado en tu máquina local (ver sección abajo para generarlas si no las tienes)
- Archivos del proyecto listos para subir
- PDFs de Exactus en la carpeta `data/raw/exactus/`

### Generación de claves SSH (Si no las tienes creadas)

Si no tienes una clave SSH configurada en tu máquina local, puedes crear un par de claves (pública y privada) de la siguiente manera:

#### En Windows (PowerShell) / Linux / macOS:

1. Abre tu terminal (PowerShell en Windows) y ejecuta:

   ```bash
   ssh-keygen -t rsa -b 4096 -f "$HOME/.ssh/id_rsa_oci"
   ```

   _(Cuando te pida una frase de paso o "passphrase", puedes presionar `Enter` para dejarla vacía, o escribir una clave de seguridad)._

2. Esto generará dos archivos en tu carpeta `.ssh` (normalmente en `C:\Users\TU_USUARIO\.ssh\` en Windows):
   - **Clave privada:** `id_rsa_oci` (es la clave que mantienes segura en tu máquina).
   - **Clave pública:** `id_rsa_oci.pub` (es la que subirás a OCI).

3. Copia el contenido de tu clave pública:
   - **En Windows (PowerShell):**
     ```powershell
     Get-Content "$HOME\.ssh\id_rsa_oci.pub" | clip
     ```
     _(Esto copiará el texto directamente a tu portapapeles)._
   - **En Linux / macOS:**
     ```bash
     cat ~/.ssh/id_rsa_oci.pub
     ```
     _(Copia el bloque de texto que se muestra en pantalla)._

4. Durante el **Paso 1: Crear la instancia en OCI**, en la sección de claves SSH, selecciona **"Paste public keys"** (Pegar claves públicas) y pega el contenido copiado.

---

## Paso 1: Crear la instancia en OCI

1. Abre **Oracle Cloud Console** → **Compute** → **Instances**
2. Crea una nueva instancia
3. Usa:
   - Imagen: Ubuntu 22.04 o 24.04
   - Shape: Ampere (Free Tier)
   - OCPU: 4 (gratis)
   - Memoria: 24 GB (gratis)
   - Almacenamiento: 200 GB
4. Asigna una IP pública
5. Sube tu clave SSH

---

## Paso 2: Conectarte a la instancia

Desde tu PowerShell local en Windows, utiliza la IP pública de tu instancia (`130.162.58.58`) y la ruta real de tu clave privada:

```powershell
$instanceIP = "130.162.58.58"
$keyPath = "D:\DevALURA\challenge-alura-agente\ssh-keys\ssh-key-2026-07-10.key"
ssh -i $keyPath ubuntu@$instanceIP
```

Actualiza el sistema:

```bash
sudo apt update && sudo apt upgrade -y
```

---

## Paso 3: Instalar Python y dependencias

Ubuntu (la imagen por defecto en OCI) no siempre incluye Python 3.11 por defecto. Elige una de estas opciones:

### Opción A: Usar la versión por defecto de Python 3 (Recomendado)

Ubuntu 22.04 usa Python 3.10 y Ubuntu 24.04 usa Python 3.12. Ambas versiones son compatibles con este proyecto:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip build-essential git
python3 --version
```

### Opción B: Instalar específicamente Python 3.11 (Requiere PPA externo en Ubuntu 22.04)

```bash
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev build-essential git
python3.11 --version
```

---

## Paso 4: Configurar memoria de intercambio (SWAP) (Crítico para OCI Free Tier)

Tu instancia gratuita `VM.Standard.E2.1.Micro` cuenta únicamente con **1 GB de RAM**. El procesamiento de archivos PDF y la generación de embeddings en Python consumen mucha memoria y harán que la máquina virtual colapse (provocando desconexiones SSH del tipo `Connection reset`).

Para solucionar esto de manera definitiva, debemos configurar **4 GB de memoria de intercambio (SWAP)** en el disco de estado sólido:

En la terminal de tu servidor (SSH):

```bash
# 1. Crear un archivo vacío de 4 GB para el Swap
sudo fallocate -l 4G /swapfile

# 2. Configurar los permisos correctos
sudo chmod 600 /swapfile

# 3. Formatear el archivo como área de intercambio
sudo mkswap /swapfile

# 4. Activar el Swap en el sistema
sudo swapon /swapfile

# 5. Hacer que el Swap se monte automáticamente al iniciar el servidor
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 6. Verificar que la memoria de intercambio esté activa (deberías ver "Swap: 4.0Gi")
free -h
```

---

## Paso 5: Subir o clonar el proyecto

### Opción A: clonar desde GitHub

```bash
cd /home/ubuntu
git clone https://github.com/TU_USUARIO/challenge-alura-agente.git
cd challenge-alura-rag
```

### Opción B: subir por SCP (Compresión ZIP recomendada)

Dado que la carpeta del entorno virtual local `env3.11` no debe copiarse al servidor (pesa mucho y no es compatible), la mejor estrategia es crear un archivo `.zip` excluyéndola, subirlo por SCP y extraerlo en el servidor.

**1. Desde tu PowerShell local (Windows), comprime el proyecto excluyendo `env3.11` y súbelo:**

```powershell
$sourceFolder = "D:\DevALURA\challenge-alura-agente\agente-alura-rag"
$instanceIP = "130.162.58.58"
$keyPath = "D:\DevALURA\challenge-alura-agente\ssh-keys\ssh-key-2026-07-10.key"

# Comprimir el proyecto local excluyendo env3.11
Get-ChildItem -Path $sourceFolder -Exclude "env3.11" | Compress-Archive -DestinationPath "D:\DevALURA\challenge-alura-agente\proyecto.zip" -Force

# Subir el archivo zip al servidor
scp -i $keyPath "D:\DevALURA\challenge-alura-agente\proyecto.zip" ubuntu@${instanceIP}:/home/ubuntu/
```

**2. Desde la terminal SSH de tu servidor (Ubuntu), instala unzip y descomprime:**

```bash
# Instalar unzip
sudo apt install -y unzip

# Descomprimir en la carpeta del agente
unzip /home/ubuntu/proyecto.zip -d /home/ubuntu/agente-alura-rag

# Eliminar el archivo zip temporal
rm /home/ubuntu/proyecto.zip
```

---

## Paso 6: Crear el entorno virtual

En la instancia remota:

```bash
cd /home/ubuntu/agente-alura-rag

# Si instalaste la versión por defecto de Python (Opción A):
python3 -m venv venv

# Si instalaste específicamente Python 3.11 (Opción B):
python3.11 -m venv venv

# Activar el entorno virtual e instalar las dependencias
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Paso 7: Configurar variables de entorno

```bash
nano .env
```

Ejemplo unificado que soporta Ollama, OpenAI y Gemini:

```env
APP_NAME="Exactus RAG Agent"
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO

# Proveedor por defecto de LLM y Embeddings
# Opciones: ollama, gemini, openai
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=openai

# Configuración de Ollama (Desarrollo Local)
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_LLM_MODEL=qwen2.5-coder:7b

# Configuración de OpenAI (Para alta velocidad con saldo prepagado)
OPENAI_API_KEY=tu_clave_de_openai_prepagada_aqui
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Configuración de Gemini
GEMINI_API_KEY=tu_clave_de_gemini_aqui
GEMINI_CHAT_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001

# Parámetros del RAG y Vectorstore
CHROMA_PERSIST_DIRECTORY=data/processed
DOCS_PATH=data/raw/exactus
TOP_K=4
CHUNK_SIZE=1200
CHUNK_OVERLAP=150
```

---

## Paso 8: Copiar los documentos

```bash
mkdir -p /home/ubuntu/agente-alura-rag/data/raw/exactus
mkdir -p /home/ubuntu/agente-alura-rag/data/processed
```

También puedes subir tus PDFs por SCP.

---

## Paso 9: Ingestar documentos (Evitando límites de cuota y auto-reanudando)

> [!IMPORTANT]
> **REGLA DE ORO DE CAMBIO DE EMBEDDINGS:**
> Si cambias el `EMBEDDING_PROVIDER` (por ejemplo, pasas de Gemini a OpenAI o viceversa), las dimensiones de los vectores cambian (OpenAI es 1,536 y Gemini 3,072). **Debes limpiar la base de datos vieja antes de indexar de nuevo** ejecutando en OCI:
> `rm -rf /home/ubuntu/agente-alura-rag/data/processed`

El sistema detecta automáticamente tu `EMBEDDING_PROVIDER` en el `.env` y ajusta las sub-divisiones (pacing) para evitar errores 429 de límite de cuota:

- **Con OpenAI (Prepago):** Procesa bloques grandes de 100 chunks y realiza pausas mínimas de 0.5s (indexa en segundos).
- **Con Gemini (Gratuito):** Procesa bloques pequeños de 50 chunks y espera 15 segundos entre ellos para mantenerse bajo el límite estricto de Tokens por Minuto (TPM) de Google.

Puedes elegir entre procesar todo el corpus o archivo por archivo:

### Opción A: Ingesta completa incremental

```bash
source venv/bin/activate
cd /home/ubuntu/agente-alura-rag
python -m scripts.ingest_incremental
```

### Opción B: Ingesta de un único PDF (Recomendado)

```bash
source venv/bin/activate
cd /home/ubuntu/agente-alura-rag
python -m scripts.ingest_pdf_incremental NOMBRE_DEL_ARCHIVO.pdf
```

### Opción C: Reanudar un manual interrumpido

Si la indexación de un manual grande se detuvo (por ejemplo, en el chunk 500), no tienes que volver a empezar desde cero ni perderás lo avanzado. Puedes reanudar la ingesta indicando el índice del chunk de inicio como segundo parámetro:

```bash
python -m scripts.ingest_pdf_incremental NOMBRE_DEL_ARCHIVO.pdf 500
```

_(Por ejemplo: `python -m scripts.ingest_pdf_incremental RH_Manual_Usuario_Recursos_Humanos.pdf 500`)_

---

## Paso 10: Ejecutar la API

```bash
source venv/bin/activate
cd /home/ubuntu/agente-alura-rag
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Paso 11: Configurar firewall y seguridad

Para acceder a la API desde internet, debes abrir el puerto 8000 tanto en la red de Oracle Cloud como en la máquina virtual (Ubuntu).

### A. Abrir los puertos en la consola de OCI

1. En **OCI Console**, ve a la página de detalles de tu instancia.
2. Haz clic en la **Subnet** asociada (en la sección _Primary VNIC_).
3. Haz clic en la **Default Security List** de la subred.
4. Haz clic en **Add Ingress Rules** y configura el puerto de la API (`8000`):
   - **Source Type:** CIDR
   - **Source CIDR:** `0.0.0.0/0` (para acceso público)
   - **IP Protocol:** TCP
   - **Destination Port Range:** `8000`
   - **Description:** Exactus RAG API
5. Haz clic de nuevo en **Add Ingress Rules** y configura el puerto de la Web de Streamlit (`8501`):
   - **Source Type:** CIDR
   - **Source CIDR:** `0.0.0.0/0`
   - **IP Protocol:** TCP
   - **Destination Port Range:** `8501`
   - **Description:** Exactus RAG Streamlit Web
6. Haz clic en **Add Ingress Rules** para guardar ambas reglas.

### B. Abrir los puertos en la máquina virtual (Ubuntu)

Las instancias de Ubuntu de Oracle Cloud Infrastructure vienen por defecto con configuraciones muy estrictas en `iptables` que bloquean puertos no estándar. Para garantizar que las reglas no sean bloqueadas por reglas restrictivas previas, insértalas al principio de la lista (**Posición 1**) ejecutando en tu terminal SSH:

```bash
# Permitir tráfico para la API (Puerto 8000)
sudo iptables -I INPUT 1 -p tcp --dport 8000 -j ACCEPT

# Permitir tráfico para la Web de Streamlit (Puerto 8501)
sudo iptables -I INPUT 1 -p tcp --dport 8501 -j ACCEPT

# Guardar las reglas para que persistan tras reiniciar la instancia
sudo netfilter-persistent save
```

_(Opcional) Si decides usar `ufw`, asegúrate de permitir SSH antes de habilitarlo para evitar quedar bloqueado:_

```bash
sudo ufw allow ssh
sudo ufw allow 8000/tcp
sudo ufw enable
sudo ufw status
```

---

## Paso 12: Validar el despliegue

```bash
curl http://130.162.58.58:8000/health
```

Prueba una pregunta de seguimiento con memoria conversacional usando OpenAI en OCI VM:

**Consulta RAG con Memoria Conversacional (OpenAI):**

```bash
curl -X POST http://130.162.58.58:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuáles son sus carpetas?",
    "chat_history": [
      {"role": "user", "content": "¿Cómo registrar un cliente nuevo?"},
      {"role": "assistant", "content": "Para registrar un cliente debes ir a la opción Clientes en el menú..."}
    ],
    "llm_provider": "openai",
    "llm_model": "gpt-4o-mini"
  }'
```

---

## Paso 13: Ejecutar como servicios systemd (Servicio persistente)

Para que la aplicación corra de forma ininterrumpida y se inicie automáticamente tras reiniciar la máquina virtual, se configuran dos servicios persistentes en segundo plano: uno para el Backend y otro para el Frontend.

### A. Servicio Backend: FastAPI

Crea el archivo de definición del backend:

```bash
sudo nano /etc/systemd/system/exactus-rag-backend.service
```

E ingresa el siguiente contenido:

```ini
[Unit]
Description=Exactus RAG Backend API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/agente-alura-rag
Environment="PATH=/home/ubuntu/agente-alura-rag/venv/bin"
ExecStart=/home/ubuntu/agente-alura-rag/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### B. Servicio Frontend: Streamlit

Crea el archivo de definición del frontend:

```bash
sudo nano /etc/systemd/system/exactus-rag-frontend.service
```

E ingresa el siguiente contenido (fijando `API_BASE_URL` apuntando al backend local de forma interna):

```ini
[Unit]
Description=Exactus RAG Frontend (Streamlit)
After=network.target exactus-rag-backend.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/agente-alura-rag
Environment="PATH=/home/ubuntu/agente-alura-rag/venv/bin"
Environment="API_BASE_URL=http://localhost:8000"
ExecStart=/home/ubuntu/agente-alura-rag/venv/bin/streamlit run frontend/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### C. Levantar y Habilitar los Servicios

Ejecuta los siguientes comandos para recargar el gestor de servicios, habilitar el arranque automático de ambos servicios y levantarlos en el servidor:

```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar el inicio con el encendido de la máquina virtual
sudo systemctl enable exactus-rag-backend.service exactus-rag-frontend.service

# Levantar/Reiniciar los servicios
sudo systemctl restart exactus-rag-backend.service exactus-rag-frontend.service

# Monitorear su estado
sudo systemctl status exactus-rag-backend.service exactus-rag-frontend.service
```

---

## Paso 14: Configurar SSL y Dominio Gratuito (DuckDNS + Caddy)

Para evitar acceder al RAG por direcciones IP desprotegidas y asegurar la conexión web con HTTPS gratuito, se utiliza **DuckDNS** (subdominio dinámico gratuito) y **Caddy Server** (como proxy inverso con emisión y renovación automática de certificados SSL Let's Encrypt).

### A. Registrar y Apuntar el Dominio

1. Crea una cuenta en [DuckDNS](https://www.duckdns.org/).
2. Registra un subdominio (ej. `challenge-alura.duckdns.org`).
3. En el panel de control de DuckDNS, reemplaza la IP actual con la IP pública de tu servidor OCI (`130.162.58.58`) y presiona **update ip**.

### B. Abrir Puertos Web (80 y 443)

1. **Consola Web de OCI:** En la _Default Security List_ de tu subred, añade dos reglas de ingreso para permitir tráfico TCP en los puertos **80** (HTTP) y **443** (HTTPS) desde cualquier origen (`0.0.0.0/0`).
2. **Máquina Virtual (Terminal SSH):** Ejecuta:
   ```bash
   sudo iptables -I INPUT 1 -p tcp --dport 80 -j ACCEPT
   sudo iptables -I INPUT 1 -p tcp --dport 443 -j ACCEPT
   sudo netfilter-persistent save
   ```

### C. Instalar Caddy Server en Ubuntu

Ejecuta la instalación oficial:

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy
```

### D. Configurar el Proxy Inverso (Caddyfile)

Edita el archivo de configuración en `/etc/caddy/Caddyfile`:

```bash
sudo nano /etc/caddy/Caddyfile
```

E ingresa el mapeo web:

```caddy
challenge-alura.duckdns.org {
    # Redirigir la API del backend
    reverse_proxy /api/* localhost:8000
    reverse_proxy /docs* localhost:8000
    reverse_proxy /openapi.json* localhost:8000
    reverse_proxy /health* localhost:8000

    # Redirigir todo lo demás al frontend Streamlit
    reverse_proxy localhost:8501
}
```

### E. Iniciar Caddy

Aplica los cambios reiniciando el servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable caddy
sudo systemctl restart caddy
```

Caddy solicitará de forma transparente el certificado SSL a Let's Encrypt. Una vez emitido, la interfaz de usuario estará completamente disponible y cifrada en:
👉 **`https://challenge-alura.duckdns.org`**

---

## Consideraciones de OCI Free Tier

- Es una opción más ligera que Docker
- Usa OpenAI si no quieres depender de Ollama local
- Revisa el tamaño del vectorstore en `data/processed/`

---

## Troubleshooting

### Dependencias no se instalan

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### La API no responde

```bash
ps aux | grep uvicorn
sudo journalctl -u exactus-rag -f
```

### Memoria insuficiente

Usa menor volumen de contexto y menos chunks:

```env
TOP_K=3
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

---

## Checklist final

- [x] Instancia OCI creada (`130.162.58.58`)
- [x] SSH funcionando con clave privada
- [x] Python 3 instalado
- [x] Memoria Swap de 4 GB configurada
- [x] Proyecto subido y descomprimido sin `env3.11`
- [x] `.env` configurado unificado (usando OpenAI o Gemini según proveedor)
- [x] PDFs cargados e indexados de forma incremental sin 429
- [x] API y Streamlit ejecutándose en segundo plano mediante Systemd
- [x] Firewall de OCI (Subnet Security List) abierto para puertos 8000 y 8501
- [x] Cortafuegos iptables abierto en Ubuntu VM para puertos 8000 y 8501
- [x] Endpoint `/health` respondiendo públicamente en `http://130.162.58.58:8000/health`
- [x] Web Streamlit accesible públicamente en `http://130.162.58.58:8501`

¡Listo para usar el despliegue sin Docker en OCI! 🎉
