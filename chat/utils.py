import asyncio
from functools import wraps, partial
import uuid
from enum import Enum

from msgs import Message
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError


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


uuid_list = []

def generate_unique_id():
    uuid_val = uuid.uuid4()
    while uuid_val in uuid_list:
        uuid_val = uuid.uuid4()
    uuid_list.append(uuid_val)
    return str(uuid_val)

def async_wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)
    return run 
