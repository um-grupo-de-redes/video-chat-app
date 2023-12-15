FROM python:3.11-alpine

RUN python3 -m pip install --no-cache-dir pip==23.3.*
COPY requirements.txt /tmp
RUN python3 -m pip install --default-timeout=300 --no-cache-dir -r /tmp/requirements.txt

COPY __init__.py .
COPY constants.py .
# COPY codec_img.py .
# COPY codec_audio.py .
COPY msgs.py .
COPY server.py .

CMD ["python3", "server.py", "--ip", "0.0.0.0", "--port", "8005"]
