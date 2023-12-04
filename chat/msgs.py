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


class MessageUsername(Message):
    def __init__(self, action, username, type_=TYPE_MESSAGE_USERNAME):
        super().__init__(action=action, type_=type_)
        self.username = username


class MessageBoolean(Message):
    def __init__(self, action, boolean, type_=TYPE_MESSAGE_BOOLEAN):
        super().__init__(action=action, type_=type_)
        self.boolean = boolean


TYPE_TO_MSG = {
    TYPE_MESSAGE_CONTENT: MessageContent,
    TYPE_MESSAGE_ROOM: MessageRoom,
    TYPE_MESSAGE_USERNAME: MessageUsername,
    TYPE_MESSAGE_BOOLEAN: MessageBoolean,
}

