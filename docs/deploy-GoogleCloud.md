# Guía de despliegue en Google Cloud Platform (GCP)

## Resumen ejecutivo

Esta guía proporciona instrucciones paso a paso para desplegar el Agente RAG de Exactus en **Google Cloud Platform (GCP)** usando Compute Engine y Free Tier.

### Ventajas de GCP Free Tier vs OCI

| Característica | GCP Free Tier | OCI Free Tier |
|---|---|---|
| Período gratis | 12 meses | Indefinido |
| Compute Engine | e2-micro (0.25 vCPU, 1GB RAM) | 4 OCPU, 24 GB RAM |
| Almacenamiento | 30 GB SSD | 200 GB |
| Recomendación | Para MVP/pruebas | Para producción pequeña |

**Recomendación**: GCP es mejor para MVP; OCI es mejor si necesitas más recursos permanentes.

### ¿Docker o instalación directa?

**Recomendación: Instalación directa** ✅ (GCP Free Tier es muy limitado)
- GCP Free Tier = 0.25 vCPU + 1GB RAM (muy justo para Docker)
- Docker agrega ~300MB overhead
- Mejor rendimiento sin Docker en e2-micro

**Alternativa**: Docker si escalas a e2-standard (costo mínimo).

---

## 📋 Requisitos previos

- Cuenta Google Cloud Free Tier activa (con crédito inicial)
- Proyecto GCP creado
- SSH configurado en tu máquina local
- Archivos de proyecto listos para subir
- PDFs de manuales de Exactus en `data/raw/exactus/`

---

## 🚀 PASO A PASO: Despliegue en GCP (sin Docker - Recomendado)

### PASO 1: Crear instancia Compute Engine en GCP

1. Ve a **Google Cloud Console** → **Compute Engine** → **Instances**
2. Clic en **Create Instance**
3. Configura así:
   - **Name**: `exactus-rag-agent` (o como prefieras)
   - **Region**: Selecciona cercana a ti (ej: `us-central1`, `southamerica-east1` si estás en LATAM)
   - **Zone**: `a` o `b` dentro de la región
   - **Machine type**: `e2-micro` (gratis 12 meses) o `e2-small` si necesitas más potencia
   - **CPU Platform**: Cualquiera (auto-selected)
   - **Boot disk**: Ubuntu 22.04 LTS (200GB - gratis en Free Tier)
   - **Allow HTTP traffic**: ✅ Sí
   - **Allow HTTPS traffic**: ✅ Sí

4. Clic en **Create**

#### Nota: ¿Necesitas más potencia?

Si `e2-micro` es lento (1GB RAM es muy poco), escala a:
- `e2-small`: 0.5 vCPU, 2GB RAM (~$13/mes fuera de Free Tier)
- `e2-medium`: 1 vCPU, 4GB RAM (~$26/mes fuera de Free Tier)

---

### PASO 2: Obtener IP externa y conectar por SSH

1. En Google Cloud Console, bajo **Compute Engine** → **Instances**, copia la **External IP**

2. Desde PowerShell en tu PC:
```powershell
$instanceIP = "Tu.IP.Externa.Aqui"
gcloud compute ssh exactus-rag-agent --zone=us-central1-a
```

O conexión manual SSH:
```powershell
# Generar clave SSH local si no la tienes
gcloud compute config-ssh

# Luego conectar
ssh -i $env:USERPROFILE\.ssh\google_compute_engine Tu.IP.Externa.Aqui
```

Una vez conectado, actualiza el sistema:
```bash
sudo apt update && sudo apt upgrade -y
```

---

### PASO 3: Instalar dependencias de Python

En la VM:
```bash
# Instalar Python 3.11 y herramientas
sudo apt install -y python3.11 python3.11-venv python3-pip build-essential git

# Verificar instalación
python3.11 --version
pip3 --version
```

---

### PASO 4: Clonar o subir el repositorio

#### Opción A: Clonar desde GitHub
```bash
cd /home/$USER
git clone https://github.com/TU_USUARIO/challenge-alura-agente.git
cd challenge-alura-agente/agente-alura-rag
```

#### Opción B: Subir archivos vía SCP desde tu PC

```powershell
# Desde PowerShell
$sourceFolder = "D:\DevALURA\challenge-alura-agente\agente-alura-rag"
$instanceIP = "Tu.IP.Externa.Aqui"

scp -r "$sourceFolder\*" "${instanceIP}:~/agente-alura-rag/"
```

---

### PASO 5: Crear entorno virtual Python

En la VM:
```bash
cd ~/agente-alura-rag

# Crear venv
python3.11 -m venv venv

# Activar
source venv/bin/activate

# Verificar
which python
python --version
```

---

### PASO 6: Instalar dependencias del proyecto

```bash
# Asegúrate de estar en el venv activado
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Instalar requirements
pip install -r requirements.txt

# Verificar instalación
pip list | grep -E "langchain|fastapi|chroma"
```

---

### PASO 7: Configurar variables de entorno (.env)

