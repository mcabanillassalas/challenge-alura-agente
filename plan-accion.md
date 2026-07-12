# Plan de acción para el Agente IA sobre manuales PDF de Exactus

## Objetivo del proyecto

Desarrollar un agente de inteligencia artificial en Python y LangChain capaz de leer manuales PDF del ERP Exactus, responder preguntas en lenguaje natural sobre su contenido y posteriormente desplegar la solución en OCI Free Tier. Este enfoque está alineado con el challenge, que exige procesar documentos PDF o CSV, responder preguntas sobre ellos y demostrar el despliegue en OCI.[file:1][file:4]

## Alcance inicial

La primera versión del proyecto se enfocará en un conjunto controlado de manuales PDF de Exactus, con el fin de construir un MVP funcional antes de ampliar cobertura. El reto recomienda empezar por un agente local funcional y solo después pasar al despliegue en la nube.[file:1]

### Alcance del MVP

- Procesar entre 2 y 5 manuales PDF de Exactus.
- Extraer texto y dividirlo en fragmentos utilizables para búsqueda semántica.
- Crear un índice vectorial local.
- Responder preguntas en lenguaje natural sobre procesos, configuraciones y uso del ERP.
- Exponer el agente mediante una API mínima.
- Preparar el proyecto para despliegue posterior en OCI.

### Fuera del alcance del MVP

- Interfaz visual compleja.
- Autenticación avanzada.
- OCR de documentos escaneados como prioridad inicial.
- Soporte multiusuario.
- Integración directa con la base de datos del ERP.

## Enfoque técnico recomendado

La solución se construirá con Python, LangChain, procesamiento de PDF y una base vectorial local, porque esas tecnologías encajan con las sugeridas por el challenge y permiten una implementación progresiva desde local hacia OCI.[file:1]

### Stack sugerido

- Python 3.11.
- FastAPI para la API local.
- LangChain para la cadena RAG.
- `pypdf` para lectura de PDFs.[file:1]
- Chroma o FAISS como vector store local.
- OpenAI o Cohere para el MVP inicial; Gemma como mejora posterior, ya que el reto permite cualquiera de estas opciones.[file:1]
- Docker para empaquetado y despliegue.
- OCI Compute Free Tier para publicación final.[file:1][file:4]

## Fases del proyecto

## Fase 1. Definición del alcance

Objetivo: seleccionar los manuales Exactus y definir qué tipo de preguntas debe responder el agente.

### Tareas

- Identificar los manuales PDF prioritarios.
- Agruparlos por módulo o tema.
- Elaborar una lista inicial de 20 a 30 preguntas objetivo.
- Definir criterios de éxito para las respuestas.

### Entregables

- Carpeta inicial `data/raw/exactus/` con los PDFs.
- Documento `docs/questions.md` con preguntas de prueba.
- Lista de módulos cubiertos por el MVP.

### Criterio de cierre

La fase se considera cerrada cuando ya existe un subconjunto acotado de manuales y una batería inicial de preguntas para validar el comportamiento del agente.

## Fase 2. Ingesta documental

Objetivo: extraer el contenido de los PDFs y dejarlo listo para indexación.

### Tareas

- Implementar lectura de PDFs.
- Normalizar texto extraído.
- Dividir el contenido en fragmentos o chunks.
- Incorporar metadatos como nombre del archivo y página.
- Indexar de forma incremental los archivos recién cargados desde el frontend.
- Permitir reindexación manual desde el frontend con el mismo proveedor y modelo de carga.
- Agregar metadatos de manual para favorecer la recuperación por tema y por módulo.
- Mantener el mapeo temático editable en `app/core/manual_routing.py`.
- Exponer el mapeo temático en `app/core/manual_routing.yml` para facilitar ajustes sin tocar el código.

### Entregables

- Script `scripts/ingest.py`.
- Servicios de carga documental y fragmentación.
- Datos procesados listos para embeddings.
- Ruta de carga que no reconstruye todo el corpus en cada subida.
- Acción de reindexación manual reutilizando el proveedor y modelo seleccionados para la carga.
- Recuperación que prioriza el manual correcto cuando la consulta apunta a usuarios, nómina, facturación u otro módulo específico.
- Reglas de enrutamiento centralizadas para extender nuevos temas o manuales sin tocar la lógica del RAG.
- Reglas de enrutamiento editables desde un archivo YAML dedicado.
- Búsqueda acotada por `manual_code` cuando el router detecta un módulo claro.
- Recuperación filtrada primero por manual cuando la consulta tiene un destino temático claro.

