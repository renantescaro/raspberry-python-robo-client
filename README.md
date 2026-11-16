# raspberry-python-robo-client
[![Testes](https://github.com/renantescaro/raspberry-python-robo-client/actions/workflows/tests.yml/badge.svg)](https://github.com/renantescaro/raspberry-python-robo-client/actions/workflows/tests.yml)

Aplicação desktop (Windows e Linux) que controla o robô com Raspberry Pi
([servidor](https://github.com/renantescaro/raspberry-python-robo-server)) usando um joystick.

* envia comandos por socket TCP (protocolo binário de 4 bytes, apenas quando algo muda + heartbeat)
* tela para mapear os botões/eixos do joystick
* controle pelo teclado, junto ou no lugar do joystick
* exibição do streaming de vídeo do robô, com detecção de rostos opcional

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
o joystick e o comando atual. Com ela em foco:

| Ação | Teclas padrão |
|---|---|
| frente / ré | `W` `↑` / `S` `↓` |
| esquerda / direita | `A` `←` / `D` `→` |
| câmera cima / baixo | `I` / `K` |
| câmera esquerda / direita | `J` / `L` |
| sair | `Esc` |

Teclado e joystick funcionam juntos. Sem joystick configurado o cliente roda só com o teclado.
As teclas podem ser trocadas no `.env` (`KEY_*`). Ao tirar o foco da janela as teclas são soltas
e o robô para.

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
