# Sumário

- [Sumário](#sumário)
- [Organização](#organização)
- [Instalação e Execução](#instalação-e-execução)
  - [Servidor](#servidor)
  - [Cliente(s)](#clientes)

# Organização

.
 * [README.md](./chat/README.md): leia-me
 * [server.py](./chat/server.py): roda o servidor.
 * [client.py](./chat/client.py): roda um cliente.
 * [codec_img.py](./chat/codec_img.py): codifica e decodifica imagens.
 * [codec_audio.py](./chat/codec_audio.py): codifica e decodifica pedaços (frames) de áudios.
 * [msgs.py](./chat/msgs.py): padroniza as mensagens JSON utilizadas por servidor e cliente(s).
 * [constants.py](./chat/constants.py): padroniza as constantes utilizadas pelo código.
 * [requirements.txt](./chat/requirements.txt): lista as bibliotecas Python utilizadas no projeto, exceto as bibliotecas padrão.
 * [requirements_client.txt](./chat/requirements.txt): lista as bibliotecas Python utilizadas somente por clientes.

# Instalação e Execução

## Servidor

Requisito(s):
* Python 3 instalado
* Pip instalado como módulo do Python 3

Navegar ate a pasta "chat" deste repositório.

```bash
cd ./chat
```

Instalar as bibliotecas Python em comum entre servidor e cliente(s).

```bash
python3 -m pip install -r requirements.txt
```

Rodar o servidor com os parâmetros adequados.

```bash
python3 server.py

# Para alterar a porta
python3 server.py --port 8005

# Veja mais parâmetros
python3 server.py --help
```

## Cliente(s)

Requisito(s):
* Python 3 instalado
* Pip instalado como módulo do Python 3

Navegar ate a pasta "chat" deste repositório.

```bash
cd ./chat
```

Instalar as bibliotecas Python em comum entre servidor e cliente(s).

```bash
python3 -m pip install -r requirements.txt
```

Instalar as bibliotecas Python em comum específicas a cliente(s).

```bash
python3 -m pip install -r requirements_client.txt
```

Rodar um ou mais clientes com os parâmetros adequados.

```bash
# Para rodar o cliente (escolher tipo de diálogo ao iniciar)
python3 client.py

# Usar "wss" para se conectar a um servidor rodando com certificado SSL
python3 client.py --server-uri "wss://18.231.183.136.sslip.io"

# Para enviar vídeo a partir de uma webcam
python3 client.py --stream-video --video-device "/dev/video0"

# Para enviar vídeo a partir de um arquivo
python3 client.py --stream-video --video-device "test.mp4"

# Veja mais parâmetros
python3 client.py --help
```