```bash
nano ~/agente-alura-rag/.env
```

Añade estas variables:
```env
# Proveedor recomendado para GCP Free Tier: OpenAI (sin dependencias locales)
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=openai

# Claves de OpenAI
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-3.5-turbo
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

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

**⚠️ Nota**: Si usas Ollama, necesitarás instalar Docker además, lo que consume recursos. **No recomendado en e2-micro**.

Guarda con `Ctrl+X`, `Y`, `Enter`.

---

### PASO 8: Copiar documentos (PDFs)

#### Opción A: Vía SCP desde tu PC

```powershell
# Desde PowerShell
$sourceFolder = "D:\DevALURA\challenge-alura-agente\agente-alura-rag\data\raw\exactus"
$instanceIP = "Tu.IP.Externa.Aqui"

scp -r "$sourceFolder\*" "${instanceIP}:~/agente-alura-rag/data/raw/exactus/"
```

#### Opción B: Crear carpetas y cargar manualmente

```bash
mkdir -p ~/agente-alura-rag/data/raw/exactus
mkdir -p ~/agente-alura-rag/data/processed
```

---

### PASO 9: Ingestar documentos

En la VM:
```bash
source venv/bin/activate
cd ~/agente-alura-rag

# Ejecutar script de ingesta
python -m scripts.ingest
```

O manualmente si prefieres:
```bash
# Esperar a que la API esté corriendo (siguiente paso)
# Luego desde tu PC:
curl -X POST http://Tu.IP.Externa:8000/api/v1/ingest \
  -F "files=@data/raw/exactus/manual.pdf" \
  -F "embedding_provider=openai" \
  -F "embedding_model=text-embedding-3-small"
```

---

### PASO 10: Ejecutar la API

En la VM:
```bash
source venv/bin/activate
cd ~/agente-alura-rag

# Ejecutar Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Verás logs como:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### PASO 11: Configurar Firewall en GCP

1. Ve a **VPC Network** → **Firewall rules**
2. Clic en **Create Firewall Rule**
3. Configura:
   - **Name**: `allow-exactus-rag`
   - **Direction**: Ingress
   - **Action**: Allow
   - **Protocol/Port**: TCP, puerto 8000
   - **Source IP ranges**: `0.0.0.0/0` (o tu IP específica)
   - **Target tags**: (opcional) o deja en blanco

4. Clic en **Create**

---

### PASO 12: Pruebas de conectividad

```bash
# Prueba del endpoint de salud
curl http://Tu.IP.Externa:8000/health

# Respuesta esperada:
# {"status":"ok"}
```

Desde tu PC (PowerShell):
```powershell
Invoke-WebRequest -Uri "http://Tu.IP.Externa:8000/health"
```

---

### PASO 13: Ejecutar la API como servicio systemd (para persistencia)

Para que la API se ejecute incluso después de desconectar SSH:

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
User=$USER
WorkingDirectory=/home/$USER/agente-alura-rag
Environment="PATH=/home/$USER/agente-alura-rag/venv/bin"
ExecStart=/home/$USER/agente-alura-rag/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Reemplaza `$USER` con tu usuario (ej: `usuario`):
```bash
sudo nano /etc/systemd/system/exactus-rag.service
# Edita manualmente o usa sed:
sudo sed -i 's|\$USER|'$USER'|g' /etc/systemd/system/exactus-rag.service
```

Inicia el servicio:
```bash
sudo systemctl daemon-reload
sudo systemctl enable exactus-rag
sudo systemctl start exactus-rag
sudo systemctl status exactus-rag

# Ver logs en tiempo real
sudo journalctl -u exactus-rag -f
```

---

### PASO 14: Hacer preguntas al agente

```bash
# Desde la VM o tu PC
curl -X POST http://Tu.IP.Externa:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cómo crear un usuario en Exactus?",
    "llm_provider": "openai",
    "llm_model": "gpt-3.5-turbo"
  }'
```

O desde PowerShell:
```powershell
$body = @{
    question = "¿Cómo crear un usuario en Exactus?"
    llm_provider = "openai"
    llm_model = "gpt-3.5-turbo"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://Tu.IP.Externa:8000/api/v1/ask" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body
```

---

## ⚠️ Consideraciones especiales para GCP Free Tier

### Problema 1: e2-micro es muy lento (0.25 vCPU, 1GB RAM)

**Síntomas**: Tiempos de respuesta lentos (>10 segundos).

**Solución**:
- Usa OpenAI para chat (no Ollama local)
- Limita TOP_K a 3-5
- Usa chunks más pequeños (CHUNK_SIZE=500)
- Escala a e2-small si lo necesitas (~$13/mes)

```env
# Configuración optimizada para e2-micro
TOP_K=3
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

### Problema 2: Almacenamiento limitado (30GB gratis)

```bash
# Monitorear uso
df -h

