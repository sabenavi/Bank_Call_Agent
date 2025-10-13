import os
import json
import websocket
import threading
import base64
import pyaudio
from dotenv import load_dotenv
import time
from prompt import PROMPT
from tools import consultar_cuenta_api, consultar_tarjeta_api, consultar_poliza_api
from pydub import AudioSegment
from info_retriever import crear_knowledge_base
load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")



url = 'wss://api.openai.com/v1/realtime?model=gpt-4o-mini-realtime-preview-2024-12-17'
headers = ["Authorization: Bearer " + OPENAI_API_KEY, "OpenAI-Beta: realtime=v1"]


class AudioHandler:
    def __init__(self, rate=24000, chunk_size=1024):
        self.p = pyaudio.PyAudio()
        self.stream_in = None
        self.stream_out = None
        self.rate = rate
        self.chunk_size = chunk_size
        self.is_recording = False
        self.audio_chunks = []  # <--- para guardar audio

    def start_stream(self):
        self.stream_in = self.p.open(format=pyaudio.paInt16,
                                     channels=1,
                                     rate=self.rate,
                                     input=True,
                                     frames_per_buffer=self.chunk_size)
        self.is_recording = True

    def stop_stream(self):
        if self.stream_in:
            self.stream_in.stop_stream()
            self.stream_in.close()
        self.is_recording = False

    def read_chunk(self):
        if self.stream_in and self.is_recording:
            chunk = self.stream_in.read(self.chunk_size, exception_on_overflow=False)
            self.audio_chunks.append(chunk)  # <--- guardar
            return chunk
        return None

    def start_output(self):
        if not self.stream_out:
            self.stream_out = self.p.open(format=pyaudio.paInt16,
                                          channels=1,
                                          rate=self.rate,
                                          output=True)

    def play_audio(self, audio_bytes):
        self.start_output()
        self.stream_out.write(audio_bytes)

    def save_user_audio_mp3(self, filename="user_audio.mp3"):
        # Convertir chunks a AudioSegment
        if not self.audio_chunks:
            return
        audio_data = b"".join(self.audio_chunks)
        audio_segment = AudioSegment(
            data=audio_data,
            sample_width=2,  # paInt16 -> 2 bytes
            frame_rate=self.rate,
            channels=1
        )
        audio_segment.export(filename, format="mp3")
        print(f"Audio del usuario guardado en {filename}")

    def cleanup(self):
        self.stop_stream()
        if self.stream_out:
            self.stream_out.stop_stream()
            self.stream_out.close()
        self.p.terminate()

audio_handler = AudioHandler()
ws_app = None

# --- WebSocket Callbacks ---
def on_open(ws):
    print("Conectividad a servidor lista.")
    print("Cargando instrucciones del asistente...")
    time.sleep(0.5)

    session_event = {
        "type": "session.update",
        "session": {
            "instructions": PROMPT,
            "modalities": ["text", "audio"],
            "turn_detection": {"type": "server_vad", "threshold": 0.7},
            "input_audio_noise_reduction": {"type": "near_field"},
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "voice": "ash",
            "temperature": 0.6,
            "tools": [
                        {
                            "type": 'function',
                            "name": 'closeCall',
                            "description": 'Si el cliente no tiene mas preguntas o ya desea cerrar la conversacion, llama a esta funcion'
                        },
                        {
                            "type": 'function',
                            "name": 'transferCall',
                            "description": 'Si el cliente desea hablar con una persona o un agente, llama a esta funcion'
                        },
                        {
                            "type": 'function',
                            "name": 'consultar_cuenta',
                            "description": 'Si el cliente desea conocer informacion sobre su cuenta como movimientos, llama a esta funcion'
                        },
                        {
                            "type": 'function',
                            "name": 'consultar_tarjeta',
                            "description": 'Si el cliente desea conocer informacion sobre su tarjeta de credito o debito, llama a esta funcion'
                        },
                        {
                            "type": 'function',
                            "name": 'consultar_poliza',
                            "description": 'Si el cliente desea conocer informacion sobre su poliza, llama a esta funcion'
                        }
                    ],
                    "tool_choice": 'auto'
        }
    }

    ws.send(json.dumps(session_event))
    print("Cliente puede comenzar a hablar.\n")
    ws.send(json.dumps({
                    "type": "conversation.item.create",
                    "item": {
                        "type": "message",
                        "role": "user",
                        "content":[{"type":"input_text","text":"Hola"}]
                    }
                }))
    ws.send(json.dumps({"type": "response.create"}))

