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

Ejemplo real optimizado para Gemini en OCI:

```env
APP_NAME="Exactus RAG Agent"
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO

# Usamos Gemini para evitar el consumo de RAM de Ollama local
LLM_PROVIDER=gemini
EMBEDDING_PROVIDER=gemini

# Clave de API de Gemini y modelo de chat
GEMINI_API_KEY=AQ.Ab8RN6K9Mu6a8Xfm0nMGB1Ts_FyB9jtdxadIPfNBn7T7500NUg
GEMINI_CHAT_MODEL=gemini-2.5-flash

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

## Paso 9: Ingestar documentos (Evitando límites de cuota)

La cuenta gratuita de Gemini limita el número de solicitudes de embedding a **100 por minuto (100 RPM)**. Para evitar que el proceso falle por error `429 Quota Exceeded`, el proyecto incluye un script de **ingesta incremental** que divide los documentos en sub-lotes pequeños e incluye reintentos automáticos con espera (backoff exponencial).

Puedes elegir entre procesar todo el corpus de manera incremental o archivo por archivo:

### Opción A: Ingesta completa incremental

```bash
source venv/bin/activate
cd /home/ubuntu/agente-alura-rag
python -m scripts.ingest_incremental
```

### Opción B: Ingesta de un único PDF (Recomendado para control de progreso)

Si quieres procesar los PDFs uno por uno:

```bash
source venv/bin/activate
cd /home/ubuntu/agente-alura-rag
python -m scripts.ingest_pdf_incremental NOMBRE_DEL_ARCHIVO.pdf
```

_(Por ejemplo: `python -m scripts.ingest_pdf_incremental CI_Manual_Usuario_Control_Inventarios.pdf`)_

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

### A. Abrir el puerto en la consola de OCI

1. En **OCI Console**, ve a la página de detalles de tu instancia.
2. Haz clic en la **Subnet** asociada (en la sección _Primary VNIC_).
3. Haz clic en la **Default Security List** de la subred.
4. Haz clic en **Add Ingress Rules** y configura:
   - **Source Type:** CIDR
   - **Source CIDR:** `0.0.0.0/0` (para acceso público) o tu IP pública actual para mayor seguridad.
   - **IP Protocol:** TCP
   - **Source Port Range:** (dejar vacío o `All`)
   - **Destination Port Range:** `8000`
   - **Description:** Exactus RAG API
5. Haz clic en **Add Ingress Rules**.

### B. Abrir el puerto en la máquina virtual (Ubuntu)

Las instancias de Ubuntu de Oracle Cloud Infrastructure vienen por defecto con configuraciones muy estrictas en `iptables` que bloquean puertos no estándar. Para abrir el puerto 8000 de forma persistente, ejecuta en tu terminal SSH:

```bash
# Agregar la regla al puerto 8000 en iptables
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT

# Guardar la regla para que persista tras reiniciar la instancia
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

Prueba una pregunta:

```bash
curl -X POST http://130.162.58.58:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"¿Cómo crear un usuario en Exactus?","llm_provider":"gemini","llm_model":"gemini-2.5-flash"}'
```

---

## Paso 13: Ejecutar como servicio systemd (recomendado)

Para que el backend corra en segundo plano y se inicie automáticamente con el sistema:

```bash
sudo nano /etc/systemd/system/exactus-rag.service
```

Contenido (asegúrate de que las rutas al entorno virtual `venv` apunten a `/home/ubuntu/agente-alura-rag/venv/bin`):

```ini
[Unit]
Description=Exactus RAG Agent
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/agente-alura-rag
Environment="PATH=/home/ubuntu/agente-alura-rag/venv/bin"
ExecStart=/home/ubuntu/agente-alura-rag/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Inicia el servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable exactus-rag
sudo systemctl start exactus-rag
sudo systemctl status exactus-rag
```

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

- [ ] Instancia OCI creada (`130.162.58.58`)
- [ ] SSH funcionando con clave privada
- [ ] Python 3 instalado (Opción A: Python 3.12 por defecto en Ubuntu 24.04)
- [ ] Memoria Swap de 4 GB configurada
- [ ] Proyecto subido y descomprimido sin `env3.11`
- [ ] `.env` configurado para usar Gemini (`gemini-embedding-2`)
- [ ] PDFs cargados e indexados de forma incremental
- [ ] API ejecutándose en el puerto 8000
- [ ] Firewall de OCI (Subnet Security List) e `iptables` abiertos para el puerto 8000
- [ ] Endpoint `/health` respondiendo en `http://130.162.58.58:8000/health`

¡Listo para usar el despliegue sin Docker en OCI! 🎉
