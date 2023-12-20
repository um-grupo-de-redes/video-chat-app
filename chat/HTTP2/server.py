import asyncio
import base64
import ssl
import uuid
from enum import Enum
from aiohttp import web

client_dict = {}
map_clients = {}
map_room_id_to_client_list = {}
map_rooms = {}
uuid_list = []

class Client:
    def __init__(self, websocket, username=None, room_id=None, password=None, room_name=None):
        self.websocket = websocket
        self.username = username
        self.password = password
        self.room_id = room_id
        self.room_name = room_name

class ClientInfo:
    def __init__(self, username, password, room_id=None, status=None, in_call=False):
        self.username = username
        self.password = password
        self.room_id = room_id
        self.status = status if status is not None else Status.OFFLINE.value
        self.in_call = in_call

    def to_json(self):
        return {
            "username": self.username,
            "room_id": self.room_id,
            "password": self.password,
            "status": self.status,
            "in_call": self.in_call
        }

class Status(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"

class Room:
    def __init__(self, client_list=[]):
        self.client_list = client_list

class RoomInfo:
    def __init__(self, room_id, room_name):
        self.room_id = room_id
        self.room_name = room_name

    def to_json(self):
        return {
            "room_id": self.room_id,
            "room_name": self.room_name
        }

def generate_unique_id():
    uuid_val = str(uuid.uuid4())
    while uuid_val in uuid_list:
        uuid_val = str(uuid.uuid4())
    uuid_list.append(uuid_val)
    return uuid

async def create_user(request):
    data = await request.json()
    new_username = data.get('username')
    new_password = data.get('password')

    existing_client = client_dict.get(request.remote)
    if existing_client:
        return web.json_response({'message': 'Usuário já existente'}, status=400)

    # Criar um novo cliente
    new_client = Client(request.remote, new_username, new_password)
    client_dict[request.remote] = new_client

    client_info = ClientInfo(new_username, new_password)
    map_clients[new_username] = client_info

    return web.json_response({'message': 'Usuário criado com sucesso'})

async def login(request):
    data = await request.json()
    username = data.get('username')
    password = data.get('password')

    existing_client = client_dict.get(request.remote)
    if existing_client and existing_client.username == username:
        if existing_client.password == password:
            return web.json_response({'message': 'Login bem-sucedido'})
        else:
            return web.json_response({'message': 'Senha incorreta'}, status=401)
    else:
        return web.json_response({'message': 'Usuário não encontrado'}, status=404)

async def get_user(request):
    request_user = request.headers.get('Username')
    users_data = [client.to_json() for client in client_dict.values() if client.username != request_user]
    return web.json_response(users_data)

async def get_rooms(request):
    rooms_info = []
    for room_key, _ in map_rooms.items():
        room_id, room_name = room_key
        room_info = RoomInfo(room_id, room_name)
        rooms_info.append(room_info.to_json())

    return web.json_response(rooms_info)

async def join_room(request):
    data = await request.json()
    client_username = data.get('username')
    room_id = data.get('room_id')

    client = client_dict.get(client_username)
    if client.room_id is not None:
        return web.json_response({'message': 'Já está em uma sala', 'success': False}, status=400)

    if room_id not in map_room_id_to_client_list:
        return web.json_response({'message': 'Sala não existe', 'success': False}, status=404)

    client.room_id = room_id
    client_info = map_clients.get(client_username)
    client_info.room_id = room_id
    client_info.status = Status.ONLINE.value

    # Adicionar o cliente à sala
    map_room_id_to_client_list[room_id].append(client)

    return web.json_response({'message': 'Entrou na sala com sucesso', 'success': True})

async def send_message(request):
    data = await request.json()
    sender_username = data.get('username')
    content = data.get('content')

    # Verificar se o remetente está em uma sala
    sender = client_dict.get(sender_username)
    if sender.room_id is None:
        return web.json_response({'message': 'Usuário não está em uma sala', 'success': False}, status=400)

    # Obter informações do remetente
    room_id = sender.room_id

    # Enviar mensagem para todos os clientes na sala, exceto o remetente
    for client in map_room_id_to_client_list[room_id]:
        if client.username != sender_username:
            message_content = f"@{sender_username}: {content}"
            await send_content_to_client(client.username, message_content)

    return web.json_response({'message': 'Mensagem enviada com sucesso', 'success': True})

async def send_content_to_client(username, content):
    # Endpoint para enviar o conteúdo ao cliente
    client_url = f"http://localhost:5000/receive_content"
    data = {'content': content}

    async with aiohttp.ClientSession() as session:
        async with session.post(client_url, json=data) as response:
            if response.status != 200:
                print(f"Falha ao enviar conteúdo para {username}")


async def send_image(request):
    data = await request.json()
    sender_username = data.get('sender_username')
    image_frame = data.get('image_frame')

    # Verificar se o remetente está em uma sala
    sender = client_dict.get(sender_username)
    if sender.room_id is None:
        return web.json_response({'message': 'Usuário não está em uma sala', 'success': False}, status=400)

    # Obter informações do remetente
    room_id = sender.room_id

    # Enviar a imagem para todos os clientes na sala, exceto o remetente
    for client in map_room_id_to_client_list.get(room_id, []):
        if client.username != sender_username:
            # Enviar a imagem para o cliente específico
            await send_image_to_client(client.username, image_frame)

    return web.json_response({'message': 'Imagem enviada com sucesso para a sala'})

async def send_image_to_client(username, image_frame):
    image_bytes = base64.b64decode(image_frame)

    client_url = f"http://localhost:5000/receive_image"
    data = {'image_frame': image_bytes}

    async with aiohttp.ClientSession() as session:
        async with session.post(client_url, json=data) as response:
            if response.status != 200:
                print(f"Falha ao enviar conteúdo para {username}")

async def send_audio(request):
    data = await request.json()
    sender_username = data.get('sender_username')
    audio_frame = data.get('audio_frame')

    # Verificar se o remetente está em uma sala
    sender = client_dict.get(sender_username)
    if sender.room_id is None:
        return web.json_response({'message': 'Usuário não está em uma sala', 'success': False}, status=400)

    # Obter informações do remetente
    room_id = sender.room_id

    # Enviar a imagem para todos os clientes na sala, exceto o remetente
    for client in map_room_id_to_client_list.get(room_id, []):
        if client.username != sender_username:
            # Enviar a imagem para o cliente específico
            await send_audio_to_client(client.username, audio_frame)

    return web.json_response({'message': 'Imagem enviada com sucesso para a sala'})

async def send_audio_to_client(username, audio_frame):
    client_url = f"http://localhost:5000/receive_audio"
    data = {'audio_frame': audio_frame}

    async with aiohttp.ClientSession() as session:
        async with session.post(client_url, json=data) as response:
            if response.status != 200:
                print(f"Falha ao enviar áudio para {username}")

async def create_rooms(app):
    # Lógica para criar as salas inicialmente
    room_names = ["Sala 1", "Sala 2", "Sala 3"]

    for room_name in room_names:
        room_id = generate_unique_id()
        room = Room(client_list=[])
        map_room_id_to_client_list[room_id] = room.client_list
        map_rooms[(room_id, room_name)] = room.client_list

        print(f"Sala '{room_name}' criada com ID: {room_id}")

async def start_server():
    app = web.Application()

    # Registrar a função create_initial_rooms no evento on_startup
    app.on_startup.append(create_rooms)

    # Iniciar o servidor
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
    ssl_context.set_alpn_protocols(['h2'])

    runner = web.AppRunner(app, ssl_context=ssl_context)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8443, ssl_context=ssl_context)
    await site.start()

app = web.Application()
app.router.add_post('/create_user', create_user)
app.router.add_get('/get_user', get_user)
app.router.add_post('/create_room', create_rooms)
app.router.add_get('/get_rooms', get_rooms)
app.router.add_get('/join_room', join_room)
app.router.add_get('/login', login)
app.router.add_get('/send_message', send_message)
app.router.add_get('/send_image', send_image)
app.router.add_get('/send_audio', send_audio)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server())
    loop.run_forever()
