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
- SSH configurado en tu máquina local
- Archivos del proyecto listos para subir
- PDFs de Exactus en la carpeta `data/raw/exactus/`

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

\`\`\`powershell
$instanceIP = "Tu.IP.Publica.Aqui"
$keyPath = "C:\ruta\a\clave.key"
ssh -i $keyPath ubuntu@$instanceIP
\`\`\`

Actualiza el sistema:

\`\`\`bash
sudo apt update && sudo apt upgrade -y
\`\`\`

---

## Paso 3: Instalar Python y dependencias

\`\`\`bash
sudo apt install -y python3.11 python3.11-venv python3-pip build-essential git
python3.11 --version
pip3 --version
\`\`\`

---

## Paso 4: Subir o clonar el proyecto

### Opción A: clonar desde GitHub

\`\`\`bash
cd /home/ubuntu
git clone https://github.com/TU_USUARIO/challenge-alura-agente.git
cd challenge-alura-rag
\`\`\`

### Opción B: subir por SCP

\`\`\`powershell
$sourceFolder = "D:\DevALURA\challenge-alura-agente\agente-alura-rag"
$instanceIP = "Tu.IP.Publica.Aqui"
$keyPath = "C:\ruta\a\clave.key"

scp -r -i $keyPath "$sourceFolder\*" "ubuntu@${instanceIP}:/home/ubuntu/agente-alura-rag/"
\`\`\`

---

## Paso 5: Crear el entorno virtual

\`\`\`bash
cd /home/ubuntu/agente-alura-rag
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
\`\`\`

---

## Paso 6: Configurar variables de entorno

\`\`\`bash
nano .env
\`\`\`

Ejemplo:

\`\`\`env
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
\`\`\`

---

## Paso 7: Copiar los documentos

\`\`\`bash
mkdir -p /home/ubuntu/agente-alura-rag/data/raw/exactus
mkdir -p /home/ubuntu/agente-alura-rag/data/processed
\`\`\`

También puedes subir tus PDFs por SCP.

---

## Paso 8: Ingestar documentos

\`\`\`bash
source venv/bin/activate
cd /home/ubuntu/agente-alura-rag
python -m scripts.ingest
\`\`\`

---

## Paso 9: Ejecutar la API

\`\`\`bash
source venv/bin/activate
cd /home/ubuntu/agente-alura-rag
uvicorn app.main:app --host 0.0.0.0 --port 8000
\`\`\`

---

## Paso 10: Configurar firewall y seguridad

En OCI, abre el puerto 8000 en la red o en el security list asociado a la instancia.

También puedes hacerlo desde la VM:

\`\`\`bash
sudo ufw allow 8000/tcp
sudo ufw enable
sudo ufw status
\`\`\`

---

## Paso 11: Validar el despliegue

\`\`\`bash
curl http://TU_IP_PUBLICA:8000/health
\`\`\`

Prueba una pregunta:

\`\`\`bash
curl -X POST http://TU_IP_PUBLICA:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"¿Cómo crear un usuario en Exactus?","llm_provider":"openai","llm_model":"gpt-3.5-turbo"}'
\`\`\`

---

## Paso 12: Ejecutar como servicio systemd (recomendado)

\`\`\`bash
sudo nano /etc/systemd/system/exactus-rag.service
\`\`\`

Contenido:

\`\`\`ini
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
\`\`\`

Inicia el servicio:

\`\`\`bash
sudo systemctl daemon-reload
sudo systemctl enable exactus-rag
sudo systemctl start exactus-rag
sudo systemctl status exactus-rag
\`\`\`

---

## Consideraciones de OCI Free Tier

- Es una opción más ligera que Docker
- Usa OpenAI si no quieres depender de Ollama local
- Revisa el tamaño del vectorstore en `data/processed/`

---

## Troubleshooting

### Dependencias no se instalan

\`\`\`bash
pip install --upgrade pip
pip install -r requirements.txt
\`\`\`

### La API no responde

\`\`\`bash
ps aux | grep uvicorn
sudo journalctl -u exactus-rag -f
\`\`\`

### Memoria insuficiente

Usa menor volumen de contexto y menos chunks:

\`\`\`env
TOP_K=3
CHUNK_SIZE=500
CHUNK_OVERLAP=50
\`\`\`

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