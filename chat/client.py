import time
import traceback
import argparse
from threading import Thread

import cv2
from websockets.sync.client import connect
from websockets.exceptions import ConnectionClosedOK

from msgs import *
from img_codec import *

stopped_g = False

# Basic message sending/receiving
def receive_message(websocket):
    try:
        message = websocket.recv()
    except ConnectionClosedOK:
        return None
    message = Message.from_json(message)
    return message

def send_message(websocket, message):
    message = message.to_json()
    try:
        websocket.send(message)
    except ConnectionClosedOK:
        pass

# Specific message sending/receiving
def check_username(websocket, username):
    send_message(
        websocket=websocket,
        message=MessageUsername(action=ACTION_CHECK_USERNAME, username=username)
    )
    message = receive_message(websocket)
    ok = message.boolean
    return ok  # wether the username is ok (e.g is not a duplicate)

def request_new_room(websocket):
    send_message(
        websocket=websocket,
        message=MessageRoom(action=ACTION_CREATE_ROOM, room_id=None)
    )
    message = receive_message(websocket)
    return message.room_id

def join_room(websocket, room_id):
    send_message(
        websocket=websocket,
        message=MessageRoom(action=ACTION_JOIN_ROOM, room_id=room_id)
    )
    message = receive_message(websocket)
    joined = message.boolean
    return joined

def send_content(websocket, content):
    send_message(
        websocket=websocket,
        message=MessageContent(action=ACTION_CONTENT, content=content)
    )

def send_frame(websocket, frame):
    frame = encode_image(frame)
    send_message(
        websocket=websocket,
        message=MessageFrame(action=ACTION_FRAME, frame=frame, sender=None)  # the server already knows the sender username
    )

# Send video frames
def send_video_in_parallel(websocket, video_source, video_fps):
    global stopped_g
    while not stopped_g:
        start_time = time.time()
        ret, frame = video_source.read()
        if not ret:
            print("Failed to read camera")
            time.sleep(max((1 / video_fps) - time.time() + start_time, 0))  # TODO: substitute with ensure_loop_rate()
            continue
        send_frame(websocket, frame)
        time.sleep(max((1 / video_fps) - time.time() + start_time, 0))  # TODO: substitute with ensure_loop_rate()

# Receive messages, and print chat messages to the screen
def message_handler(websocket):
    global stopped_g
    while not stopped_g:
        try:
            message = receive_message(websocket)
            if message.action == ACTION_CONTENT:
                print(message.content)
            elif message.action == ACTION_FRAME:
                if type(message.sender) == str:
                    sender = message.sender[:15]
                else:
                    continue
                frame = decode_image(message.frame)
                # TODO: a grid instead of multiple windows
                cv2.imshow(sender, frame)
                cv2.waitKey(1)  # milliseconds
        except TimeoutError:
            pass

# Chat application
def finite_state_machine(websocket, video_source, video_fps):
    global stopped_g
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
                    target=message_handler,
                    args=(websocket, )
                )
                receiver_thread.start()
                if video_source is not None:
                    print("Started sending video")
                    send_video_thread = Thread(
                        target=send_video_in_parallel,
                        args=(websocket, video_source, video_fps, )
                    )
                    send_video_thread.start()
            content = input()  # blocks waiting for input
            send_content(websocket, content)


def main(stream_video, server_uri, video_device, video_fps):
    global stopped_g
    try:
        websocket = connect(server_uri)  # establish a connection
        video_source = None
        if stream_video:
            print("Started capturing video")
            video_source = cv2.VideoCapture(video_device)
        finite_state_machine(websocket, video_source, video_fps)
    except:
        if DEBUG:
            traceback.print_exc()
        print("An error happened. Restart the app.")
    finally:
        print("Closing...")
        stopped_g = True
        websocket.close()
        video_source.release()
        cv2.destroyAllWindows()
        exit()
    
def parse_args():
    ap = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    ap.add_argument(
        "--stream-video",
        action='store_true', default=False,
        help="Wether to stream video to the room. Can still receive video"
    )
    ap.add_argument(
        "--server-uri",
        type=str, default="ws://localhost:8005",
        help="Websocket server URI (like 'wss://18.231.183.136.sslip.io')"
    )
    ap.add_argument(
        "--video-device",
        type=str, default="/dev/video0",
        help="Which device to get the video from"
    )
    ap.add_argument(
        "--video-fps",
        type=int, default=24,
        help="Video frames per second"
    )
    args = ap.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    main(**vars(args))

