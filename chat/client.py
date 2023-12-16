import time
import traceback
import argparse
from threading import Thread, Lock
from functools import partial

import cv2
import sounddevice as sd
import numpy as np

from websockets.sync.client import connect
from websockets.exceptions import ConnectionClosedOK

from msgs import *
from codec_img import encode_image, decode_image
from codec_audio import encode_audio_raw, decode_audio

stopped_g = False
sender_audio_dict_lock = Lock()

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
def check_login(websocket, username, password):
    send_message(
        websocket=websocket,
        message=MessageLogin(action=ACTION_CHECK_LOGIN, username=username, password=password)
    )
    message = receive_message(websocket)
    if isinstance(message, MessageContent):
        return message.content
    ok = message.boolean
    return ok  # wether the username is ok (e.g is not a duplicate)

def show_rooms(websocket):
    send_message(
        websocket=websocket,
        message=MessageRoom(action=ACTION_SHOW_ROOM, room_id=None)
    )
    message = receive_message(websocket)
    return message.rooms

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

def send_image_frame(websocket, frame):
    frame = encode_image(frame)
    send_message(
        websocket=websocket,
        message=MessageImageFrame(action=ACTION_IMAGE_FRAME, frame=frame, sender=None)  # the server already knows the sender username
    )

def send_audio_frame(websocket, frame):
    frame = encode_audio_raw(frame)
    send_message(
        websocket=websocket,
        message=MessageAudioFrame(action=ACTION_AUDIO_FRAME, frame=frame, sender=None)  # the server already knows the sender username
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
        send_image_frame(websocket, frame)
        time.sleep(max((1 / video_fps) - time.time() + start_time, 0))  # TODO: substitute with ensure_loop_rate()

# Send audio frames
warned_input_overflow = False
def audio_input_stream_cb(indata, frames, timeobj, status, websocket):
    global warned_input_overflow
    if status.input_overflow and not warned_input_overflow:
        warned_input_overflow = True
        print('WARNING: INPUT OVERFLOW')
    send_audio_frame(websocket, indata[:])

# Play audio in parallel
sender_audio_dict = {}

def play_audio_in_parallel(audio_output_stream):
    global stopped_g
    global sender_audio_dict, sender_audio_dict_lock

    audio_output_stream.start()

    frame = np.zeros((audio_output_stream.blocksize, 1), dtype=np.float32)
    while not stopped_g:
        i = 0
        frame[::] = 0
        sender_audio_dict_lock.acquire()
        for sender, v in sender_audio_dict.items():
            if v['played']:
                continue
            i += 1
            frame += decode_audio(v['frame'])
            sender_audio_dict[sender]['played'] = True
        sender_audio_dict_lock.release()
        if i > 0:
            frame /= i
            print("playing")
            audio_output_stream.write(frame)

# Receive all messages (text, video and audio), printing text and showing videos
def message_handler(websocket):
    global stopped_g
    global sender_audio_dict, sender_audio_dict_lock
    while not stopped_g:
        try:
            message = receive_message(websocket)
            if message is None:
                continue
            elif message.action == ACTION_CONTENT:
                print(message.content)
            elif message.action == ACTION_IMAGE_FRAME:
                if type(message.sender) == str:
                    sender = message.sender[:15]
                else:
                    continue
                frame = decode_image(message.frame)
                # TODO: a grid instead of multiple windows
                cv2.imshow(sender, frame)
                cv2.waitKey(1)  # milliseconds
            elif message.action == ACTION_AUDIO_FRAME:
                if type(message.sender) == str:
                    sender = message.sender[:15]
                else:
                    continue
                # Support multiple senders
                sender_audio_dict_lock.acquire()
                if message.sender not in sender_audio_dict.keys():
                    sender_audio_dict[message.sender] = {}
                sender_audio_dict[message.sender]['frame'] = message.frame[:]
                sender_audio_dict[message.sender]['played'] = False
                sender_audio_dict_lock.release()
        except TimeoutError:
            pass

# Chat application
def finite_state_machine(websocket, video_source, video_fps, audio_input_stream, audio_output_stream, chat_active):
    global stopped_g
    reached_in_room_state = False
    state = STATE_LOGIN
    while not stopped_g:
        if state == STATE_LOGIN:
            print("LOGIN")
            print("Type your username (if you don't have one, will be created): ")
            username = input()
            print("Type your password: ")
            password = input()
            ok = check_login(websocket, username, password)
            if ok == "Incorrect password":
                print("Error: incorrect password\n")
                state = STATE_LOGIN
                continue
            if not ok:
                print("Error: choose another username\n")
                state = STATE_LOGIN
                continue
            state = STATE_SHOW_OPTIONS
            continue
        elif state == STATE_SHOW_OPTIONS:
            print('\n')
            print("Available rooms: ")
            rooms = show_rooms(websocket=websocket)
            if not rooms:
                print("No available rooms!")
                break
            for room in rooms:
                room_name = room['room_name']
                room_id = room['room_id']
                print(f'Nome da sala: {room_name}, ID da sala: {room_id}\n')
            state = STATE_JOIN
            continue
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
                # Start input devices
                if video_source is not None:
                    print("Started sending video")
                    send_video_thread = Thread(
                        target=send_video_in_parallel,
                        args=(websocket, video_source, video_fps, )
                    )
                    send_video_thread.start()
                if audio_input_stream is not None:
                    audio_input_stream.start()
                # Start output device(s)
                if audio_output_stream is not None:
                    play_audio_thread = Thread(
                        target=play_audio_in_parallel,
                        args=(audio_output_stream, )
                    )
                    play_audio_thread.start()
                # Start receiving room messages in parallel
                if chat_active:
                    receiver_thread = Thread(
                        target=message_handler,
                        args=(websocket, )
                    )
                    receiver_thread.start()
            content = input()  # blocks waiting for input
            send_content(websocket, content)


def main(stream_video, stream_audio, play_audio, server_uri, video_device, video_fps, audio_device, audio_sample_size, audio_sample_rate):
    global stopped_g
    try:
        websocket = None
        video_source = None
        audio_input_stream = None
        audio_output_stream = None
        valid_option = False
        websocket = connect(server_uri)  # establish a connection
        while not valid_option:
            print("Choose dialogue option: ")
            print("(1) Only chat")
            print("(2) Only stream")
            print("(3) Both chat and stream")
            option = input()
            if option == '1':
                stream_video = False
                stream_audio = False
                chat_active = True
                valid_option = True
            elif option == '2':
                stream_video = True
                stream_audio = True
                chat_active = False
                valid_option = True
            elif option == '3':
                stream_video = True
                stream_audio = True
                chat_active = True
                valid_option = True
            else:
                print("Error: invalid option\n")
        if stream_video:
            print("Started capturing video")
            video_source = cv2.VideoCapture(video_device)
        if stream_audio:
            print("Started capturing audio")
            audio_input_stream = sd.RawInputStream(
                blocksize=audio_sample_size,
                samplerate=audio_sample_rate,
                channels=1,
                dtype=np.int16,
                callback=partial(audio_input_stream_cb, websocket=websocket),
            )
        if play_audio:
            audio_output_stream = sd.Stream(
                blocksize=audio_sample_size,
                samplerate=audio_sample_rate,
                channels=1,
                dtype=np.float32,
                latency=None,
            )
        finite_state_machine(websocket, video_source, video_fps, audio_input_stream, audio_output_stream, chat_active)
    except:
        if DEBUG:
            traceback.print_exc()
        print("An error happened. Restart the app.")
    finally:
        print("Closing...")
        stopped_g = True
        if websocket is not None:
            websocket.close()
        if video_source is not None:
            video_source.release()
        if audio_input_stream is not None:
            audio_input_stream.abort()  # audio_input_stream.stop()
            audio_input_stream.close()
        if audio_output_stream is not None:
            audio_output_stream.abort()  # audio_output_stream.stop()
            audio_output_stream.close()
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
        "--stream-audio",
        action='store_true', default=False,
        help="Wether to stream audio to the room. Can still receive audio"
    )
    ap.add_argument(
        "--play-audio",
        action='store_true', default=False,
        help="Wether to play audio from the room"
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
    ap.add_argument(
        "--audio-device",
        type=str, default=None,
        help="Which device to get the audio from"
    )
    ap.add_argument(
        "--audio-sample-size",
        type=int, default=512,
        help="How many integers to send each time"
    )
    ap.add_argument(
        "--audio-sample-rate",
        type=int, default=16000,
        help="Audio frames per second"
    )
    args = ap.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    main(**vars(args))

