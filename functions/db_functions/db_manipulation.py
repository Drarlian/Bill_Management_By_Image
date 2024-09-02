from dotenv import load_dotenv
from datetime import datetime
import base64
import os

import psycopg2
from psycopg2 import pool

from functions.generate_functions.generate_uuid import generate_uuid

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

connection_pool = pool.SimpleConnectionPool(
    1,
    20,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    options="-c client_encoding=utf8"
)


def get_db_connection():
    try:
        connection = connection_pool.getconn()
        if connection:
            return connection
    except (Exception, psycopg2.DatabaseError) as error:
        print('Error ao obter conexão do pool: ', error)
        return None


def release_db_connection(connection):
    try:
        connection_pool.putconn(connection)
    except (Exception, psycopg2.DatabaseError) as error:
        print('Erro ao devolver a conexão ao pool: ', error)


def find_one_user_by_code(code: str) -> bool:
    connection = get_db_connection()
    if connection:
        try:

            with connection.cursor() as cursor:
                find_one_query = ('SELECT * FROM customers WHERE id = %s')

                cursor.execute(find_one_query, (code,))
                record = cursor.fetchone()
                if record:
                    return True
                else:
                    return False
        except (Exception, psycopg2.Error) as error:
            print('Erro ao encontrar usuário pelo id: ', error)
            connection.rollback()
        finally:
            release_db_connection(connection)


def find_one_measure_by_date_and_type_and_id(user_code: str, measure_type: str, date: datetime) -> bool:
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                find_one_query = '''SELECT * FROM measures WHERE EXTRACT(MONTH FROM date) = %s 
                AND EXTRACT(YEAR FROM date) = %s AND type = %s AND id_customer = %s;'''
                cursor.execute(find_one_query, (date.month, date.year, measure_type, user_code))

                record = cursor.fetchone()
                if record:
                    return False
                else:
                    return True
        except (Exception, psycopg2.Error) as error:
            print('Erro ao encontrar measure: ', error)
            connection.rollback()
        finally:
            release_db_connection(connection)


def find_one_measure_by_uuid(measure_uuid: str) -> bool:
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                find_one_query = '''SELECT * FROM measures WHERE uuid = %s'''
                cursor.execute(find_one_query, (measure_uuid,))

                record = cursor.fetchone()
                if record:
                    return True
                else:
                    return False
        except (Exception, psycopg2.Error) as error:
            print('Erro ao encontrar measure pelo uuid: ', error)
            connection.rollback()
        finally:
            release_db_connection(connection)


def find_all_measures_by_user_code(user_code: str, measure_type: str | None) -> dict:
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                find_all_query = "SELECT * FROM measures WHERE id_customer = %s"
                if measure_type is not None:
                    find_all_query = find_all_query + " AND type = %s"
                    cursor.execute(find_all_query, (user_code, measure_type))
                else:
                    cursor.execute(find_all_query, user_code)

                records = cursor.fetchall()

                measures: dict = {"customer_code": user_code, "measures": []}
                for row in records:
                    binary_data = bytes(row[3])  # ->  # Converter o memoryview para bytes

                    base64_encoded_data = base64.b64encode(binary_data)  # ->  # Encode para Base64

                    string_image = base64_encoded_data.decode('utf-8')   # -> Converter para string

                    measures["measures"].append(
                        {'uuid': row[1], 'value': row[2], 'image': string_image,
                         'measure_datetime': row[4].strftime('%Y-%m-%d %H:%M:%S'),
                         'measure_type': row[5], 'customer_code': row[6]})
                return measures
        except (Exception, psycopg2.Error) as error:
            print('Erro ao encontrar registros: ', error)
            connection.rollback()
        finally:
            release_db_connection(connection)


def insert_one_measure(measure_infos: dict) -> str:
    new_uuid = generate_uuid()
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                insert_one_query = "INSERT INTO measures (uuid, value, imagebase64, date, type, confirmed, id_customer) VALUES (%s, %s, %s, %s, %s, %s, %s);"
                cursor.execute(insert_one_query, (new_uuid, float(measure_infos['value']), measure_infos['image'],
                                                  measure_infos['measure_datetime'], measure_infos['measure_type'],
                                                  measure_infos['confirmed'], measure_infos['customer_code']))
                connection.commit()
                return new_uuid
        except (Exception, psycopg2.Error) as error:
            print('Erro ao inserir um registro: ', error)
            connection.rollback()
        finally:
            release_db_connection(connection)


def check_confirm_measure(measure_uuid: str) -> bool:
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                find_one_query = '''SELECT confirmed FROM measures WHERE uuid = %s'''
                cursor.execute(find_one_query, (measure_uuid,))

                record = cursor.fetchone()
                if int(record[0]) == 1:
                    return True
                else:
                    return False
        except (Exception, psycopg2.Error) as error:
            print('Erro1 ao encontrar usuário: ', error)
            connection.rollback()
        finally:
            release_db_connection(connection)


def confirm_measure(measure_uuid: str, new_value: int) -> bool | None:
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                find_one_query = '''UPDATE measures SET confirmed = 1, value = %s WHERE uuid = %s;'''
                cursor.execute(find_one_query, (new_value, measure_uuid))

                connection.commit()
                return True
        except (Exception, psycopg2.Error) as error:
            print('Erro2 ao encontrar usuário: ', error)
            connection.rollback()
            return None
        finally:
            release_db_connection(connection)
