# 🚀 Guardião de Ergonomia e Foco - Global Solution 2025

**Projeto de Edge Computing & IoT para a Global Solution da FIAP, focado no tema "O Futuro do Trabalho".**

Este projeto é uma solução de IoT que aborda diretamente o desafio de **Saúde e Bem-Estar no Trabalho** para profissionais em home office (trabalho remoto), um pilar central do "Futuro do Trabalho".

---

## 👥 Integrantes

* *Daniel Brito dos Santos Junior - RM 566236*
* *Gustavo Palomares Borsato - RM 564621*
* *Vitor Rampazzi Franco - RM 562270*

---

## 📄 Descrição do Projeto

### O Problema
Com o crescimento do trabalho remoto, problemas de saúde como LER (Lesão por Esforço Repetitivo), dores nas costas e *burnout* tornaram-se comuns. Muitos profissionais passam horas em má postura e esquecem-se de fazer pausas regulares, afetando a sua saúde e produtividade.

### A Solução
O **"Guardião de Ergonomia e Foco"** é um assistente de bem-estar inteligente e proativo. A solução utiliza um dispositivo IoT (ESP32) para monitorizar ativamente a postura do utilizador e gerir ciclos de trabalho e pausa (Método Pomodoro).

A solução é composta por duas partes principais:
1.  **Dispositivo de Hardware (Edge):** Um ESP32 simulado no Wokwi que usa um sensor ultrassônico para medir a distância do utilizador ao monitor. Ele fornece feedback local imediato através de LEDs (Verde, Amarelo, Vermelho) e um buzzer.
2.  **Portal de Bem-Estar (Dashboard):** Uma aplicação web (Python Flask + SocketIO) que recebe os dados do ESP32 via MQTT. O portal não só exibe o status em tempo real, mas também **educa o utilizador**, explicando o que cada estado significa e quais ações tomar.

---

## 🔗 Links e Demonstração

* **Link do Wokwi:** [CLIQUE AQUI PARA ACESSAR A SIMULAÇÃO](https://wokwi.com/projects/447283123261239297)
* **Link do Vídeo Explicativo:** [CLIQUE AQUI PARA VER O VÍDEO](COLOQUE-SEU-LINK-DO-YOUTUBE/DRIVE-AQUI)

### 📸 Screenshots

## **Circuito no Wokwi:**
<img width="1049" height="449" alt="image" src="https://github.com/user-attachments/assets/4c5844d6-6fca-4543-93a2-ffdd4c9e6d2e" />

## **Dashboard (Portal de Bem-Estar):**
<img width="1917" height="909" alt="image" src="https://github.com/user-attachments/assets/c3e96926-45b5-4b7d-bbcb-c27a09916aba" />


---

## 📡 Arquitetura e Tópicos MQTT

Este projeto utiliza uma arquitetura Cliente-Servidor baseada no protocolo MQTT para comunicação em tempo real.

* **Broker MQTT Utilizado:** `54.172.140.81` (IP do Servidor do Professor)

### 1. Tópico de Publicação (ESP32 -> Dashboard)
O ESP32 envia dados dos sensores para o servidor.

* **Tópico:** `fiap/gs/ergonomia/attrs`
* **Descrição:** O ESP32 publica um *payload* JSON neste tópico a cada 2 segundos, contendo o estado atual do utilizador.
* **Exemplo de Payload (JSON):**
    ```json
    {
      "distancia": 45,
      "postura": "OK",
      "timer_status": "INATIVO"
    }
    ```

### 2. Tópico de Subscrição (Dashboard -> ESP32)
O ESP32 subscreve este tópico para receber comandos do dashboard.

* **Tópico:** `fiap/gs/ergonomia/cmd`
* **Descrição:** O servidor Python publica comandos neste tópico quando o utilizador clica nos botões "Iniciar" ou "Parar" no site.
* **Exemplos de Payload (JSON):**
    * `{"comando": "start"}` (Para iniciar o timer Pomodoro)
    * `{"comando": "reset"}` (Para parar/resetar o timer)

---

## 🛠️ Instruções de Uso e Replicação

Para executar este projeto, você precisará de dois ambientes a funcionar em simultâneo: a **simulação do hardware** (Wokwi) e o **servidor do dashboard** (no seu computador).

### Ambiente 1: O Hardware (Simulação no Wokwi)

1.  Abra o **[Link do Wokwi](https://wokwi.com/projects/447283123261239297)**.
2.  O código `ergonomia_esp32.ino` já deve estar carregado.
3.  As bibliotecas C++ (`WiFi.h`, `PubSubClient.h`, etc.) são importadas pelo `#include` no código e **já estão incluídas no Wokwi**. Não é preciso instalar nada aqui.
4.  Pressione o botão "Play" (verde) para iniciar a simulação.
5.  Abra o **Monitor Serial** para ver as mensagens de conexão ao WiFi e ao Broker MQTT.

### Ambiente 2: O Servidor (Execução Local no seu PC)

Este é o "cérebro" que liga o ESP32 ao seu navegador.

1.  Abra um terminal (prompt de comando) no seu computador.
2.  Navegue até a pasta `servidor-dashboard` do projeto.
3.  **Instale as dependências (Bibliotecas Python):**
    Antes de executar, precisa de instalar as bibliotecas que o Python usa (Flask, SocketIO e Paho-MQTT). O ficheiro `requirements.txt` lista todas elas.
    
    Execute o comando abaixo (apenas uma vez):
    ```bash
    pip install -r requirements.txt
    ```
4.  **Inicie o Servidor:**
    Após instalar as dependências, inicie o servidor com o seguinte comando:
    ```bash
    python dashboard_ergonomia.py
    ```
5.  Se tudo correr bem, verá uma mensagem como `Iniciando servidor Flask...`.

### Passo 3: Teste

1.  Com o **Ambiente 1** (Wokwi) e o **Ambiente 2** (Servidor Python) a funcionar.
2.  Abra o seu navegador e acesse: `http://127.0.0.1:5000`.
3.  No Wokwi, **clique no sensor ultrassônico** e **arraste o slider** para alterar a distância.
4.  Observe o dashboard no seu navegador: o status (OK, ATENCAO, ALERTA) e a distância devem mudar em tempo real.
5.  No dashboard, clique em **"Iniciar Ciclo"**. Observe o LCD no Wokwi: o timer deve mudar de "INATIVO" para "FOCO".

---

## 🗂️ Códigos-Fonte Comentados

* **`hardware-dispositivo/ergonomia_esp32.ino`**: Código C++ (Arduino) para o ESP32, responsável por ler os sensores, controlar os atuadores (LEDs, LCD, Buzzer) e comunicar via MQTT.
* **`servidor-dashboard/dashboard_ergonomia.py`**: Código Python que contém o servidor Flask, a lógica de SocketIO (tempo real) e o cliente MQTT (Paho) que faz a ponte entre o ESP32 e o dashboard.
* **`servidor-dashboard/requirements.txt`**: Lista de dependências Python necessárias para rodar o servidor.
