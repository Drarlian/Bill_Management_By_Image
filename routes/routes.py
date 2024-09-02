from fastapi import APIRouter
from starlette.responses import JSONResponse

from functions.validation_functions.validations import base64_image_validation
import functions.db_functions.db_manipulation as db_functions
from functions.gemini_functions.gemini_manipulation import validate_image_with_gemini
from entities.entities import Upload, ConfirmBody

from datetime import datetime
from typing import Optional


router = APIRouter()


@router.post('/upload')
def receive_image(informations: Upload):
    """
    Enpoint responsável por receber uma imagem em base 64, consultar o Gemini e retornar a medida lida pela API.
    :param informations:
    :return:
    """
    informations = dict(informations)

    if not base64_image_validation(informations['image']):
        return JSONResponse(status_code=400, content={"error_code": "INVALID_DATA",
                                                      "error_description": 'Image is not base64'})

    if informations['measure_type'] not in ['WATER', 'GAS']:
        return JSONResponse(status_code=400, content={"error_code": "INVALID_DATA",
                                                      "error_description": 'Invalid measure type'})

    # PESQUIAR NO BANCO SE O CÓDIGO DE USUARIO INFORMADO REALMENTE EXISTE
    if not db_functions.find_one_user_by_code(informations['customer_code']):
        return JSONResponse(status_code=400, content={"error_code": "INVALID_DATA",
                                                      "error_description": 'Customer code does not exist'})

    # VERIFICAR SE A DATA RECEBIDA ESTA NO FARMATO DATETIME
    if not isinstance(informations['measure_datetime'], datetime):
        return JSONResponse(status_code=400, content={"error_code": "INVALID_DATA",
                                                      "error_description": 'Invalid measure datetime'})

    # VERIFICAR NO BANCO SE EXISTE UMA VERIFICAÇÃO FEITA NO MES ATUAL
    if not db_functions.find_one_measure_by_date_and_type_and_id(informations['customer_code'],
                                                                 informations['measure_type'],
                                                                 informations['measure_datetime']):
        return JSONResponse(status_code=409, content={"error_code": "DOUBLE_REPORT",
                                                      "error_description": "Leitura do mês já realizada"})

    # ENVIAR A IMAGEM BASE64 RECEBIDA PARA O GEMINI OBTER O NÚMERO DA FATURA DE AGUA/GAS
    gemini_response: str = validate_image_with_gemini(informations['image'])
    if gemini_response:
        # INSERIR AS INFORMAÇÕES RECEBIDAS DA REQUISIÇÃO E DO GEMINI NO BANCO DE DADOS
        uuid = db_functions.insert_one_measure(
            {'image': informations['image'], 'customer_code': informations['customer_code'],
             'measure_datetime': informations['measure_datetime'],
             'measure_type': informations['measure_type'], 'value': gemini_response, "confirmed": 0})

        return JSONResponse(status_code=200, content={"image_url": "URL_DA_IMAGEM", "measure_value": gemini_response,
                                                      "measure_uuid": uuid})


@router.patch('/confirm')
def confirm_measure_value(informations: ConfirmBody):
    try:
        informations = dict(informations)
        exist_response = db_functions.find_one_measure_by_uuid(informations['measure_uuid'])

        if type(informations['measure_uuid']) is not str or type(informations['confirmed_value']) is not float:
            return JSONResponse(status_code=400, content={"error_code": "INVALID_DATA",
                                                          "error_description": "Tipo de dado inválido"})

        if not exist_response:  # -> Caso não exista o uuid informado na tabela
            return JSONResponse(status_code=404, content={"error_code": "MEASURE_NOT_FOUND",
                                                          "error_description": "Leitura não encontrada"})

        confirmed_response = db_functions.check_confirm_measure(informations['measure_uuid'])

        if confirmed_response:
            return JSONResponse(status_code=409, content={"error_code": "CONFIRMATION_DUPLICATE",
                                                          "error_description": "Leitura do mês já realizada"})

        final_response = db_functions.confirm_measure(informations['measure_uuid'], informations['confirmed_value'])

        if final_response:
            return JSONResponse(status_code=200, content={"success": True})
        else:
            return JSONResponse(status_code=400, content={"error_code": "Erro interno durante a confirmação"})

    except:
        return JSONResponse(status_code=400, content={"error_code": "Erro interno"})


@router.get('/{customer_code}/list')
def get_all_customers(customer_code: str, measure_type: Optional[str] = None):
    """
    Endpoint responsável por listar as medidas realizadas por um determinado cliente.
    :param customer_code: ID do usuário na tabela de measures.
    :param measure_type: Tipo de measure, podendo ser APENAS WATER ou GAS.
    :return:
    """
    try:
        if measure_type and measure_type not in ['WATER', 'GAS']:
            return JSONResponse(status_code=400, content={"error_code": "INVALID_TYPE",
                                                          "error_description": "Tipo de medição não permitida"})

        measures: dict | None = db_functions.find_all_measures_by_user_code(customer_code, measure_type)

        if len(measures["measures"]) == 0:
            return JSONResponse(status_code=404, content={"error_code": "MEASURES_NOT_FOUND",
                                                          "error_description": "Nenhuma leitura encontrada"})

        return JSONResponse(status_code=200, content=measures)
    except:
        return JSONResponse(status_code=400, content={"error_code": "Erro interno"})
