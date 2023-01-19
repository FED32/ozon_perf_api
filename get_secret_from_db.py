import pandas as pd
import numpy as np
import os
import psycopg2
from sqlalchemy import create_engine
import logger_api


logger = logger_api.init_logger()


# читаем параметры подключения
host = os.environ.get('ECOMRU_PG_HOST', None)
port = os.environ.get('ECOMRU_PG_PORT', None)
ssl_mode = os.environ.get('ECOMRU_PG_SSL_MODE', None)
db_name = os.environ.get('ECOMRU_PG_DB_NAME', None)
user = os.environ.get('ECOMRU_PG_USER', None)
password = os.environ.get('ECOMRU_PG_PASSWORD', None)
target_session_attrs = 'read-write'

db_params = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def get_secret_from_db(client_id: str):
    """"Получает client_secret из БД по client_id"""

    query = f"""
            SELECT 
            al.id, 
            asd.attribute_value client_id, 
            asd2.attribute_value client_secret 
            FROM account_service_data asd 
            JOIN account_list al ON asd.account_id = al.id 
            JOIN (SELECT al.mp_id, asd.account_id, asd.attribute_id, asd.attribute_value 
            FROM account_service_data asd 
            JOIN account_list al ON asd.account_id = al.id 
            WHERE al.mp_id = 14) asd2 ON asd2.mp_id = al.mp_id AND asd2.account_id= asd.account_id AND asd2.attribute_id <> asd.attribute_id 
            WHERE al.mp_id = 14 AND asd.attribute_id = 9 AND al.status_1 = 'Active' and asd.attribute_value = '{client_id}' 
            GROUP BY asd.attribute_id, asd.attribute_value, asd2.attribute_id, asd2.attribute_value, al.id
            """

    try:
        engine = create_engine(db_params)

        data = pd.read_sql(query, con=engine)

        if data is None:
            logger.error("accounts database error")
            return ''
        elif data.shape[0] == 0:
            logger.error("non-existent account")
            return ''
        else:
            data = data.drop_duplicates(subset=['client_id', 'client_secret'], keep='first')
            return data['client_secret'][0]

    except:
        print('Нет подключения к БД')
        return ''