### Criterio de cierre

La fase se considera cerrada cuando los PDFs se procesan sin errores importantes, el sistema conserva trazabilidad por documento y página, la carga del frontend reindexa solo los archivos nuevos, existe una opción explícita de reindexación manual y la recuperación favorece el manual más específico según el tema consultado.

## Fase 3. Índice vectorial y recuperación

Objetivo: convertir los fragmentos en embeddings y habilitar búsqueda semántica.

### Tareas

- Configurar embeddings.
- Crear el vector store local.
- Persistir el índice.
- Probar consultas de recuperación sin generación todavía.

### Entregables

- Carpeta `vectorstore/` generada correctamente.
- Servicio `app/services/vectorstore.py`.
- Pruebas básicas de recuperación.

### Criterio de cierre

La fase se considera cerrada cuando una consulta devuelve fragmentos relevantes del manual adecuado.

## Fase 4. Cadena RAG y respuestas

Objetivo: construir el agente que genere respuestas usando contexto recuperado.

### Tareas

- Definir prompt del sistema.
- Construir cadena RAG con LangChain.
- Limitar las respuestas al contexto recuperado.
- Incorporar fuente o referencia documental básica.

### Entregables

- Servicio `app/services/rag_chain.py`.
- Endpoint o script que responda preguntas.
- Primer conjunto de ejemplos de preguntas y respuestas.

### Criterio de cierre

La fase se considera cerrada cuando el agente responde correctamente un conjunto mínimo de preguntas reales sobre Exactus usando los PDFs cargados.[file:1][file:4]

## Fase 5. API local y validación funcional

Objetivo: exponer el agente mediante una API local y verificar estabilidad.

### Tareas

- Crear endpoints `/health` y `/ask`.
- Agregar validación de entrada.
- Incorporar logging básico.
- Ejecutar pruebas manuales y smoke tests.
- Mantener el frontend y la API alineados con la carga incremental.

### Entregables

- API FastAPI funcional.
- Scripts de prueba rápida.
- Registro de preguntas validadas.

### Criterio de cierre

La fase se considera cerrada cuando el servicio puede levantarse localmente, recibir preguntas y responder de forma estable, y la carga de documentos no provoca reconstrucciones completas innecesarias.

## Fase 6. Documentación del proyecto

Objetivo: dejar el repositorio listo para evaluación y entrega.

### Tareas

- Redactar README.
- Documentar arquitectura.
- Incluir tecnologías utilizadas.
- Agregar instrucciones de ejecución.
- Incluir ejemplos de preguntas y respuestas.
- Incorporar capturas o evidencia del despliegue cuando exista.

### Entregables

- `README.md` completo.
- `docs/architecture.md`.
- Evidencias de uso.

### Criterio de cierre

La fase se considera cerrada cuando el repositorio cumple con los entregables solicitados: código, README, arquitectura, instrucciones, ejemplos y evidencia del despliegue.[file:1][file:4][file:2]

## Fase 7. Despliegue en OCI (Directo vía Systemd)

Objetivo: publicar la solución en Oracle Cloud Infrastructure Free Tier optimizando recursos.

> [!NOTE]
> **Decisión de Arquitectura:**
> Debido a la limitación de 1GB de RAM de la instancia gratuita de OCI (VM.Standard.E2.1.Micro), se decidió realizar un despliegue directo sobre el sistema operativo (Ubuntu) utilizando un entorno virtual de Python y gestionando el servicio en segundo plano con **Systemd**. Esto evita el consumo adicional de memoria que traería Docker y maximiza la disponibilidad de recursos para el Agente RAG.

### Tareas

- Crear y configurar la instancia VM.Standard.E2.1.Micro en OCI.
- Subir el código fuente empaquetado.
- Configurar el entorno virtual e instalar dependencias.
- Configurar las variables de entorno unificadas en `.env` (habilitando OpenAI como proveedor principal prepagado).
- Ejecutar la ingesta incremental rápida de los manuales.
- Configurar reglas de seguridad de entrada de red (OCI Security List y iptables del SO) para abrir el puerto 8000.
- Configurar exactus-rag.service en Systemd para garantizar disponibilidad del backend.
- Conectar el frontend local de Streamlit a la API de producción.

### Entregables

