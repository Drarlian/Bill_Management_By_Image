import google.generativeai as genai
import base64
import os

from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEY = os.getenv('GEMINI_KEY')


def convert_base64_to_image(base64_image: str):
    if base64_image.startswith('data:image'):
        base64_image = base64_image.split(',')[1]

    bytes_image = base64.b64decode(base64_image)
    buffer = BytesIO(bytes_image)
    image = Image.open(buffer)

    return image


def validate_image_with_gemini(base64_image: str):
    image = convert_base64_to_image(base64_image)

    genai.configure(api_key=GEMINI_KEY)

    model = genai.GenerativeModel('gemini-1.5-flash')

    response = model.generate_content(["Identifique o valor do documento na imagem a seguir: OBS: Responda apenas o valor no padrão float. ", image],
                                      stream=True)
    response.resolve()
    return response.text


if __name__ == '__main__':
    # print(validate_image_with_gemini(''))
    pass
