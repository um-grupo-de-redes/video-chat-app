from flask import Flask, request, jsonify

app = Flask(__name__)

# Variável global para armazenar o conteúdo recebido
content = None
image_content = None
audio_content = None

@app.route('/receive_content', methods=['POST'])
def receive_content():
    global content
    content = request.json.get('content')
    print(f"Conteúdo recebido")
    return jsonify({'message': 'Conteúdo recebido com sucesso'})

@app.route('/receive_image', methods=['POST'])
def receive_image():
    global image_content
    image_content = request.json.get('image_frame')
    print(f"Conteúdo da imagem recebido")
    return jsonify({'message': 'Imagem recebida com sucesso'})

@app.route('/receive_audio', methods=['POST'])
def receive_audio():
    global audio_content
    audio_content = request.json.get('audio_frame')
    print(f"Conteúdo do áudio recebido")
    return jsonify({'message': 'Áudio recebido com sucesso'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