# Limpiar si es necesario
du -sh ~/agente-alura-rag/data/*
rm -rf ~/agente-alura-rag/data/processed/*
python -m scripts.rebuild_index
```

### Problema 3: Costo de OpenAI

Embeddings de `text-embedding-3-small`: ~$0.02 USD por 1M tokens.
Chat `gpt-3.5-turbo`: ~$0.5-1 USD por 1M tokens.

**Estimado mensual**: $2-5 USD si haces ~100 consultas/mes.

**Alternativa gratuita**: Usa Ollama local en e2-small ($13/mes) y ahorras en OpenAI.

### Problema 4: No puedo conectar a la instancia

```bash
# Desde GCP Console, abre Cloud Shell (>_ icono)
gcloud compute ssh exactus-rag-agent --zone=us-central1-a

# O verifica SSH keys
gcloud compute project-info describe --format='value(commonInstanceMetadata[ssh-keys])'
```

---

## 🔄 ALTERNATIVA: Despliegue con Docker en GCP

Si escalas a `e2-small` o superior, puedes usar Docker:

### Instalar Docker

```bash
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER
newgrp docker
```

### Seguir los pasos del documento deploy-OCI.md

Los pasos son muy similares. Simplemente reemplaza:
- IP local por la externa de GCP
- Configuración de firewall según GCP

---

## 📊 Costos esperados en GCP Free Tier

| Recurso | Gratis | Costo adicional |
|---------|--------|---|
| Compute Engine e2-micro | ✅ 12 meses | $0 después ($12-15/mes si escalas) |
| Storage (30GB) | ✅ | $0.020/GB mes (después de 30GB) |
| Bandwidth saliente | $0.12/GB | $0.12/GB (primeros 100GB gratis) |
| OpenAI API | No | $0.02-0.5/1M tokens |

**Costo total esperado**: 
- Con Free Tier: $0 (solo API keys pagadas)
- Después de 12 meses: $12-20/mes + OpenAI

---

## ✅ Checklist final

- [ ] Instancia Compute Engine creada (e2-micro o superior)
- [ ] Conexión SSH funcionando desde tu PC
- [ ] Python 3.11 instalado en la VM
- [ ] Git instalado
- [ ] Repositorio clonado o archivos subidos
- [ ] Entorno virtual Python creado y activado
- [ ] `requirements.txt` instalado sin errores
- [ ] `.env` configurado con API keys válidas
- [ ] PDFs ubicados en `data/raw/exactus/`
- [ ] Script de ingesta ejecutado correctamente
- [ ] Firewall de GCP abierto para puerto 8000
- [ ] API ejecutándose (`uvicorn` corriendo)
- [ ] `GET /health` retorna 200 OK
- [ ] `POST /api/v1/ask` responde preguntas correctamente
- [ ] Servicio systemd configurado y corriendo
- [ ] Logs disponibles sin errores críticos

---

## 🔧 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'langchain'"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Error: "Connection refused"
```bash
# Verifica que la API está corriendo
ps aux | grep uvicorn

# Si no, inicia
source venv/bin/activate
cd ~/agente-alura-rag
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```

### Error: "Invalid API key" (OpenAI)
```bash
# Verifica que la clave está en .env
cat ~/.env | grep OPENAI_API_KEY

# Actualiza si es necesario
nano ~/.env
```

### La API es muy lenta
```bash
# Verifica recursos disponibles
free -h
top

# Reduce configuración
# En .env: TOP_K=3, CHUNK_SIZE=500

# O escala a e2-small en GCP Console
```

### SSH se desconecta después de inactividad
```bash
# Usa screen para sesiones persistentes
screen -S rag-api
# Dentro de screen: source venv/bin/activate && uvicorn ...
# Presiona Ctrl+A, Ctrl+D para detach

# Listar sesiones
screen -ls

# Volver a sesión
screen -r rag-api
```

---

## 📞 Recursos útiles

- [Google Cloud Console](https://console.cloud.google.com)
- [GCP Compute Engine Docs](https://cloud.google.com/compute/docs)
- [GCP Free Tier](https://cloud.google.com/free)
- [gcloud CLI Reference](https://cloud.google.com/sdk/gcloud/reference)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

## Comparativa: OCI vs GCP

| Aspecto | OCI Free Tier | GCP Free Tier |
|---|---|---|
| Recursos gratis | Indefinido | 12 meses |
| Compute | 4 OCPU, 24GB RAM | 0.25 vCPU, 1GB RAM |
| Almacenamiento | 200GB | 30GB |
| Mejor para | Producción pequeña | MVP/Pruebas |
| Costo después | $0 (si mantienes límites) | $12-20/mes |
| Recomendación | Si necesitas recursos fijos | Si quieres probar primero |

---

## Notas finales

- **GCP es mejor para MVP rápido**, OCI es mejor para producción pequeña estable
- Monitorea costos en **Billing** de GCP (especialmente OpenAI)
- Mantén backups de `data/processed/` (vectorstore)
- Para mejor rendimiento en Free Tier, considera Ollama local en escalado posterior
- Usa Cloud Monitoring de GCP para alertas de CPU/memoria

¡Listo para desplegar en GCP! 🎉
