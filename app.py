import os
import time
import glob
import json
import paho.mqtt.client as paho
import streamlit as st
from PIL import Image
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
from gtts import gTTS
from googletrans import Translator

# 1. Configuración de la Página
st.set_page_config(
    page_title="Control por Voz - MQTT IoT",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Estilos CSS Personalizados
st.markdown("""
    <style>
    /* Header principal en degradado */
    .header-container {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
        padding: 30px;
        border-radius: 20px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px rgba(99, 102, 241, 0.25);
    }
    .header-container h1 {
        margin: 0;
        font-size: 2.3rem;
        font-weight: 800;
        color: white !important;
    }
    .header-container p {
        margin-top: 8px;
        font-size: 1.05rem;
        color: #e0e7ff !important;
    }

    /* Tarjeta de estado para los comandos */
    .status-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 14px;
        padding: 20px;
        margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Callbacks y Configuración MQTT
def on_publish(client, userdata, result):
    print("El dato ha sido publicado correctamente.\n")

def on_message(client, userdata, message):
    global message_received
    time.sleep(2)
    message_received = str(message.payload.decode("utf-8"))
    st.write(message_received)

broker = "broker.mqttdashboard.com"
port = 1883
client1 = paho.Client("ClienteMajo")
client1.on_message = on_message

# 4. Barra Lateral (Información de red IoT)
with st.sidebar:
    st.title("🌐 Configuración IoT")
    st.caption("Conexión con Broker MQTT Dashboard")
    
    st.markdown("---")
    st.markdown(f"**Broker:** `{broker}`")
    st.markdown(f"**Puerto:** `{port}`")
    st.markdown(f"**Tópico MQTT:** `voicemajo`")
    
    st.markdown("---")
    st.info("💡 **Tip:** Asegúrate de dar permisos de micrófono a tu navegador cuando presiones el botón.")

# 5. Banner de Título
st.markdown("""
    <div class="header-container">
        <h1>🎙️ Control por Voz - Interfaces Multimodales</h1>
        <p>Captura comandos de voz en tiempo real y transmite instrucciones vía MQTT a sistemas ciberfísicos.</p>
    </div>
""", unsafe_allow_html=True)

# 6. Panel Principal
col_left, col_right = st.columns([1, 1.2], gap="large")

with col_left:
    st.subheader("🖼️ Asistente de Voz")
    try:
        image = Image.open('voice_ctrl.jpg')
        st.image(image, use_container_width=True)
    except Exception:
        st.info("🎙️ *Imagen del asistente no encontrada, el control por voz está activo.*")

with col_right:
    st.subheader("📢 Reconocimiento de Voz")
    st.write("Haz clic en el botón inferior para comenzar a escuchar:")

    # Configuración del Botón de Reconocimiento de Voz con Bokeh
    stt_button = Button(label="🎤 Iniciar Escucha de Voz", width=260)
    stt_button.js_on_event("button_click", CustomJS(code="""
        var recognition = new webkitSpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        
        recognition.onresult = function (e) {
            var value = "";
            for (var i = e.resultIndex; i < e.results.length; ++i) {
                if (e.results[i].isFinal) {
                    value += e.results[i][0].transcript;
                }
            }
            if (value != "") {
                document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
            }
        }
        recognition.start();
    """))

    result = streamlit_bokeh_events(
        stt_button,
        events="GET_TEXT",
        key="listen",
        refresh_on_update=False,
        override_height=75,
        debounce_time=0
    )

    # Procesamiento del Texto Reconocido
    if result and "GET_TEXT" in result:
        command_text = result.get("GET_TEXT").strip()
        
        st.markdown("### 📝 Comando Reconocido:")
        st.info(f"🗣️ **\"{command_text}\"**")
        
        # Envío del mensaje por MQTT
        try:
            client1.on_publish = on_publish
            client1.connect(broker, port)
            message = json.dumps({"Act1": command_text})
            ret = client1.publish("voicemajo", message)
            
            st.success(f"🚀 **Comando enviado con éxito vía MQTT al tópico `voicemajo`**", icon="✅")
        except Exception as e:
            st.error(f"Error al enviar mensaje por MQTT: {e}")

    # Creación de directorio temporal
    try:
        os.makedirs("temp", exist_ok=True)
    except Exception:
        pass
