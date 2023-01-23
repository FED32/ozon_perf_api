import pandas as pd
import numpy as np
import os
import psycopg2
from sqlalchemy import create_engine
import logger_api
from datetime import datetime
import time
import json
from flask import Flask, jsonify


logger = logger_api.init_logger()

# читаем параметры подключения
host = os.environ.get('ECOMRU_PG_HOST', None)
port = os.environ.get('ECOMRU_PG_PORT', None)
ssl_mode = os.environ.get('ECOMRU_PG_SSL_MODE', None)
db_name = os.environ.get('ECOMRU_PG_DB_NAME', None)
user = os.environ.get('ECOMRU_PG_USER', None)
password = os.environ.get('ECOMRU_PG_PASSWORD', None)
target_session_attrs = 'read-write'

# host = 'localhost'
# port = '5432'
# db_name = 'postgres'
# user = 'postgres'
# password = ' '

db_params = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def put_query(json_file,
              table_name: str,
              attempts: int = 3,
              result=None
              ):
    """Загружает запрос в БД"""

    try:
        # if result.status_code == 200:
        res_id = result.json().get("campaignId", None)
        if res_id is not None:
            json_file.setdefault("res_id", res_id)

        res_error = result.json().get("error", None)
        if res_error is not None:
            json_file.setdefault("res_error", res_error)
        # elif result.status_code == 400:
        #     json_file.setdefault("res_error", result.text)
        # else:
        #     json_file.setdefault("res_error", result.text)
    except:
        json_file.setdefault("res_error", result.text)

    dataset = pd.DataFrame([json_file])
    dataset['date_time'] = datetime.now()

    engine = create_engine(db_params)

    n = 0
    while n < attempts:
        try:
            res = dataset.to_sql(name=table_name, con=engine, if_exists='append', index=False)
            logger.info(f"Upload to {table_name} - ok")
            return 'ok'
        except BaseException as ex:
            logger.error(f"data to db: {ex}")
            time.sleep(5)
            n += 1
    logger.error("data to db error")
    return None


