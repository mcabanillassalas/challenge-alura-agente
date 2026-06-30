# Notas de despliegue OCI

## Objetivo

Desplegar la aplicación en una instancia OCI Compute Free Tier usando Docker.

## Nota

Si en OCI no se desea usar Ollama, se puede dejar `EMBEDDING_PROVIDER=openai` para evitar dependencias locales de modelo.

## Pasos generales

1. Crear VM Ubuntu en OCI.
2. Instalar Docker y Docker Compose.
3. Clonar el repositorio.
4. Configurar `.env`.
5. Copiar los PDFs a `data/raw/exactus/`.
6. Ejecutar la ingesta.
7. Levantar la API con Docker Compose.
