import time
import traceback
import argparse
from threading import Thread, Lock

from websockets.sync.client import connect

from msgs import *

stopped_g = False

# Message sending
def send_message(websocket, message):
    message = message.to_json()
    websocket.send(message)

def check_username(websocket, username):
    send_message(
        websocket=websocket,
        message=MessageUsername(action=ACTION_CHECK_USERNAME, username=username)
    )
    message = websocket.recv()
    message = Message.from_json(message)
    ok = message.boolean
    return ok  # wether the username is ok (e.g is not a duplicate)

def request_new_room(websocket):
    send_message(
        websocket=websocket,
        message=MessageRoom(action=ACTION_CREATE_ROOM, room_id=None)
    )
    message = websocket.recv()
    message = Message.from_json(message)
    return message.room_id

def join_room(websocket, room_id):
    send_message(
        websocket=websocket,
        message=MessageRoom(action=ACTION_JOIN_ROOM, room_id=room_id)
    )
    message = websocket.recv()
    message = Message.from_json(message)
    joined = message.boolean
    return joined

# Receive chat messages
def receive_content_in_parallel(websocket):
    while not stopped_g:
        try:
            message = websocket.recv()
            message = Message.from_json(message)
            if message.action != ACTION_CONTENT:
                continue
            print(message.content)
        except TimeoutError:
            pass

def finite_state_machine(websocket):
    reached_in_room_state = False
    state = STATE_CHOOSE_USERNAME
    while not stopped_g:
        if state == STATE_CHOOSE_USERNAME:
            print("Choose your username:")
            username = input()
            ok = check_username(websocket, username)
            if not ok:
                print("Error: choose another username\n")
                state = STATE_CHOOSE_USERNAME
                continue
            state = STATE_SHOW_OPTIONS
            continue
        elif state == STATE_SHOW_OPTIONS:
            print("Options:")
            print("(1) Create a room")
            print("(2) Join an existing room")
            option = input()
            if option == '1':
                state = STATE_CREATE
                continue
            elif option == '2':
                state = STATE_JOIN
                continue
            else:
                print("Error: invalid option\n")
                continue
        elif state == STATE_CREATE:
            room_id = request_new_room(websocket=websocket)
            if room_id is None:
                print("Error: error creating room\n")
                state = STATE_SHOW_OPTIONS
                continue
            state = STATE_IN_ROOM
        elif state == STATE_JOIN:
            print("Write the room's ID:")
            room_id = input()
            if ((room_id is None) or (room_id == "")):
                print("Error: Room ID is empty\n")
                state = STATE_JOIN
                continue
            joined = join_room(websocket=websocket, room_id=room_id)
            if not joined:
                print("Error: Failed to join room\n")
                state = STATE_SHOW_OPTIONS
                continue
            state = STATE_IN_ROOM
        elif state == STATE_IN_ROOM:
            # There's no encryption/obfuscation whatsoever.
            if not reached_in_room_state:
                reached_in_room_state = True
                print("The joined room ID is:", room_id)
                # Start receiving room messages in parallel
                receiver_thread = Thread(
                    target=receive_content_in_parallel,
                    args=(websocket, )
                )
                receiver_thread.start()
            content = input()  # blocks waiting for input
            send_message(
                websocket=websocket,
                message=MessageContent(action=ACTION_CONTENT, content=content)
            )


def main(ip, port):
    try:
        websocket = connect(f"ws://{ip}:{port}")  # establish a connection
        finite_state_machine(websocket)
    except:
        if DEBUG:
            traceback.print_exc()
        print("An error happened. Restart the app.")
    finally:
        print("Closing...")
        stopped_g = True
        websocket.close()
        exit()
    
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

