import time
import traceback
import argparse

import asyncio
from websockets.server import serve
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

from msgs import *
from utils import *

stopped_g = False

client_dict = {}
map_clients = []
map_room_id_to_client_list = {}
map_rooms = {}

# Basic message sending/receiving
async def receive_message(websocket):
    try:
        message = await websocket.recv()
    except ConnectionClosedOK:
        return None
    message = Message.from_json(message)
    return message

async def send_message(websocket, message):
    message = message.to_json()
    try:
        await websocket.send(message)
    except ConnectionClosedOK:
        pass

async def message_handler(websocket):
    global stopped_g
    client_dict[websocket] = Client(websocket)
    try:
        # TODO: maybe rate limit, at this layer, to avoid DDoS
        while not stopped_g:
            message = await receive_message(websocket)
            if message is None:
                time.sleep(0.001)
                continue
            if message.action == ACTION_CHECK_LOGIN:
                # Check if username exists
                username_exists = False
                for client in client_dict.values():
                    if client.username == message.username:
                        username_exists = True
                        break
                if username_exists:
                    if client.password != message.password:
                        content = "Incorrect password"
                        await send_message(websocket, MessageContent(action=ACTION_CHECK_LOGIN, content=content))
                    else:
                        await send_message(websocket, MessageBoolean(action=ACTION_CHECK_LOGIN, boolean=False))
                        continue
                # Check if there's already a username for that client
                if client_dict[websocket].username is not None:
                    await send_message(websocket, MessageBoolean(action=ACTION_CHECK_LOGIN, boolean=False))
                    continue
                # Create username
                client_dict[websocket].username = message.username
                client_dict[websocket].password = message.password
                client_info = ClientInfo(message.username, message.password)
                client_info = client_info.to_json()
                map_clients.append(client_info)
                await send_message(websocket, MessageBoolean(action=ACTION_CHECK_LOGIN, boolean=True))
            elif message.action == ACTION_SHOW_ROOM:
                rooms_info = []
                for room_key, _ in map_rooms.items():
                    room_id, room_name = room_key
                    room_info = RoomInfo(room_id, room_name)
                    rooms_info.append(room_info.to_json())
                await send_message(websocket, MessageRooms(action=ACTION_SHOW_ROOM, rooms=rooms_info))
            elif message.action == ACTION_SHOW_USERS:
                clients_info = []
                current_username = client.username

                for client_info in map_clients:
                    if client_info["username"] != current_username:
                        if client_info["room_id"] and not client_info["in_call"]:
                            status = Status.ONLINE.value
                            clients_info.append({
                                "username": client_info["username"],
                                "room_id": client_info["room_id"],
                                "status": status
                            })
                        elif client_info["in_call"]:
                            status = Status.BUSY.value
                            clients_info.append({
                                "username": client_info["username"],
                                "room_id": client_info["room_id"],
                                "status": status
                            })
                        else:
                            status = Status.OFFLINE.value
                            clients_info.append({
                                "username": client_info["username"],
                                "status": status
                            })

                await send_message(websocket, MessageUsers(action=ACTION_SHOW_USERS, users=clients_info))
            elif message.action == ACTION_CREATE_ROOM:
                # Check if already has room_id
                if client_dict[websocket].room_id is not None:
                    await send_message(websocket, MessageRoom(action=ACTION_CREATE_ROOM, room_id=None))
                    continue
                # Create room
                room_id = generate_unique_id()
                map_room_id_to_client_list[room_id] = [client_dict[websocket]]
                client_dict[websocket].room_id = room_id
                await send_message(websocket, MessageRoom(action=ACTION_CREATE_ROOM, room_id=client_dict[websocket].room_id))
            elif message.action == ACTION_JOIN_ROOM:
                # Check if already has room_id
                if client_dict[websocket].room_id is not None:
                    await send_message(websocket, MessageBoolean(action=ACTION_JOIN_ROOM, boolean=False))
                    continue
                # Check if room exists
                if message.room_id not in map_room_id_to_client_list:
                    await send_message(websocket, MessageBoolean(action=ACTION_JOIN_ROOM, boolean=False))
                    continue
                # Join room
                map_room_id_to_client_list[message.room_id].append(client_dict[websocket])
                client_dict[websocket].room_id = message.room_id
                current_username = client.username
                for client_info in map_clients:
                    if client_info["username"] == current_username:
                        client_info["room_id"] = message.room_id
                await send_message(websocket, MessageBoolean(action=ACTION_JOIN_ROOM, boolean=True))
            elif message.action == ACTION_CONTENT:
                room_id = client_dict[websocket].room_id
                username = client_dict[websocket].username
                # Send message to the right room
                for client in map_room_id_to_client_list[room_id]:
                    if client.username == username:
                        continue
                    await send_message(
                        client.websocket,
                        MessageContent(action=ACTION_CONTENT, content="@" + username + ": " + message.content)
                    )
            elif message.action == ACTION_IMAGE_FRAME:
                room_id = client_dict[websocket].room_id
                username = client_dict[websocket].username
                # TODO: maybe some frame validation
                # Send frame to the right room
                for client in map_room_id_to_client_list[room_id]:
                    if client.username == username:
                        continue
                    await send_message(
                        client.websocket,
                        MessageImageFrame(action=ACTION_IMAGE_FRAME, sender=username, frame=message.frame)
                    )
            elif message.action == ACTION_AUDIO_FRAME:
                room_id = client_dict[websocket].room_id
                username = client_dict[websocket].username
                # TODO: maybe some audio frame validation
                # Send audio frame to the right room
                for client in map_room_id_to_client_list[room_id]:
                    if client.username == username:
                        continue
                    await send_message(
                        client.websocket,
                        MessageAudioFrame(action=ACTION_AUDIO_FRAME, sender=username, frame=message.frame)
                    )
    except ConnectionClosedError:
        pass
    except KeyboardInterrupt:
        stopped_g = True
    except:
        if DEBUG:
            traceback.print_exc()
        print("An error happened. Restart the server.")
    finally:
        del client_dict[websocket]

async def spin_server(ip, port):
    # Creating rooms
    room1_id = generate_unique_id()
    room2_id = generate_unique_id()
    room3_id = generate_unique_id()

    # Naming the rooms
    room1_name = "Sala 1"
    room2_name = "Sala 2"
    room3_name = "Sala 3"

    room1 = Room(client_list=[])
    room2 = Room(client_list=[])
    room3 = Room(client_list=[])

    map_room_id_to_client_list[room1_id] = room1.client_list
    map_room_id_to_client_list[room2_id] = room2.client_list
    map_room_id_to_client_list[room3_id] = room3.client_list

    map_rooms[room1_id, room1_name] = room1.client_list
    map_rooms[room2_id, room2_name] = room2.client_list
    map_rooms[room3_id, room3_name] = room3.client_list

    # Inicialização com as salas já criadas
    print(f"Rooms initialized: {room1_name}, {room2_name}, {room3_name}")
    async with serve(message_handler, ip, port):
        print("Handling messages...")
        await asyncio.Future()  # run forever

def main(ip, port):
    asyncio.run(spin_server(ip, port))

def parse_args():
    ap = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    ap.add_argument(
        "--ip",
        type=str, default="localhost",
        help="IP or DNS of the websocket"
    )
    ap.add_argument(
        "--port",
        type=int, default=8005,
        help="Ephemeral port number of the websocket (1024 to 65535)"
    )
    args = ap.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    main(**vars(args))

