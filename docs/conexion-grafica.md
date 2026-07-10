# Guía de Conexión Gráfica a la Instancia de OCI

Esta guía detalla los métodos para conectarte y gestionar el Agente RAG en tu servidor de Oracle Cloud Infrastructure (OCI) de forma visual.

Debido a que la instancia gratuita de OCI cuenta con recursos limitados (**1 GB de RAM** y **1 OCPU**), se presentan dos opciones con sus respectivas advertencias de rendimiento.

---

## Opción A: VS Code Remote - SSH (Altamente Recomendada ⭐️)

Este es el estándar en el desarrollo de software. En lugar de instalar un escritorio completo y pesado en el servidor, utilizas **Visual Studio Code** en tu computadora local para conectarte directamente al sistema de archivos del servidor mediante SSH.

### Ventajas:

- **Consumo de recursos Cero en el servidor:** El entorno gráfico corre en tu PC de escritorio, no en la nube.
- **Todo en uno:** Tienes un explorador de archivos visual, editor de código con coloreado sintáctico, buscador global, terminal remota integrada y control de Git.
- **Rapidez:** La conexión es instantánea y no tiene retraso de video (lag).

### Paso 1: Instalar la extensión en tu VS Code local

1. Abre VS Code en tu máquina local.
2. Ve al menú de Extensiones en la barra lateral izquierda (`Ctrl + Shift + X`).
3. Busca **"Remote - SSH"** (desarrollada por Microsoft) e instálala.

### Paso 2: Configurar tu archivo de hosts SSH

1. En VS Code, haz clic en el botón verde con el icono `<>` (esquina inferior izquierda) o presiona `Ctrl + Shift + P` y escribe `Remote-SSH: Connect to Host...`.
2. Selecciona **"Configure SSH Hosts..."** y elige el archivo de configuración del usuario (típicamente `C:\Users\TU_USUARIO\.ssh\config`).
3. Añade la configuración de tu servidor usando los datos reales de tu sesión:

```text
Host exactus-rag-oci
    HostName 130.162.58.58
    User ubuntu
    IdentityFile D:\DevALURA\challenge-alura-agente\ssh-keys\ssh-key-2026-07-10.key
```

4. Guarda el archivo (`Ctrl + S`).

### Paso 3: Conectarse al servidor

1. Haz clic de nuevo en el botón verde `<>` en la esquina inferior izquierda.
2. Selecciona **"Connect to Host..."** y elige `exactus-rag-oci`.
3. Se abrirá una nueva ventana de VS Code. La primera vez, te preguntará el sistema operativo del host; selecciona **Linux**.
4. ¡Listo! En la barra lateral ahora puedes hacer clic en **"Open Folder"** (Abrir carpeta) y seleccionar `/home/ubuntu/agente-alura-rag` para editar y gestionar el código de forma 100% visual.

---

## Opción B: Escritorio Remoto (XRDP + XFCE)

Si necesitas utilizar una interfaz gráfica completa del sistema operativo (un escritorio clásico con ventanas, navegador web, etc.) directamente en la nube.

> [!WARNING]
> **ADVERTENCIA CRÍTICA DE RENDIMIENTO:**
> Tu instancia gratuita `VM.Standard.E2.1.Micro` cuenta únicamente con **1 GB de RAM**.
> Instalar y ejecutar un escritorio gráfico consumirá entre el 60% y 80% de la memoria del sistema. Esto provocará que la máquina virtual vaya extremadamente lenta y podría causar que el Agente RAG o la base de datos de Chroma colapsen por falta de memoria (Out of Memory). **Solo utiliza esta opción si es estrictamente necesario.**

### Paso 1: Instalar XFCE y XRDP (En la terminal SSH del servidor)

Conéctate por SSH y ejecuta los siguientes comandos para instalar un entorno de escritorio muy ligero (XFCE) y el servidor de escritorio remoto (XRDP):

```bash
# Actualizar e instalar el escritorio ligero XFCE
sudo apt update
sudo apt install -y xfce4 xfce4-goodies

# Instalar el servidor XRDP
sudo apt install -y xrdp

# Configurar XRDP para usar XFCE por defecto para el usuario actual
echo "xfce4-session" > ~/.xsession

# Reiniciar el servicio para aplicar cambios
sudo systemctl restart xrdp
```

### Paso 2: Crear una contraseña para el usuario `ubuntu`

Por defecto, el usuario `ubuntu` de OCI no tiene contraseña en el sistema (se autentica únicamente mediante llaves SSH). El cliente de Escritorio Remoto de Windows requiere una contraseña tradicional para ingresar. Créala con:

```bash
sudo passwd ubuntu
```

_(Ingresa y confirma una contraseña segura cuando la terminal te lo solicite. No se mostrarán caracteres al escribirla por seguridad)._

### Paso 3: Habilitar el puerto 3389 (RDP)

Para que la conexión pueda ingresar, debes abrir el puerto estándar de escritorio remoto:

**A. En la consola de Oracle Cloud (OCI):**

1. Ve a la página de detalles de tu instancia y haz clic en la **Subnet** asignada (en la sección _Primary VNIC_).
2. Haz clic en la **Default Security List** de la subred.
3. Añade una **Ingress Rule** (Regla de Ingreso):
   - **Source Type:** CIDR
   - **Source CIDR:** `0.0.0.0/0` (o tu IP pública para mayor seguridad)
   - **IP Protocol:** TCP
   - **Source Port Range:** All
   - **Destination Port Range:** `3389`
   - **Description:** Permitir Escritorio Remoto RDP

**B. En el Firewall de la máquina virtual (SSH):**

```bash
# Abrir el puerto en iptables
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 3389 -j ACCEPT

# Persistir la regla para reiniciar
sudo netfilter-persistent save
```

### Paso 4: Conectar desde Windows

1. En tu computadora con Windows, presiona la tecla de Inicio y busca **"Conexión a Escritorio Remoto"** (o presiona `Win + R`, escribe `mstsc` y dale `Enter`).
2. En el campo **Equipo**, escribe la IP pública de tu servidor: `130.162.58.58`.
3. Haz clic en **Conectar**.
4. Si aparece una advertencia de certificado de seguridad, haz clic en **Sí**.
5. En la pantalla de login de XRDP, introduce:
   - **Username:** `ubuntu`
   - **Password:** La contraseña que creaste en el Paso 2.
6. ¡Listo! Ingresarás al escritorio remoto gráfico de Ubuntu.
