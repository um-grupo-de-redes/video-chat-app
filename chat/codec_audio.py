import numpy as np
import base64


###############################################################################
# ENCODING
###############################################################################

def encode_audio_raw(frame):
    # input should be already encoded as a 'bytes' object
    frame = base64.b64encode(frame)
    # Convert from 'bytes' to 'str'
    frame = frame.decode()
    return frame


###############################################################################
# DECODING
###############################################################################

def bytes_to_array(bytesobj, num_channels=1):
    """Create NumPy array from a buffer object."""
    data = np.frombuffer(bytesobj, dtype=np.int16)
    data.shape = -1, num_channels
    return data


def array_to_audioarray(arr, array_scale_factor=1/32768):  # since we are using int16
    """ Scale audio to floating point numbers between -1 and 1. """
    return arr.astype(np.float32) * array_scale_factor


def bytes_to_audioarray(bytesobj):
    return array_to_audioarray(bytes_to_array(bytesobj))


def decode_audio(frame):
    frame = base64.b64decode(frame)
    frame = bytes_to_audioarray(frame)
    return frame
