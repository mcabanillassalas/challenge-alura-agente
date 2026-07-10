# Guía de despliegue en Oracle OCI Free Tier

## Resumen ejecutivo

Esta guía proporciona instrucciones paso a paso para desplegar el Agente RAG de Exactus en una instancia **Oracle Cloud Infrastructure (OCI) Free Tier**.

### ¿Docker o instalación directa?

**Recomendación: Docker** ✅
- Encapsulación limpia (no contamina la VM)
- Fácil de reproducir y versionar
- OCI Free Tier tiene suficiente memoria (1-2 GB disponibles)
- Despliegue más profesional
- Requiere ~300MB adicionales (aceptable)

**Alternativa**: Instalación directa sin Docker (ver sección final).

---

## 📋 Requisitos previos

- Cuenta Oracle Cloud Free Tier activa
- SSH configurado en tu máquina local
- Archivos de proyecto listos para subir
- PDFs de manuales de Exactus en `data/raw/exactus/`

---

## 🚀 PASO A PASO: Despliegue con Docker

### PASO 1: Crear instancia Compute en OCI

1. Ve a **Oracle Cloud Console** → **Compute** → **Instances**
2. Clic en **Create Instance**
3. Configura así:
   - **Imagen**: Ubuntu 22.04 (o 24.04)
   - **Shape**: Ampere (ARM-based) - es gratis si está en Free Tier
   - **OCPU**: 4 cores (gratis)
   - **Memoria**: 24 GB (gratis)
   - **Almacenamiento**: 200 GB (gratis, pero ojo con `data/processed/`)

4. **VCN y Subnet**: Crea una nueva o usa la existente
5. **Public IP**: Asigna una (importante para acceder)
6. **SSH Key**: Descarga la clave privada y guárdala localmente

En tu máquina local, asigna permisos a la clave (Windows):
```powershell
$keyPath = "C:\ruta\a\tu\clave.key"
icacls $keyPath /inheritance:r /grant:r "$env:USERNAME`:F"
```

---

### PASO 2: Conectar a la instancia por SSH

Desde PowerShell en tu PC:
```powershell
$instanceIP = "Tu.IP.Publica.Aqui"
$keyPath = "C:\ruta\a\clave.key"
ssh -i $keyPath ubuntu@$instanceIP
```

O en WSL/Git Bash:
```bash
ssh -i /path/to/key.key ubuntu@$instanceIP
```

Una vez conectado, actualiza el sistema:
```bash
sudo apt update && sudo apt upgrade -y
```

---

### PASO 3: Instalar Docker y Docker Compose

En la VM:
```bash
# Instalar Docker
sudo apt install -y docker.io docker-compose

# Agregar usuario ubuntu al grupo docker (sin sudo después)
sudo usermod -aG docker ubuntu

# Aplicar cambios
newgrp docker

# Verificar instalación
docker --version
docker-compose --version
```

---

### PASO 4: Clonar o subir el repositorio

#### Opción A: Clonar desde GitHub
```bash
cd /home/ubuntu
git clone https://github.com/TU_USUARIO/challenge-alura-agente.git
cd challenge-alura-agente/agente-alura-rag
```

#### Opción B: Subir archivos vía SCP desde tu PC

```powershell
# Desde PowerShell
$sourceFolder = "D:\DevALURA\challenge-alura-agente\agente-alura-rag"
$instanceIP = "Tu.IP.Publica.Aqui"
$keyPath = "C:\ruta\a\clave.key"

scp -r -i $keyPath "$sourceFolder\*" "ubuntu@${instanceIP}:/home/ubuntu/agente-alura-rag/"
```

---

### PASO 5: Configurar variables de entorno (.env)

En la VM:
```bash
cd /home/ubuntu/agente-alura-rag
nano .env
```

Añade o edita estas variables:
```env
# Proveedor por defecto
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama

# Modelos Ollama
OLLAMA_LLM_MODEL=llama2
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Alternativa: OpenAI (RECOMENDADO para embeddings en Free Tier)
# Descomentar si prefieres no usar Ollama
# EMBEDDING_PROVIDER=openai
# OPENAI_API_KEY=sk-...
# OPENAI_EMBEDDING_MODEL=text-embedding-3-small
# LLM_PROVIDER=openai
# OPENAI_CHAT_MODEL=gpt-3.5-turbo

# Rutas
CHROMA_PERSIST_DIRECTORY=data/processed
DOCS_PATH=data/raw/exactus
TOP_K=5
CHUNK_SIZE=1000
CHUNK_OVERLAP=100

