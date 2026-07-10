# Guía de despliegue en Oracle OCI Free Tier con Docker

## Resumen ejecutivo

Esta guía cubre el despliegue del Agente RAG de Exactus en una instancia de **Oracle Cloud Infrastructure (OCI) Free Tier** usando **Docker**.

> Si prefieres desplegar sin Docker, consulta [docs/deploy-OCI.md](deploy-OCI.md).

## ¿Por qué Docker?

**Recomendación: Docker** ✅
- Encapsulación limpia y reproducible
- Evita mezclar dependencias en la VM
- Facilita mover el despliegue entre entornos
- Es una opción más profesional para un MVP o demo

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

```powershell
$instanceIP = "Tu.IP.Publica.Aqui"
$keyPath = "C:\ruta\a\clave.key"
ssh -i $keyPath ubuntu@$instanceIP
```

Actualiza el sistema:

```bash
sudo apt update && sudo apt upgrade -y
```

---

## Paso 3: Instalar Docker y Docker Compose

```bash
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu
newgrp docker

docker --version
docker-compose --version
```

---

## Paso 4: Subir o clonar el proyecto

### Opción A: clonar desde GitHub

```bash
cd /home/ubuntu
git clone https://github.com/TU_USUARIO/challenge-alura-agente.git
cd challenge-alura-agente/agente-alura-rag
```

### Opción B: subir por SCP

```powershell
$sourceFolder = "D:\DevALURA\challenge-alura-agente\agente-alura-rag"
$instanceIP = "Tu.IP.Publica.Aqui"
$keyPath = "C:\ruta\a\clave.key"

scp -r -i $keyPath "$sourceFolder\*" "ubuntu@${instanceIP}:/home/ubuntu/agente-alura-rag/"
```

---

## Paso 5: Configurar variables de entorno

```bash
cd /home/ubuntu/agente-alura-rag
nano .env
```

Ejemplo:

```env
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama

OLLAMA_LLM_MODEL=llama2
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

CHROMA_PERSIST_DIRECTORY=data/processed
DOCS_PATH=data/raw/exactus
TOP_K=5
CHUNK_SIZE=1000
CHUNK_OVERLAP=100

API_HOST=0.0.0.0
API_PORT=8000
```

---

## Paso 6: Copiar los documentos

```bash
mkdir -p /home/ubuntu/agente-alura-rag/data/raw/exactus
mkdir -p /home/ubuntu/agente-alura-rag/data/processed
```

Si lo prefieres, puedes subir los PDFs desde tu PC con SCP.

---

## Paso 7: Crear el archivo Docker Compose

```bash
nano docker-compose.yml
```

Contenido sugerido:

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

## Paso 8: Construir y levantar la app

```bash
cd /home/ubuntu/agente-alura-rag
docker build -t exactus-rag:latest .
docker-compose up -d

docker-compose logs -f
```

---

## Paso 9: Ingestar documentos

```bash
docker-compose exec api python -m scripts.ingest
```

---

## Paso 10: Configurar firewall y seguridad

En OCI, abre el puerto 8000 en la red o en el security list asociado a la instancia.

También puedes hacerlo desde la VM:

```bash
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
  -d '{"question":"¿Cómo crear un usuario en Exactus?","llm_provider":"ollama","llm_model":"llama2"}'
```

---

## Consideraciones de OCI Free Tier

- Ollama puede consumir bastante memoria
- Si tienes problemas, considera usar OpenAI para embeddings/chat
- Mantén control del tamaño de `data/processed/`

Ejemplo de configuración alternativa:

```env
EMBEDDING_PROVIDER=openai
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-3.5-turbo
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

---

## Troubleshooting

### Error de espacio en disco

```bash
docker system prune -a
du -sh /home/ubuntu/agente-alura-rag/*
```

### La API no responde

```bash
docker-compose ps
docker-compose logs api
```

### Memoria insuficiente

```bash
docker stats
```

---

## Checklist final

- [ ] Instancia OCI creada
- [ ] SSH funcionando
- [ ] Docker instalado
- [ ] Proyecto subido o clonado
- [ ] `.env` configurado
- [ ] PDFs cargados
- [ ] Contenedor corriendo
- [ ] API respondiendo en puerto 8000

¡Listo para usar el despliegue con Docker! 🎉