- Backend API corriendo de forma pública y persistente en `http://130.162.58.58:8000`.
- Endpoint `GET /health` respondiendo externamente con éxito.
- Frontend Streamlit local interactuando exitosamente con la API en OCI.

### Criterio de cierre

La fase se considera cerrada cuando la aplicación está funcionando en OCI, el puerto es accesible externamente y el sistema de reindexación incremental responde correctamente sin límites de cuota usando la clave OpenAI prepagada.

## Plan de seguimiento

El seguimiento debe ser simple, medible y orientado a entregables, ya que el desafío valora una solución funcional, bien organizada y bien documentada.[file:1][file:4]

### Estados sugeridos

- Pendiente.
- En progreso.
- Bloqueado.
- Validado.

### Tablero de seguimiento

| Fase                   | Estado   | Responsable | Evidencia                                                | Fecha objetivo |
| ---------------------- | -------- | ----------- | -------------------------------------------------------- | -------------- |
| Definición de alcance  | Validado | Proyecto    | PDFs y preguntas base creados                            | Completado     |
| Ingesta documental     | Validado | Proyecto    | Scripts de ingesta incremental con pacing automático     | Completado     |
| Índice vectorial       | Validado | Proyecto    | Vector store local persistido (Chroma DB)                | Completado     |
| Cadena RAG             | Validado | Proyecto    | Enrutamiento temático inteligente y respuestas correctas | Completado     |
| API local              | Validado | Proyecto    | `/health` y `/ask` operativos en entorno de desarrollo   | Completado     |
| README y documentación | Validado | Proyecto    | README completo con guías de OCI y de Red                | Completado     |
| Deploy OCI             | Validado | Proyecto    | API activa en `http://130.162.58.58:8000` con systemd    | Completado     |

### Métricas de avance

- Número de PDFs incorporados.
- Número de preguntas de prueba definidas.
- Número de preguntas respondidas correctamente.
- Estado del entorno: local, Docker, OCI.
- Número de commits relevantes en GitHub, ya que el reto pide historial de commits como parte del entregable.[file:4]

## Cronograma sugerido

### Semana 1

- Selección de manuales Exactus.
- Preparación de estructura del proyecto.
- Lectura de PDFs.
- C .
- Creación de índice vectorial.

### Semana 2

- Implementación de cadena RAG.
- API con FastAPI.
- Pruebas funcionales.
- Ajustes de prompt y retrieval.
- Borrador del README.

### Semana 3

- Dockerización.
- Despliegue en OCI.
- Capturas de evidencia.
- Limpieza del repositorio.
- Revisión final de entregables antes del envío.[file:2][file:4]

## Estructura mínima de trabajo

```bash
exactus-rag-agent/
├── app/
│   ├── api/
│   ├── core/
│   ├── schemas/
│   └── services/
├── data/
│   └── processed/
│   └── raw/exactus/
├── docs/
├── frontend/
├── scripts/
├── tests/
├── vectorstore/
├── .env.example
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Riesgos y mitigación

| Riesgo                            | Impacto | Mitigación                                                             |
| --------------------------------- | ------- | ---------------------------------------------------------------------- |
| PDFs con mala extracción de texto | Medio   | Probar primero con pocos manuales y validar calidad del texto.         |
| Respuestas imprecisas             | Alto    | Ajustar chunk size, embeddings y prompt; validar con preguntas reales. |
| Exceso de alcance                 | Alto    | Mantener MVP enfocado en pocos documentos y una API simple.            |
| Problemas en OCI                  | Medio   | Probar primero en Docker local y luego migrar a OCI.                   |
| README incompleto                 | Alto    | Documentar desde etapas tempranas y no al final únicamente.            |

## Criterios de éxito del proyecto

El proyecto estará listo para entrega cuando cumpla estos puntos:

- Existe un agente funcional que responde preguntas basadas en manuales PDF de Exactus.[file:4]
- El repositorio GitHub es público, organizado y con historial de commits.[file:4][file:2]
- El README documenta arquitectura, tecnologías, ejecución y ejemplos.[file:1][file:4]
- Existe evidencia del despliegue en OCI mediante URL pública o captura.[file:4]

## Próximo paso operativo

El siguiente paso recomendado es crear la estructura base del proyecto y preparar los primeros archivos funcionales: configuración, endpoints mínimos, servicio de carga documental y script de ingesta. Esto sigue la recomendación del challenge de iniciar por un agente local funcional antes del despliegue.[file:1]
