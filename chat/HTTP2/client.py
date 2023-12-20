import httpx

SERVER_URL = 'https://localhost:8443'  # Atualize com a URL do servidor

async def create_user(username, password):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{SERVER_URL}/create_user", json={"username": username, "password": password})
        return response.json()

async def login(username, password):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{SERVER_URL}/login", json={"username": username, "password": password})
        return response.json()

async def get_users():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVER_URL}/get_user")
        return response.json()

async def get_rooms():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVER_URL}/get_rooms")
        return response.json()

async def join_room(username, room_id):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVER_URL}/join_room", json={"username": username, "room_id": room_id})
        return response.json()

async def send_message(username, content):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{SERVER_URL}/send_message", json={"username": username, "content": content})
        return response.json()
    
async def send_image(username, image_frame):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{SERVER_URL}/send_image", json={"username": username, "content": image_frame})
        return response.json()
    
async def send_audio(username, audio_frame):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{SERVER_URL}/send_audio", json={"username": username, "audio_frame": audio_frame})
        return response.json()

async def main():
    username = None

    while True:
        if not username:
            print("Selecione a opção:")
            print("1. Criar usuário")
            print("2. Logar")
            print("0. Sair")
            option = int(input())

            if option == 1:
                username = input("Digite o nome de usuário: ")
                password = input("Digite a senha: ")
                result = await create_user(username, password)
                print(result)
            elif option == 2:
                username = input("Digite o nome de usuário: ")
                password = input("Digite a senha: ")
                result = await login(username, password)
                print(result)
                if result.get('message') != 'Login bem-sucedido':
                    print("Falha no login")
                    username = None
            elif option == 0:
                break
            else:
                print("Opção inválida")

        else:  # O usuário está logado
            print("Opções disponíveis:")
            print("1. Ver usuários")
            print("2. Ver salas")
            print("0. Sair")
            option = int(input())

            if option == 1:
                users = await get_users()
                print(users)
            elif option == 2:
                rooms = await get_rooms()
                print(rooms)
                print("Selecione uma sala para entrar (ou 0 para voltar):")
                room_id = int(input())
                if room_id == 0:
                    continue
                else:
                    result = await join_room(username, room_id)
                    if result.get('success'):
                        print("Opções disponíveis na sala:")
                        print("1. Enviar mensagem")
                        print("2. Iniciar chamada de vídeo")
                        print("0. Voltar")
                        room_option = int(input())

                        if room_option == 1:
                            content = input("Digite a mensagem: ")
                            await send_message(username, content)
                        elif room_option == 2:
                            # await send_image(username, image_frame)
                            # await send_audio(username, audio_frame)
                            break
                        elif room_option == 0:
                            continue
                        else:
                            print("Opção inválida")
                    else:
                        print(result.get('message'))
            elif option == 0:
                break
            else:
                print("Opção inválida")

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
