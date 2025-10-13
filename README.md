# Bank_Call_Agent
Asistente virtual voice-to-voice con VAD impulsado con la API de realtime modelo mini de OpenAI
# BG Bot - Asistente Virtual por Voz (Banco Guayaquil)

**BG Bot** es un asistente virtual por voz que se comunica en tiempo real con la API de OpenAI.  
Permite conversar mediante audio con respuestas habladas y maneja herramientas personalizadas para simular la consulta de **cuentas**, **tarjetas** y **pólizas** del Banco Guayaquil.

---

## Características

- Conversación por voz en tiempo real (cliente WebSocket con OpenAI Realtime API).  
- Respuestas contextuales usando un prompt diseñado para banca.  
- Ejecución automática de funciones (consultar cuenta, tarjeta o póliza).  
- Detección automática de voz (`server_vad`).  

---

## 🧰 Requisitos

- Python **3.10 o superior** (recomendado: **3.12**).  
- Micrófono funcional.  
- Clave API válida de **OpenAI** con acceso a modelos Realtime.  

---

## ⚙️ Instalación y configuración

### Clonar el repositorio

git clone https://github.com/tu-usuario/bg-bot-voice-assistant.git
cd bg-bot-voice-assistant

### Crear un entorno virtual 
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate

### Instalar dependencias
pip install -r requirements.txt

### Configurar las variables de entorno
Crear en la raiz del proyecto un archivo .env con el siguiente contenido
OPENAI_API_KEY=tu_clave_api_aqui

###Ejecución 
python main.py