# API
API_HOST=0.0.0.0
API_PORT=8000
```

Guarda con `Ctrl+X`, `Y`, `Enter`.

---

### PASO 6: Copiar documentos (PDFs)

#### Opción A: Vía SCP desde tu PC

```powershell
# Desde PowerShell
$sourceFolder = "D:\DevALURA\challenge-alura-agente\agente-alura-rag\data\raw\exactus"
$instanceIP = "Tu.IP.Publica.Aqui"
$keyPath = "C:\ruta\a\clave.key"

scp -r -i $keyPath "$sourceFolder\*" "ubuntu@${instanceIP}:/home/ubuntu/agente-alura-rag/data/raw/exactus/"
```

#### Opción B: Crear carpetas en OCI (carga manual después)

En la VM:
```bash
mkdir -p /home/ubuntu/agente-alura-rag/data/raw/exactus
mkdir -p /home/ubuntu/agente-alura-rag/data/processed
```

---

### PASO 7: Construir y ejecutar Docker

En la VM:
```bash
cd /home/ubuntu/agente-alura-rag

# Construir imagen Docker
docker build -t exactus-rag:latest .

# Ejecutar con docker-compose
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f
```

#### Si docker-compose.yml no existe

Crea el archivo:
```bash
nano docker-compose.yml
```

Contenido:
```yaml
version: '3.9'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./vectorstore:/app/vectorstore
    environment:
      - LLM_PROVIDER=${LLM_PROVIDER}
      - EMBEDDING_PROVIDER=${EMBEDDING_PROVIDER}
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - OPENAI_CHAT_MODEL=${OPENAI_CHAT_MODEL:-}
      - OPENAI_EMBEDDING_MODEL=${OPENAI_EMBEDDING_MODEL:-}
      - OLLAMA_LLM_MODEL=${OLLAMA_LLM_MODEL:-}
      - OLLAMA_EMBEDDING_MODEL=${OLLAMA_EMBEDDING_MODEL:-}
      - CHROMA_PERSIST_DIRECTORY=${CHROMA_PERSIST_DIRECTORY}
      - DOCS_PATH=${DOCS_PATH}
      - TOP_K=${TOP_K}
      - CHUNK_SIZE=${CHUNK_SIZE}
      - CHUNK_OVERLAP=${CHUNK_OVERLAP}
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    restart: unless-stopped
```

---

### PASO 8: Ingestar documentos

Una vez que el contenedor está corriendo:

#### Opción A: Script de ingesta dentro del contenedor
```bash
docker-compose exec api python -m scripts.ingest
```

#### Opción B: Hacer POST request a la API
```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -F "files=@data/raw/exactus/manual.pdf" \
  -F "embedding_provider=ollama" \
  -F "embedding_model=nomic-embed-text"
```

---

### PASO 9: Configurar firewall y seguridad

#### En la consola de OCI:

1. Ve a **Network** → **Network Security Groups** (o Security Lists)
2. Añade regla de entrada:
   - **Protocol**: TCP
   - **Source**: `0.0.0.0/0` (o tu IP específica para mayor seguridad)
   - **Destination Port**: `8000`

#### Alternativa: Configurar firewall en la VM

```bash
sudo ufw allow 8000/tcp
sudo ufw enable
sudo ufw status
```

---

### PASO 10: Pruebas de conectividad

```bash
# Prueba del endpoint de salud
curl http://TU_IP_PUBLICA:8000/health

# Respuesta esperada:
# {"status":"ok"}
```

Desde tu PC (PowerShell):
```powershell
Invoke-WebRequest -Uri "http://Tu.IP.Publica:8000/health"
```

---

### PASO 11: Hacer preguntas al agente

```bash
# Desde la VM o tu PC
curl -X POST http://TU_IP_PUBLICA:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cómo crear un usuario en Exactus?",
    "llm_provider": "ollama",
    "llm_model": "llama2"
  }'
