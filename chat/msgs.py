import json

from constants import *


class Message(object):
    encoding = "utf-8"

    def __init__(self, action, type_):
        self.action = action
        self.type_ = type_

    def to_json(self):
        return json.dumps(self.__dict__)

    def encode(self):
        # msg = Message(type_=10)
        # data = msg.encode()
        return bytes(self.to_json(), encoding=self.encoding)

    @classmethod
    def from_json(self, data):
        data = json.loads(data)
        type_ = data['type_']
        msg = TYPE_TO_MSG[type_](**data)
        return msg

    @classmethod
    def decode(self, data):
        # msg = Message.decode(data)
        return self.from_json(data.decode(self.encoding))


class MessageContent(Message):
    def __init__(self, action, content, type_=TYPE_MESSAGE_CONTENT):
        super().__init__(action=action, type_=type_)
        self.content = content


class MessageRoom(Message):
    def __init__(self, action, room_id, type_=TYPE_MESSAGE_ROOM):
        super().__init__(action=action, type_=type_)
        self.room_id = room_id


class MessageRooms(Message):
    def __init__(self, action, rooms, type_=TYPE_MESSAGE_ROOMS):
        super().__init__(action=action, type_=type_)
        self.rooms = rooms


class MessageUsers(Message):
    def __init__(self, action, users, type_=TYPE_MESSAGE_USERS):
        super().__init__(action=action, type_=type_)
        self.users = users


class MessageLogin(Message):
    def __init__(self, action, username, password, type_=TYPE_MESSAGE_LOGIN):
        super().__init__(action=action, type_=type_)
        self.username = username
        self.password = password


class MessageBoolean(Message):
    def __init__(self, action, boolean, type_=TYPE_MESSAGE_BOOLEAN):
        super().__init__(action=action, type_=type_)
        self.boolean = boolean


class MessageImageFrame(Message):
    def __init__(self, action, frame, sender, type_=TYPE_MESSAGE_IMAGE_FRAME):
        super().__init__(action=action, type_=type_)
        self.frame = frame
        self.sender = sender


class MessageAudioFrame(Message):
    def __init__(self, action, frame, sender, type_=TYPE_MESSAGE_AUDIO_FRAME):
        super().__init__(action=action, type_=type_)
        self.frame = frame
        self.sender = sender

TYPE_TO_MSG = {
    TYPE_MESSAGE_CONTENT: MessageContent,
    TYPE_MESSAGE_ROOM: MessageRoom,
    TYPE_MESSAGE_ROOMS: MessageRooms,
    TYPE_MESSAGE_USERS: MessageUsers,
    TYPE_MESSAGE_LOGIN: MessageLogin,
    TYPE_MESSAGE_BOOLEAN: MessageBoolean,
    TYPE_MESSAGE_IMAGE_FRAME: MessageImageFrame,
    TYPE_MESSAGE_AUDIO_FRAME: MessageAudioFrame,
}

