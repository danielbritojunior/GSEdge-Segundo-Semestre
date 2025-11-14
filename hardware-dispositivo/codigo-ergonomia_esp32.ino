// --- Bibliotecas
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// --- Configurações de Rede
const char* SSID = "Wokwi-GUEST";
const char* PASSWORD = "";

// --- Configurações do MQTT 
const char* BROKER_MQTT = "44.223.43.74"; 
const int BROKER_PORT = 1883;

const char* ID_MQTT = "esp32_ergonomia_01";
const char* TOPICO_PUBLISH = "fiap/gs/ergonomia/attrs";
const char* TOPICO_SUBSCRIBE = "fiap/gs/ergonomia/cmd";

// --- Pinos e Componentes
const int I2C_SDA_PIN = 21;
const int I2C_SCL_PIN = 22;
const int BUZZER_PIN = 14;
const int TRIG_PIN = 5;
const int ECHO_PIN = 18;
const int LED_VERDE_PIN = 17;  // Postura OK
const int LED_AMARELO_PIN = 16;   // NOVO: Postura ATENÇÃO
const int LED_VERMELHO_PIN = 4; // Postura RUIM

// Limites de postura (em cm)
const int LIMITE_POSTURA_OK_CM = 40;     // Acima disto = VERDE
const int LIMITE_POSTURA_ALERTA_CM = 30; // Abaixo disto = VERMELHO
                                       // Entre os dois = AMARELO

// --- Componentes
LiquidCrystal_I2C lcd(0x27, 16, 2); 
WiFiClient espClient;
PubSubClient MQTT(espClient);

// --- Variáveis de Estado
int distanciaAtual = 0;
String estadoPostura = "OK";
String estadoTimer = "INATIVO";
bool timerAtivo = false;

// --- Variáveis de Temporização (Pomodoro)
unsigned long tempoInicioCiclo = 0;
// (Para testes usamos valores curtos)
const long DURACAO_FOCO_MS = 10000; // 10 segundos
const long DURACAO_PAUSA_MS = 5000; // 5 segundos

// --- Variáveis de Controle
unsigned long ultimoEnvioMQTT = 0;
const long INTERVALO_ENVIO_MQTT = 2000; // Envia dados a cada 2s

// --- Funções de Inicialização
void initSerial() { Serial.begin(115200); }
void initPins() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_VERDE_PIN, OUTPUT);
  pinMode(LED_AMARELO_PIN, OUTPUT); 
  pinMode(LED_VERMELHO_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
}
void initLCD() {
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  lcd.init(); lcd.backlight();
  lcd.setCursor(0, 0); lcd.print("Ergonomia: OK");
  lcd.setCursor(0, 1); lcd.print("Timer: INATIVO");
}
void initWiFi() {
  Serial.print("Conectando ao WiFi...");
  lcd.clear();
  lcd.setCursor(0, 0); lcd.print("Conectando WiFi");
  WiFi.begin(SSID, PASSWORD);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); lcd.print(".");}
  Serial.println("\nWiFi conectado!");
  lcd.clear();
  lcd.setCursor(0, 0); lcd.print("WiFi Conectado!");
  delay(1000);
}

// --- Funções de Atuadores e Sensores
void tocarSom(String tipo) {
  if (tipo == "foco") {
    tone(BUZZER_PIN, 500, 100); // 1 bipe curto
  } else if (tipo == "pausa") {
    tone(BUZZER_PIN, 800, 100); delay(100);
    tone(BUZZER_PIN, 800, 100); // 2 bipes curtos
  } else if (tipo == "alerta") {
    tone(BUZZER_PIN, 200, 50); // Bip baixo e rápido
  }
}
void atualizarLCD() {
  lcd.clear();
  // Linha 0: Postura
  lcd.setCursor(0, 0);
  lcd.print("Dist: "); lcd.print(distanciaAtual); lcd.print("cm ("); lcd.print(estadoPostura); lcd.print(")");
  
  // Linha 1: Timer
  lcd.setCursor(0, 1);
  lcd.print("Timer: "); lcd.print(estadoTimer);
  if (timerAtivo) {
    unsigned long tempoDecorrido = (millis() - tempoInicioCiclo) / 1000;
    lcd.print(" "); lcd.print(tempoDecorrido); lcd.print("s");
  }
}
int lerSensorDistancia() {
  digitalWrite(TRIG_PIN, LOW); delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH); delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long duration = pulseIn(ECHO_PIN, HIGH);
  return duration * 0.034 / 2;
}