```

O desde PowerShell:
```powershell
$body = @{
    question = "¿Cómo crear un usuario en Exactus?"
    llm_provider = "ollama"
    llm_model = "llama2"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://Tu.IP.Publica:8000/api/v1/ask" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body
```

---

## ⚠️ Consideraciones especiales para OCI Free Tier

### Problema 1: Memoria insuficiente para Ollama

Ollama consume ~4GB en memoria. OCI Free Tier tiene suficiente, pero si hay problemas:

```env
# Usa OpenAI en su lugar (más económico)
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...
LLM_PROVIDER=openai
OPENAI_CHAT_MODEL=gpt-3.5-turbo
```

**Costo aproximado**: $0-2 USD/mes si mantienes bajo volumen.

### Problema 2: Vectorstore demasiado grande

Si `data/processed/` crece demasiado (Free Tier = 200GB):

```bash
# Monitorear tamaño
du -sh /home/ubuntu/agente-alura-rag/data/processed/

# Limpiar Chroma si es necesario
rm -rf /home/ubuntu/agente-alura-rag/data/processed/*

# Reconstruir índice
docker-compose exec api python -m scripts.rebuild_index
```

### Problema 3: Contenedor muere por falta de memoria

```bash
# Ver uso de memoria en tiempo real
docker stats
```

Si hay problemas, edita `docker-compose.yml` para limitar recursos:
```yaml
services:
  api:
    mem_limit: 1024m
    memswap_limit: 2048m
```

### Problema 4: Ollama requiere mucho almacenamiento

Cada modelo de Ollama ocupa 4-7GB. En Free Tier con 200GB:
- Llama2: ~7GB
- Nomic-embed-text: ~275MB
- Otros modelos: 4-13GB

**Solución**: Usa solo OpenAI para embeddings (no requiere almacenamiento local):
```env
EMBEDDING_PROVIDER=openai
LLM_PROVIDER=ollama  # O también openai
```

---

## 📊 Costos esperados en OCI Free Tier

| Recurso | Gratis | Cuota |
|---------|--------|-------|
| Compute (Ampere) | ✅ | 4 OCPU + 24 GB RAM |
| Block Storage | ✅ | 200 GB |
| Bandwidth saliente | ✅ | 10 TB/mes |
| Database (opcional) | ✅ | Algunos tipos |

**Costo total esperado**: $0 si mantienes todo dentro de Free Tier.

---

## 🔄 ALTERNATIVA: Instalación directa sin Docker

Si prefieres no usar Docker:

### Instalar Python y dependencias

```bash
# Instalar Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip build-essential

# Crear entorno virtual
python3.11 -m venv /home/ubuntu/venv

# Activar entorno
source /home/ubuntu/venv/bin/activate

# Instalar dependencias
cd /home/ubuntu/agente-alura-rag
pip install --upgrade pip
pip install -r requirements.txt
```

### Ejecutar API

```bash
source /home/ubuntu/venv/bin/activate
cd /home/ubuntu/agente-alura-rag
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Ejecutar como servicio systemd (opcional)

Crea archivo de servicio:
```bash
sudo nano /etc/systemd/system/exactus-rag.service
```

Contenido:
```ini
[Unit]
Description=Exactus RAG Agent
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/agente-alura-rag
Environment="PATH=/home/ubuntu/venv/bin"
ExecStart=/home/ubuntu/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
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

**Ventaja**: Menos overhead de recursos.
**Desventaja**: Más frágil ante actualizaciones de dependencias.

---

## ✅ Checklist final

- [ ] Instancia OCI creada con Ubuntu 22.04+
- [ ] Conexión SSH funcionando
- [ ] Docker instalado y verificado
- [ ] Repositorio clonado o archivos subidos
- [ ] `.env` configurado con variables correctas
- [ ] PDFs ubicados en `data/raw/exactus/`
- [ ] `docker-compose.yml` presente y válido
- [ ] Imagen Docker construida sin errores
- [ ] Contenedor corriendo (`docker-compose up -d`)
- [ ] Documentos ingestados correctamente
- [ ] API responde en puerto 8000
- [ ] Firewall abierto para puerto 8000 en OCI
- [ ] `GET /health` retorna 200 OK
- [ ] `POST /api/v1/ask` responde preguntas correctamente
- [ ] Logs disponibles sin errores críticos

---

## 🔧 Troubleshooting

### Error: "No space left on device"
```bash
# Limpia el almacenamiento de Docker
docker system prune -a
du -sh /home/ubuntu/agente-alura-rag/*
```

### Error: "Connection refused"
```bash
# Verifica que el contenedor está corriendo
docker-compose ps

# Verifica logs
docker-compose logs api

# Reinicia
docker-compose restart
```

### Error: "Out of memory"
```bash
# Reduce modelos o usa OpenAI para embeddings
# Ver sección de Problema 1 arriba
```

### No puedo conectar a la API desde mi PC
```bash
# 1. Verifica la IP pública en OCI Console
# 2. Verifica firewall: sudo ufw status
# 3. Verifica Network Security Group en OCI
# 4. Prueba desde dentro de la VM: curl localhost:8000/health
```

---

## 📞 Recursos útiles

- [OCI Documentation](https://docs.oracle.com/en-us/iaas/)
- [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/)
- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://python.langchain.com/)

---

## Notas finales

- Siempre mantén backups de `data/processed/` (vectorstore)
- Monitorea el uso de almacenamiento regularmente
- Considera usar herramientas como `screen` o `tmux` para procesos de larga duración
- Para producción, considera usar certificados SSL (Let's Encrypt + Nginx)

¡Listo para desplegar! 🎉
