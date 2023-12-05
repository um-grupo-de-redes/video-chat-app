import simplejpeg
import base64


def encode_image(frame, quality=85):
    frame = simplejpeg.encode_jpeg(
        frame,
        quality=quality,
        colorspace='BGR',
        colorsubsampling='444',
        fastdct=True,
    )
    frame = base64.b64encode(frame)
    # Convert from bytes to str
    frame = frame.decode()
    return frame


def decode_image(frame):
    frame = base64.b64decode(frame)
    frame = simplejpeg.decode_jpeg(
        frame,
        colorspace='BGR',
        fastdct=False,
        fastupsample=False,
        min_height=0,
        min_width=0,
        min_factor=1,
        strict=True,
    )
    return frame


if __name__ == "__main__":
    import cv2
    frame = "test.png"
    frame = cv2.imread(frame)
    assert frame.shape == (152, 174, 3)
    frame = encode_image(frame)
    frame = decode_image(frame)
    assert frame.shape == (152, 174, 3)