def on_message(ws, message):
    data = json.loads(message)
    event_type = data.get("type")
    if event_type == "response.text.delta":
        print(data["delta"], end="", flush=True)
    elif event_type == "response.audio.delta" and "delta" in data:
        audio_bytes = base64.b64decode(data["delta"])
        audio_handler.play_audio(audio_bytes)
    elif event_type == "response.done":
         response = data.get("response", {})
         output_items = response.get("output", [])

         for item in output_items:
            if not isinstance(item, dict):
                continue

            item_type = item.get("type")
            item_name = item.get("name")
            item_id = item.get("call_id")

            if item_type == "function_call" and item_name == "consultar_cuenta":
                print("Consultando cuenta...")                
                # Se forza el mensaje para que el agente lo diga
                saldo, movimientos = consultar_cuenta_api("099999")

                reply = (
                    f"Gracias. He verificado su cédula. "
                    f"Su saldo disponible en la cuenta principal es de {saldo:,.2f} dolares. "
                    f"Últimos movimientos: "
                    + ", ".join([f"{m['detalle']} ({m['monto']:+.2f} dolares)" for m in movimientos])
                    + ". ¿Desea realizar otra consulta?"
                )

                ws.send(json.dumps({
                    "type": "conversation.item.create",
                    "item": {
                        "type": "message",
                        "role": "user",
                        "content":[{"type":"input_text","text":"Dime lo siguiente:" +reply}]
                    }
                }))
                ws.send(json.dumps({"type": "response.create"}))

            elif item_type == "function_call" and item_name == "consultar_tarjeta":
                print("Consultando tarjeta...")
                # Se forza el mensaje para que el agente lo diga
                tarjetas = consultar_tarjeta_api("099999")

                reply = (
                    f"Gracias. He verificado su cédula. "
                    f"Resumen de sus tarjetas: "
                + ", ".join([f"{t['tarjeta']} (Limite: {t['limite']:+.2f}) dolares (Cupo disponible: {t['disponible']:+.2f} dolares)" for t in tarjetas])
                + ". ¿Desea realizar otra consulta?"
                )

                ws.send(json.dumps({
                    "type": "conversation.item.create",
                    "item": {
                        "type": "message",
                        "role": "user",
                        "content":[{"type":"input_text","text":"Dime lo siguiente:" +reply}]
                    }
                }))
                ws.send(json.dumps({"type": "response.create"}))
            elif item_type == "function_call" and item_name == "consultar_poliza":
                print("Consultando poliza...")
                polizas = consultar_poliza_api("099999")
                reply = (
                f"Gracias. He verificado su cédula. "
                f"Su póliza es de tipo {polizas['tipo']} y se encuentra {polizas['estado']}, "
                f"con vigencia {polizas['vigencia']}."
                )

                ws.send(json.dumps({
                    "type": "conversation.item.create",
                    "item": {
                        "type": "message",
                        "role": "user",
                        "content":[{"type":"input_text","text":"Dime lo siguiente:" + reply}]
                    }
                }))
                ws.send(json.dumps({"type": "response.create"}))
            elif item_type == "function_call" and item_name == "transferCall":
                print("Transfiriendo llamada...") 
            elif item_type == "function_call" and item_name == "closeCall":
                print("Cerrando llamada...")      



def on_close(ws, close_status_code, close_msg):
    print("Conexión cerrada:", close_status_code, close_msg)
    audio_handler.cleanup()


def on_error(ws, error):
    print("Error:", error)

def send_audio_continuous(ws):
    audio_handler.start_stream()

    try:
        while True:
            chunk = audio_handler.read_chunk()
            if chunk:
                try:
                    ws.send(json.dumps({
                        "type": "input_audio_buffer.append",
                        "audio": base64.b64encode(chunk).decode("utf-8")
                    }))
                except websocket.WebSocketConnectionClosedException:
                    print(" Conexión WebSocket cerrada.")
                    break
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\n[Detenido por usuario]")
    finally:
        ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
        audio_handler.stop_stream()

def run_ws():
    global ws_app
    ws_app = websocket.WebSocketApp(
        url,
        header=headers,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws_app.run_forever()

if __name__ == "__main__":
    ws_thread = threading.Thread(target=run_ws)
    ws_thread.start()

    # Esperar conexion websocket
    time.sleep(2)

    # Inicia envio de audio
    send_audio_continuous(ws_app)
