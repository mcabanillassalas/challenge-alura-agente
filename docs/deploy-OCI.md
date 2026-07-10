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

Desde PowerShell:

```powershell
$instanceIP = "Tu.IP.Publica.Aqui"
# Si usaste la ruta de generación por defecto:
$keyPath = "$HOME\.ssh\id_rsa_oci"
# O especifica tu ruta personalizada si la guardaste en otro lugar:
# $keyPath = "C:\ruta\a\clave.key"
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

## Paso 4: Subir o clonar el proyecto

### Opción A: clonar desde GitHub

```bash
cd /home/ubuntu
git clone https://github.com/TU_USUARIO/challenge-alura-agente.git
cd challenge-alura-rag
```

### Opción B: subir por SCP

Desde tu PowerShell local:

```powershell
$sourceFolder = "D:\DevALURA\challenge-alura-agente\agente-alura-rag"
$instanceIP = "Tu.IP.Publica.Aqui"
$keyPath = "$HOME\.ssh\id_rsa_oci"

# Crear primero el directorio destino remoto para evitar fallos de copia
ssh -i $keyPath ubuntu@$instanceIP "mkdir -p /home/ubuntu/agente-alura-rag"

# Subir los archivos recursivamente
scp -r -i $keyPath "$sourceFolder\*" "ubuntu@${instanceIP}:/home/ubuntu/agente-alura-rag/"
```

---

## Paso 5: Crear el entorno virtual

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

## Paso 6: Configurar variables de entorno

```bash
nano .env
```

Ejemplo:

```env
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=openai

OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-3.5-turbo
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

CHROMA_PERSIST_DIRECTORY=data/processed
DOCS_PATH=data/raw/exactus
TOP_K=5
CHUNK_SIZE=1000
CHUNK_OVERLAP=100

API_HOST=0.0.0.0
API_PORT=8000
```

---

## Paso 7: Copiar los documentos

```bash
mkdir -p /home/ubuntu/agente-alura-rag/data/raw/exactus
mkdir -p /home/ubuntu/agente-alura-rag/data/processed
```

También puedes subir tus PDFs por SCP.

---

## Paso 8: Ingestar documentos

```bash
source venv/bin/activate
cd /home/ubuntu/agente-alura-rag
python -m scripts.ingest
```

---

## Paso 9: Ejecutar la API

```bash
source venv/bin/activate
cd /home/ubuntu/agente-alura-rag
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Paso 10: Configurar firewall y seguridad

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

## Paso 11: Validar el despliegue

```bash
curl http://TU_IP_PUBLICA:8000/health
```

Prueba una pregunta:

```bash
curl -X POST http://TU_IP_PUBLICA:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"¿Cómo crear un usuario en Exactus?","llm_provider":"openai","llm_model":"gpt-3.5-turbo"}'
```

---

## Paso 12: Ejecutar como servicio systemd (recomendado)

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

- [ ] Instancia OCI creada
- [ ] SSH funcionando
- [ ] Python 3.11 instalado
- [ ] Proyecto subido o clonado
- [ ] `.env` configurado
- [ ] PDFs cargados
- [ ] API ejecutándose en puerto 8000
- [ ] Firewall abierto
- [ ] Endpoint `/health` respondiendo

¡Listo para usar el despliegue sin Docker! 🎉
