import base64
from io import BytesIO
from PIL import Image


def base64_image_validation(base64_str: str):
    try:
        if base64_str.startswith('data:image'):
            base64_str = base64_str.split(',')[1]

        # Tenta decodificar a string Base64
        image_data = base64.b64decode(base64_str)

        # Tenta abrir a imagem com PIL (Pillow)
        image = Image.open(BytesIO(image_data))

        image.verify()  # Verifica se a imagem é válida

        return True
    except:
        return False


if __name__ == '__main__':
    # print(base64_image_validation(''))
    pass
