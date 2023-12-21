# Instalação e Execução

## Servidor

Requisitos:
* Docker instalado.
* Docker Compose instalado.

#### Local

Subir servidor localmente
```
docker compose -f docker-compose-local.yml up
```

#### Público (com SSL)

Criar arquivos para definir as variáveis de ambiente

```
# Definir DNS público
echo "
SERVER_NAME=example.com.br
" | tee .envs/production/server_name

echo "
CERT_EMAIL=example@email.com
" | tee .envs/production/email
```

Subir servidor publicamente

```
docker compose up
```

## Cliente(s)

#### Rodar cliente

Ver o [README](chat/README.md) da pasta "chat".

