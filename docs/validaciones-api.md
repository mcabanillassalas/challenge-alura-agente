# Guía de Validaciones y Diagnóstico de API (Gemini / LangChain)

Esta guía recopila scripts rápidos en formato "one-liner" (comandos de una sola línea de Python) y scripts cortos que puedes ejecutar en la terminal (tanto local como en el servidor OCI) para validar el estado de tus llaves de API, la disponibilidad de modelos, y comprobar si has excedido las cuotas de ráfaga (429).

---

## 1. Verificación Básica de API Key y Conexión

Este comando valida que tu `GEMINI_API_KEY` sea válida y que el servidor tenga salida a internet para conectarse con Google.

### Comando individual (embed_query):
```bash
python -c "from langchain_google_genai import GoogleGenerativeAIEmbeddings; import os; os.environ['GOOGLE_API_KEY'] = 'AQ.Ab8RN6K9Mu6a8Xfm0nMGB1Ts_FyB9jtdxadIPfNBn7T7500NUg'; embed = GoogleGenerativeAIEmbeddings(model='gemini-embedding-2'); print('Conexión Exitosa. Dimensiones del vector:', len(embed.embed_query('test')))"
```
* **Salida esperada:** `Conexión Exitosa. Dimensiones del vector: 3072` (o 768 según el modelo).
* **Si falla:** Mostrará un error de autenticación (API Key inválida) o un error de timeout (problemas de red/firewall).

---

## 2. Diagnóstico de Lotes y Límites de Cuota (batch_embed)

Este comando prueba el procesamiento en lote (`embed_documents`), que es el que se utiliza para indexar múltiples fragmentos en el vectorstore. Es ideal para diagnosticar si has excedido tu cuota diaria (RPD) o de ráfaga (RPM).

```bash
python -c "from langchain_google_genai import GoogleGenerativeAIEmbeddings; import os; os.environ['GOOGLE_API_KEY'] = 'AQ.Ab8RN6K9Mu6a8Xfm0nMGB1Ts_FyB9jtdxadIPfNBn7T7500NUg'; embed = GoogleGenerativeAIEmbeddings(model='gemini-embedding-2'); print('Resultado lote exitoso:', len(embed.embed_documents(['texto 1', 'texto 2'])))"
```
* **Si falla con `RESOURCE_EXHAUSTED` (429):** Revisa los detalles del error en la consola:
  * Si la métrica contiene `RequestsPerMinute`, espera 60 segundos y vuelve a intentar.
  * Si la métrica contiene `RequestsPerDay`, significa que alcanzaste el límite diario (1,000 requests) para ese modelo específico y deberás esperar a que se restablezca a medianoche o cambiar de modelo.

---

## 3. Listar Modelos de Embeddings Disponibles

Si tienes dudas de qué modelos de embeddings están activos y soportados por tu clave de API, puedes consultar la lista oficial que Google le asigna a tu proyecto en tiempo real:

```bash
python -c "
import requests
api_key = 'AQ.Ab8RN6K9Mu6a8Xfm0nMGB1Ts_FyB9jtdxadIPfNBn7T7500NUg'
url = f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}'
response = requests.get(url).json()
print('Modelos de embedding disponibles:')
for m in response.get('models', []):
    if 'embedContent' in m.get('supportedGenerationMethods', []):
        print(f'- {m.get(\"name\")} ({m.get(\"displayName\")})')
"
```

* **Salida típica:**
  * `models/gemini-embedding-001`
  * `models/gemini-embedding-2`

---

## 4. Probar Generación de Respuestas (Chat / LLM)

Este comando valida que el modelo de lenguaje del chat (por defecto `gemini-2.5-flash`) esté funcionando y responda preguntas correctamente utilizando la API Key.

```bash
python -c "from langchain_google_genai import ChatGoogleGenerativeAI; import os; os.environ['GOOGLE_API_KEY'] = 'AQ.Ab8RN6K9Mu6a8Xfm0nMGB1Ts_FyB9jtdxadIPfNBn7T7500NUg'; llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash'); print('Respuesta LLM:', llm.invoke('Hola, ¿cuál es la capital de Francia?').content)"
```

* **Salida esperada:** `Respuesta LLM: La capital de Francia es París.`

---

## 5. Tabla de Errores Comunes de la API

| Código / Error | Causa | Solución |
| :--- | :--- | :--- |
| **`403 API_KEY_INVALID`** | La clave de API es incorrecta o está mal copiada. | Revisa que la variable `GEMINI_API_KEY` en el `.env` no tenga espacios ni comillas adicionales. |
| **`404 models/... is not found`** | El modelo que intentas usar ha sido retirado o renombrado por Google. | Consulta el paso 3 para listar los modelos activos y actualiza el código o `.env`. |
| **`429 RequestsPerMinuteExceeded`** | Has enviado demasiadas peticiones en un solo minuto (ráfaga). | Configura lotes (sub_batch_size) en los scripts e introduce pausas con `time.sleep()`. |
| **`429 RequestsPerDayExceeded`** | Agotaste la cuota de 1,000 llamadas gratuitas al día para ese modelo. | Espera a la medianoche (Hora del Pacífico) o cambia el modelo en el código a otro modelo activo (ej. de `gemini-embedding-2` a `gemini-embedding-001`). |
