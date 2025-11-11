"""
PROJETO: Guardião de Ergonomia e Foco (v3 - Dashboard/Site Completo)
DESCRIÇÃO: Versão com um portal web informativo que explica
           o que fazer em cada situação de ergonomia e produtividade.
"""

from flask import Flask, render_template_string
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import json

# --- Configurações do MQTT 
MQTT_BROKER    = "broker.hivemq.com" 
MQTT_PORT      = 1883
MQTT_KEEPALIVE = 60
MQTT_TOPIC_DADOS = "fiap/gs/ergonomia/attrs"
MQTT_TOPIC_CMD   = "fiap/gs/ergonomia/cmd"

# --- App Flask e SocketIO
app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")

# --- Variável de Estado Global
ultimo_estado = {
    "distancia": 0,
    "postura": "INATIVO",
    "timer_status": "INATIVO"
}

# ================== Lógica MQTT ==================
# (Nenhuma mudança aqui)
def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Conectado ao Broker '{MQTT_BROKER}' com resultado: {rc}")
    client.subscribe(MQTT_TOPIC_DADOS)
    print(f"[MQTT] Subscrito em: {MQTT_TOPIC_DADOS}")

def on_message(client, userdata, msg):
    global ultimo_estado
    try:
        payload_str = msg.payload.decode("utf-8")
        print(f"[MQTT] Mensagem recebida em {msg.topic}: {payload_str}")
        data = json.loads(payload_str)
        ultimo_estado = {
            "distancia": data.get("distancia", ultimo_estado["distancia"]),
            "postura": data.get("postura", ultimo_estado["postura"]),
            "timer_status": data.get("timer_status", ultimo_estado["timer_status"])
        }
        socketio.emit("novo_estado", ultimo_estado)
        print(f"[SocketIO] Emitindo 'novo_estado': {ultimo_estado}")
    except Exception as e:
        print(f"[ERRO] Falha ao processar mensagem MQTT: {e}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
client.loop_start() 

# ================== Rotas HTTP (Flask) ==================

@app.route("/")
def index():
    # O HTML abaixo foi completamente reestruturado
    return render_template_string("""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Guardião de Ergonomia e Foco</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    
    <style>
        :root {
            --color-bg: #1f2023;
            --color-card: #2a2c30;
            --color-text: #eaeaea;
            --color-text-muted: #888;
            --color-ok: #28a745;
            --color-atencao: #ffc107;
            --color-alerta: #dc3545;
            --color-foco: #007bff;
            --color-inativo: #6c757d;
        }
        body {
            font-family: 'Roboto', sans-serif; background-color: var(--color-bg);
            color: var(--color-text);
            margin: 0; padding: 20px;
            /* Permite scrollar (rolar a página) */
            height: auto; 
            display: flex; flex-direction: column; align-items: center;
        }
        .container {
            width: 100%;
            max-width: 900px;
        }
        
        /* --- Cabeçalho --- */
        .header { text-align: center; margin-bottom: 20px; }
        .header h1 { font-size: 2.5rem; font-weight: 700; margin: 0; }
        .header p { font-size: 1.1rem; color: var(--color-text-muted); margin: 5px 0 0 0;}
        #status-socket { font-size: 0.9rem; color: var(--color-text-muted); height: 18px; }

        /* --- Título da Seção --- */
        .section-title {
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--color-text);
            margin-top: 40px;
            margin-bottom: 20px;
            border-bottom: 2px solid var(--color-foco);
            padding-bottom: 10px;
        }
        
        /* --- Grid do Dashboard (O que já tínhamos) --- */
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
        }
        .card {
            background-color: var(--color-card);
            padding: 25px; border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        .card h2 {
            font-size: 1.2rem; font-weight: 700; margin-top: 0;
            color: var(--color-text-muted); text-transform: uppercase;
            letter-spacing: 0.5px; border-bottom: 1px solid #444; padding-bottom: 10px;
        }
        
        /* Card de Postura */
        #card-postura .status-value {
            font-size: 4rem; font-weight: 700; text-align: center;
            margin: 10px 0; padding: 20px 0; border-radius: 8px;
            transition: all 0.3s ease;
        }
        #card-postura .status-value.status-ok { background-color: rgba(40, 167, 69, 0.1); color: var(--color-ok); }
        #card-postura .status-value.status-atencao { background-color: rgba(255, 193, 7, 0.1); color: var(--color-atencao); }
        #card-postura .status-value.status-alerta { background-color: rgba(220, 53, 69, 0.1); color: var(--color-alerta); }
        #card-postura .distancia-valor { font-size: 1.5rem; text-align: center; color: var(--color-text); }
        
        /* Card do Timer */
        #card-timer .status-value {
            font-size: 3rem; font-weight: 700; text-align: center;
            margin: 25px 0 35px 0;
            transition: color 0.3s ease;
        }
        #card-timer .status-value.status-foco { color: var(--color-foco); }
        #card-timer .status-value.status-pausa { color: var(--color-pausa); }
        #card-timer .status-value.status-inativo { color: var(--color-inativo); }
        
        .botoes-timer { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        .btn { padding: 15px; font-size: 1rem; font-weight: 700; border: none; border-radius: 8px; cursor: pointer; transition: all 0.2s ease; }
        .btn-start { background-color: var(--color-foco); color: white; }
        .btn-start:hover { background-color: #0056b3; }
        .btn-reset { background-color: var(--color-alerta); color: white; }
        .btn-reset:hover { background-color: #a71d2a; }
        
        /* --- NOVA SEÇÃO: Guia de Bem-Estar --- */
        .info-guide {
            background-color: var(--color-card);
            padding: 25px; border-radius: 12px;
            margin-top: 25px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        .info-guide h3 {
            font-size: 1.3rem;
            font-weight: 700;
            margin-top: 0;
            padding-bottom: 10px;
            border-bottom: 1px solid #444;
        }
        .info-guide p {
            font-size: 1rem;
            line-height: 1.6;
            color: var(--color-text-muted);
        }
        .info-guide .info-item h3 {
            /* Remove a borda de baixo para os itens */
            border-bottom: none;
        }
        
        /* Códigos de cor para os títulos */
        .info-ok { color: var(--color-ok); }
        .info-atencao { color: var(--color-atencao); }
        .info-alerta { color: var(--color-alerta); }
        .info-timer { color: var(--color-foco); }
        
    </style>
</head>
<body>

    <div class="container">
        <div class="header">
            <h1>Guardião de Ergonomia e Foco</h1>
            <p>Seu assistente pessoal de saúde e produtividade no trabalho remoto.</p>
            <div id="status-socket" class="status-socket">Conectando...</div>
        </div>

        <h2 class="section-title">Seu Status Atual</h2>
        <div class="dashboard-grid">
            <div class="card" id="card-postura">
                <h2>Postura Atual</h2>
                <div id="status-postura" class="status-value status-inativo">--</div>
                <div class="distancia-valor">
                    Distância: <span id="valor-distancia">--</span> cm
                </div>
            </div>

            <div class="card" id="card-timer">
                <h2>Foco / Pausa</h2>
                <div id="status-timer" class="status-value status-inativo">INATIVO</div>
                <div class="botoes-timer">
                    <button id="btn-start" class="btn btn-start">Iniciar Ciclo</button>
                    <button id="btn-reset" class="btn btn-reset">Parar/Resetar</button>
                </div>
            </div>
        </div>

        <h2 class="section-title">Guia de Bem-Estar e Produtividade</h2>
        <div class="info-guide">
            
            <div class="info-item">
                <h3 class="info-ok">VERDE (OK)</h3>
                <p>
                    <strong>O que significa:</strong> Sua postura está ótima! Você está a uma distância saudável do monitor.
                    <br/>
                    <strong>O que fazer:</strong> Continue assim! Manter essa distância previne a fadiga ocular e dores no pescoço.
                </p>
            </div>
            <hr style="border-color: #444; margin: 20px 0;">

            <div class="info-item">
                <h3 class="info-atencao">AMARELO (ATENÇÃO)</h3>
                <p>
                    <strong>O que significa:</strong> Você está começando a curvar-se ou a aproximar-se demais do ecrã.
                    <br/>
                    <strong>O que fazer:</strong> Ajuste suas costas na cadeira. Tente a regra "20-20-20": a cada 20 minutos, olhe para algo a 20 pés (6 metros) de distância por 20 segundos.
                </p>
            </div>
            <hr style="border-color: #444; margin: 20px 0;">

            <div class="info-item">
                <h3 class="info-alerta">VERMELHO (ALERTA)</h3>
                <p>
                    <strong>O que significa:</strong> Sua postura está incorreta. Você está muito perto do monitor, o que causa tensão extrema nos olhos, pescoço e ombros.
                    <br/>
                    <strong>O que fazer:</strong> PARE! Levante-se, estique os braços, olhe pela janela. Esta é a principal causa de LER (Lesão por Esforço Repetitivo). Corrija sua postura antes de continuar.
                </p>
            </div>
            <hr style="border-color: #444; margin: 20px 0;">

            <div class="info-item">
                <h3 class="info-timer">O Timer (Foco / Pausa)</h3>
                <p>
                    <strong>O que é?</strong>
                    Esta funcionalidade utiliza o <strong>"Método Pomodoro"</strong>, uma técnica de gestão de tempo mundialmente famosa. O método divide o trabalho em blocos focados (normalmente 25 minutos), seguidos por uma pausa curta (5 minutos).
                </p>
                <p>
                    <strong>Por que usar?</strong>
                    O cérebro humano não foi feito para manter o foco máximo por horas a fio. Pausas curtas e regulares são essenciais para prevenir a exaustão (burnout), "resetar" o foco e aumentar a sua <strong>produtividade</strong> geral ao longo do dia.
                </p>
                <p>
                    <strong>Nosso sistema:</strong>
                    Para melhorar a sua experiência, o dispositivo emite um <strong>alarme sonoro suave</strong> (via buzzer) para o avisar exatamente quando o seu tempo de "Foco" termina e a "Pausa" começa, e novamente quando é hora de voltar ao trabalho.
                    <br/>
                    <em>(Nota: O ciclo padrão no dispositivo está configurado para 10s de foco e 5s de pausa para fins de demonstração.)</em>
                </p>
            </div>

        </div>
    </div>

    <script>
        $(function() {
            const socket = io({ transports: ['websocket', 'polling'] });
            
            const statusSocketEl = $('#status-socket');
            const statusPosturaEl = $('#status-postura');
            const valorDistanciaEl = $('#valor-distancia');
            const statusTimerEl = $('#status-timer');
            
            socket.on('connect', () => { statusSocketEl.text('Conectado'); statusSocketEl.css('color', 'var(--color-ok)'); });
            socket.on('disconnect', () => { statusSocketEl.text('Desconectado'); statusSocketEl.css('color', 'var(--color-alerta)'); });

            socket.on('novo_estado', (data) => {
                console.log("Novo estado recebido:", data);
                
                if (data.postura) {
                    statusPosturaEl.text(data.postura);
                    statusPosturaEl.removeClass('status-ok status-atencao status-alerta');
                    if (data.postura === "OK") statusPosturaEl.addClass('status-ok');
                    else if (data.postura === "ATENCAO") statusPosturaEl.addClass('status-atencao');
                    else if (data.postura === "ALERTA") statusPosturaEl.addClass('status-alerta');
                }
                if (data.distancia !== undefined) valorDistanciaEl.text(data.distancia);

                if (data.timer_status) {
                    statusTimerEl.text(data.timer_status.replace("_", " "));
                    statusTimerEl.removeClass('status-foco status-pausa status-inativo');
                    if (data.timer_status === "FOCO") statusTimerEl.addClass('status-foco');
                    else if (data.timer_status === "PAUSA") statusTimerEl.addClass('status-pausa');
                    else statusTimerEl.addClass('status-inativo');
                }
            });
            
            $('#btn-start').click(() => { socket.emit('start_pomodoro'); });
            $('#btn-reset').click(() => { socket.emit('reset_pomodoro'); });
            
            socket.on('connect', () => { socket.emit('solicitar_estado_atual'); });
        });
    </script>
</body>
</html>
    """)

# ================== Eventos SocketIO ==================
# (Nenhuma mudança aqui)
@socketio.on('connect')
def handle_connect():
    print("[SocketIO] Novo cliente conectado.")
    socketio.emit("novo_estado", ultimo_estado)

@socketio.on('solicitar_estado_atual')
def handle_solicitar_estado():
    socketio.emit("novo_estado", ultimo_estado)

@socketio.on('start_pomodoro')
def handle_start_pomodoro():
    print("[SocketIO] Comando 'start_pomodoro' recebido do cliente.")
    payload_cmd = json.dumps({"comando": "start"})
    client.publish(MQTT_TOPIC_CMD, payload_cmd)
    print(f"[MQTT] Comando 'start' publicado em: {MQTT_TOPIC_CMD}")

@socketio.on('reset_pomodoro')
def handle_reset_pomodoro():
    print("[SocketIO] Comando 'reset_pomodoro' recebido do cliente.")
    payload_cmd = json.dumps({"comando": "reset"})
    client.publish(MQTT_TOPIC_CMD, payload_cmd)
    print(f"[MQTT] Comando 'reset' publicado em: {MQTT_TOPIC_CMD}")

# ================== Main ==================
if __name__ == "__main__":
    print("Iniciando servidor Flask com SocketIO (v3 - Dashboard/Site Completo)...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, use_reloader=False)