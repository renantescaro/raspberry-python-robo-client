# raspberry-python-robo-client
[![Testes](https://github.com/renantescaro/raspberry-python-robo-client/actions/workflows/tests.yml/badge.svg)](https://github.com/renantescaro/raspberry-python-robo-client/actions/workflows/tests.yml)

Aplicação desktop (Windows e Linux) que controla o robô com Raspberry Pi
([servidor](https://github.com/renantescaro/raspberry-python-robo-server)) usando um joystick.

* envia comandos por socket TCP (protocolo binário de 4 bytes, apenas quando algo muda + heartbeat)
* tela para mapear os botões/eixos do joystick
* controle pelo teclado, junto ou no lugar do joystick
* botão para desligar o Raspberry Pi
* vídeo da câmera do robô dentro da janela de controle, com detecção opcional de rostos, pessoas, gatos e cachorros

## Instalação

Windows:
```bash
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

Linux:
```bash
sudo apt-get install python3-tk
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Atualizando um venv da versão antiga: remova antes os pacotes que conflitam
(`pip uninstall pygame opencv-python Pillow`), pois `pygame-ce` e `opencv-contrib-python`
usam os mesmos nomes de módulo.

## Configuração ⚙️

Copie `.env.example` para `.env` e defina ao menos `SERVER_HOST`.
Arquivos `.env` da versão anterior (chaves em português) continuam funcionando.

## Execução

```bash
python main.py                  # controle do robô (abre a configuração se faltar mapeamento)
python main.py --configure      # remapear o joystick
python main.py --video          # exibe o vídeo mesmo com VIDEO_ENABLED=false
python main.py --test-joystick  # mostra os botões/eixos pressionados
```

### Teclado ⌨️

Com `KEYBOARD_ENABLED=true` (padrão) abre a janela **Controle do robô**, que mostra a conexão,
o joystick e o comando atual (e o vídeo, se habilitado). Com ela em foco:

| Ação | Teclas padrão |
|---|---|
| frente / ré | `W` / `S` |
| esquerda / direita | `A` / `D` |
| câmera cima / baixo | `↑` / `↓` |
| câmera esquerda / direita | `←` / `→` |
| sair | `Esc` |

Teclado e joystick funcionam juntos. Sem joystick configurado o cliente roda só com o teclado.
As teclas podem ser trocadas no `.env` (`KEY_*`). Ao tirar o foco da janela as teclas são soltas
e o robô para.

### Wi-Fi do robô 📶

O painel da janela mostra a qualidade do Wi-Fi do robô, enviada pelo servidor a cada 2 s:
por exemplo, *Wi-Fi do robô: 91% (-46 dBm) - ótimo*. A cor indica a faixa: verde (ótimo ≥ 70%,
bom ≥ 50%), laranja (fraco ≥ 30%) e vermelho (ruim). Com um servidor antigo aparece *sem dados*.

### Desligar o robô 🔌

O botão **Desligar robô** fica no canto superior direito da janela. Por segurança é preciso
**clicar duas vezes**: o primeiro clique mostra *Confirmar?* (vermelho) por 3 segundos e só o
segundo clique nesse intervalo envia o comando. O botão fica desabilitado sem conexão com o robô.
O servidor precisa estar configurado para permitir o desligamento (veja o README do servidor).

### Vídeo 📷

Com `VIDEO_ENABLED=true` e `STREAMING_URL=http://<pi>:8080/?action=stream`, a imagem da câmera
aparece na própria janela **Controle do robô**, com o status sobreposto no rodapé.

* `VIDEO_SIZE` é o tamanho da janela; o vídeo é ajustado mantendo a proporção
* `VIDEO_ROTATE_180=false` se a imagem aparecer de cabeça para baixo
* a leitura e decodificação rodam numa thread (o OpenCV libera o GIL), sem atrasar os comandos;
  só o quadro mais recente é exibido
* se o stream cair, o cliente reconecta sozinho

### Detecção de rostos, pessoas e animais 🐱🐶

`DETECT` escolhe o que marcar no vídeo, separado por vírgula: `face`, `person`, `cat`, `dog`.
Exemplo: `DETECT=cat,dog`. Cada detecção aparece com uma caixa colorida e o nome (com a confiança).

* `face` usa um classificador Haar (`assets/haarcascade_face.xml`): só acha rostos de frente
* `person`, `cat` e `dog` usam o **YOLO11n** pelo módulo DNN do OpenCV (sem PyTorch). Ele
  reconhece o corpo inteiro, de lado ou visto de baixo, o que importa numa câmera rente ao chão
* o modelo (~11 MB) é baixado na primeira vez para `assets/yolo11n.onnx` e conferido pelo SHA-256;
  sem internet, a detecção de pessoas/animais é desativada e o resto continua funcionando
* `DETECT_CONFIDENCE` (padrão `0.5`) é a confiança mínima para mostrar uma pessoa/animal
* a detecção roda na thread de vídeo, a cada 2 quadros (~20 ms por quadro numa CPU comum)
* a chave antiga `FACE_DETECTION=true` continua valendo (equivale a incluir `face`)

O modelo YOLO11n é da Ultralytics, licenciado em AGPL-3.0.

Para testar sem o robô, rode o servidor em modo simulador: `python main.py --simulate`.

## Testes

```bash
pip install -r requirements-dev.txt
pytest                                   # unitários, integração e contrato
pytest tests/test_contract.py -v         # só o contrato do protocolo
```

Os testes de contrato validam o `protocol.py` contra `tests/contract/protocol_vectors.json`.
Se o repositório `raspberry-python-robo-server` estiver clonado na pasta ao lado (ou em `PEER_REPO_DIR`),
também testam a compatibilidade cruzada com ele. `tests/test_contract.py` e o arquivo de
vetores devem ser **idênticos** nos dois repositórios.

O GitHub Actions (`.github/workflows/tests.yml`) roda tudo a cada push na `master` e em pull requests;
o job de contrato baixa o outro repositório na branch de mesmo nome (ou `master`).