// --- Funções de Lógica Principal
void checarPostura() {
  distanciaAtual = lerSensorDistancia();
  String estadoAnterior = estadoPostura;

  
  if (distanciaAtual <= LIMITE_POSTURA_ALERTA_CM && distanciaAtual > 0) {
    // 1. ALERTA (Ex: 1-30 cm)
    estadoPostura = "ALERTA";
    digitalWrite(LED_VERMELHO_PIN, HIGH);
    digitalWrite(LED_AMARELO_PIN, LOW);
    digitalWrite(LED_VERDE_PIN, LOW);
    if (estadoAnterior != "ALERTA") tocarSom("alerta"); // Toca só na transição
  
  } else if (distanciaAtual <= LIMITE_POSTURA_OK_CM && distanciaAtual > LIMITE_POSTURA_ALERTA_CM) {
    // 2. ATENCAO (Ex: 31-40 cm)
    estadoPostura = "ATENCAO";
    digitalWrite(LED_VERMELHO_PIN, LOW);
    digitalWrite(LED_AMARELO_PIN, HIGH);
    digitalWrite(LED_VERDE_PIN, LOW);
  
  } else if (distanciaAtual > LIMITE_POSTURA_OK_CM) {
    // 3. OK (Ex: > 40 cm)
    estadoPostura = "OK";
    digitalWrite(LED_VERMELHO_PIN, LOW);
    digitalWrite(LED_AMARELO_PIN, LOW);
    digitalWrite(LED_VERDE_PIN, HIGH);
  
  } else {
    // 4. ERRO (distancia == 0 ou negativa)
    // Se o sensor falhar a leitura, desliga tudo
    estadoPostura = "ERRO";
    digitalWrite(LED_VERMELHO_PIN, LOW);
    digitalWrite(LED_AMARELO_PIN, LOW);
    digitalWrite(LED_VERDE_PIN, LOW);
  }
}

void gerenciarTimerPomodoro() {
  if (!timerAtivo) return; 
  unsigned long tempoDecorrido = millis() - tempoInicioCiclo;

  if (estadoTimer == "FOCO") {
    if (tempoDecorrido >= DURACAO_FOCO_MS) {
      Serial.println("Tempo de FOCO terminado. Iniciando PAUSA.");
      tocarSom("pausa");
      estadoTimer = "PAUSA";
      tempoInicioCiclo = millis(); // Reinicia o contador
    }
  } else if (estadoTimer == "PAUSA") {
    if (tempoDecorrido >= DURACAO_PAUSA_MS) {
      Serial.println("Tempo de PAUSA terminado. Iniciando FOCO.");
      tocarSom("foco");
      estadoTimer = "FOCO";
      tempoInicioCiclo = millis(); // Reinicia o contador
    }
  }
}

// --- Funções MQTT
void sendDataMQTT() {
  StaticJsonDocument<200> doc;
  doc["distancia"] = distanciaAtual;
  doc["postura"] = estadoPostura; // Agora envia "OK", "ATENCAO" ou "ALERTA"
  doc["timer_status"] = timerAtivo ? estadoTimer : "INATIVO";
  
  char buffer[200];
  serializeJson(doc, buffer);
  
  MQTT.publish(TOPICO_PUBLISH, buffer);
  Serial.print("--- DADOS PUBLICADOS --- ");
  Serial.println(buffer);
}
void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  String msg;
  for (int i = 0; i < length; i++) msg += (char)payload[i];
  Serial.print("Mensagem recebida ["); Serial.print(topic); Serial.print("]: "); Serial.println(msg);

  StaticJsonDocument<128> doc;
  deserializeJson(doc, msg);
  const char* comando = doc["comando"]; 

  if (strcmp(comando, "start") == 0) {
    Serial.println("Comando de START recebido!");
    timerAtivo = true;
    estadoTimer = "FOCO";
    tempoInicioCiclo = millis();
    tocarSom("foco");
  } else if (strcmp(comando, "reset") == 0) {
    Serial.println("Comando de RESET recebido!");
    timerAtivo = false;
    estadoTimer = "INATIVO";
  }
  
  atualizarLCD();
  sendDataMQTT(); // Envia o novo estado imediatamente
}
void initMQTT() {
  MQTT.setServer(BROKER_MQTT, BROKER_PORT);
  MQTT.setCallback(mqtt_callback); 
}
void reconnectMQTT() {
  while (!MQTT.connected()) {
    Serial.print("Conectando ao Broker MQTT...");
    lcd.clear();
    lcd.setCursor(0, 0); lcd.print("Conectando MQTT");
    
    if (MQTT.connect(ID_MQTT)) {
      Serial.println("Conectado!");
      lcd.clear();
      lcd.setCursor(0, 0); lcd.print("MQTT Conectado!");
      delay(1000);
      MQTT.subscribe(TOPICO_SUBSCRIBE);
      Serial.print("Subscrito em: "); Serial.println(TOPICO_SUBSCRIBE);
    } else {
      Serial.print("Falha (rc="); Serial.print(MQTT.state()); Serial.println("), tentando novamente em 2s...");
      lcd.clear();
      lcd.setCursor(0, 0); lcd.print("Falha MQTT...");
      delay(2000);
    }
  }
}
void VerificaConexoesWiFIEMQTT() {
  if (WiFi.status() != WL_CONNECTED) initWiFi(); 
  if (!MQTT.connected()) reconnectMQTT();     
}

// ===== SETUP =====
void setup() {
  initSerial();
  initPins();
  initLCD();
  initWiFi();
  initMQTT();
  atualizarLCD(); // Atualiza o LCD com o estado inicial
}

// ===== LOOP =====
void loop() {
  VerificaConexoesWiFIEMQTT(); 
  MQTT.loop(); // Essencial para o MQTT (receber msgs e manter conexão)

  checarPostura();
  gerenciarTimerPomodoro();
  
  // Atualiza o LCD e envia dados MQTT em intervalos
  if (millis() - ultimoEnvioMQTT > INTERVALO_ENVIO_MQTT) {
    atualizarLCD();
    sendDataMQTT();
    ultimoEnvioMQTT = millis();
  }

  delay(100); // Pequeno delay para estabilidade
}