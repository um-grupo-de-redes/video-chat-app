import uuid
import traceback
import argparse

import asyncio
from websockets.server import serve
from websockets.exceptions import ConnectionClosedOK

from msgs import *


class Client:
    def __init__(self, websocket, username=None, room_id=None):
        self.websocket = websocket
        self.username = username
        self.room_id = room_id

class Room:
    def __init__(self, client_list=[]):
        self.client_list = client_list

def generate_unique_id():
    # TODO: assert is unique
    return str(uuid.uuid4())


async def send_message(websocket, message):
    message = message.to_json()
    try:
        await websocket.send(message)
    except ConnectionClosedOK:
        pass

client_dict = {}
map_room_id_to_client_list = {}

async def message_handler(websocket):
    client_dict[websocket] = Client(websocket)
    try:
        # TODO: maybe rate limit, at this layer, to avoid DDoS
        async for message in websocket:
            message = Message.from_json(message)
            if message.action == ACTION_CHECK_USERNAME:
                # Check if username exists
                username_exists = False
                for client in client_dict.values():
                    if client.username == message.username:
                        username_exists = True
                        break
                if username_exists:
                    await send_message(websocket, MessageBoolean(action=ACTION_CHECK_USERNAME, boolean=False))
                    continue
                # Check if there's already a username for that client
                if client_dict[websocket].username is not None:
                    await send_message(websocket, MessageBoolean(action=ACTION_CHECK_USERNAME, boolean=False))
                    continue
                # Create username
                client_dict[websocket].username = message.username
                await send_message(websocket, MessageBoolean(action=ACTION_CHECK_USERNAME, boolean=True))
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
    except:
        if DEBUG:
            traceback.print_exc()
        print("An error happened. Restart the server.")
    finally:
        del client_dict[websocket]

async def spin_server(ip, port):
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

