import pandas as pd
import numpy as np
import os
import psycopg2
from datetime import datetime
import time
from sqlalchemy import exc
import json
from flask import Flask, jsonify


def sql_query(query, engine, logger, type_='dict'):

    with engine.connect() as connection:
        with connection.begin() as transaction:

            try:
                data = pd.read_sql(query, con=connection)

                if data is None:
                    logger.error("database error")
                    return None
                elif data.shape[0] == 0:
                    logger.info(f"no data")
                    if type_ == 'dict':
                        return []
                    elif type_ == 'df':
                        return data
                else:
                    if type_ == 'dict':
                        return data.to_dict(orient='records')
                    elif type_ == 'df':
                        return data

            except (exc.DBAPIError, exc.SQLAlchemyError):
                logger.error("db error")
                transaction.rollback()
                raise
            except BaseException as ex:
                logger.error(f"{ex}")
                transaction.rollback()
                raise
            finally:
                connection.close()


def put_query(json_file,
              engine,
              logger,
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

    with engine.begin() as connection:
        n = 0
        while n < attempts:
            try:
                res = dataset.to_sql(name=table_name, con=connection, if_exists='append', index=False)
                logger.info(f"Upload to {table_name} - ok")
                return 'ok'
            except BaseException as ex:
                logger.error(f"data to db: {ex}")
                time.sleep(5)
                n += 1
        logger.error("data to db error")
        return None


def get_clients(account_id: int, engine, logger):
    """Получает список доступных аккаунтов для клиента"""

    # query = f"""
    #          SELECT account_id as api_id, attribute_value as client_id
    #          FROM account_service_data asd WHERE attribute_id = 9 AND account_id = {account_id}
    #          """

    query = f"""
             SELECT 
             al.name AS name, 
             asd.account_id AS acc_id, 
             asd.attribute_value as ozon_perf_client_id 
             FROM account_list al 
             JOIN account_service_data asd ON al.id = asd.account_id 
             WHERE status_1 = 'Active' AND al.mp_id = 14 AND asd.attribute_id = 9 AND client_id = {account_id}
             """

    return sql_query(query, engine, logger, type_='dict')

    # with engine.begin() as connection:
    #     try:
    #         data = pd.read_sql(query, con=connection)
    #
    #         if data is None:
    #             logger.error("accounts database error")
    #             return None
    #         elif data.shape[0] == 0:
    #             logger.info("non-existent account")
    #             return []
    #         else:
    #             return data['client_id'].tolist()
    #
    #     except BaseException as ex:
    #         logger.error(f"get clients: {ex}")
    #         # print('Нет подключения к БД')
    #         return None


def get_objects_from_db(client_id: str, table_name: str, engine, logger):
    """Получает кампании клиента созданные через сервис"""

    if table_name == 'ozon_perf_addproducts':

        query = f"""
                 SELECT * 
                 FROM {table_name} 
                 WHERE res_error IS NULL AND client_id = '{client_id}'
                 """

    else:

        query = f"""
                 SELECT * 
                 FROM {table_name} 
                 WHERE res_id IS NOT NULL AND client_id = '{client_id}'
                 """

    return sql_query(query, engine, logger, type_='dict')

    # with engine.begin() as connection:
    #     try:
    #         data = pd.read_sql(query, con=connection)
    #
    #         if data is None:
    #             logger.error("accounts database error")
    #             return None
    #         elif data.shape[0] == 0:
    #             logger.info(f"no data for account {client_id}")
    #             return []
    #         else:
    #             return data.to_dict(orient='records')
    #
    #     except BaseException as ex:
    #         logger.error(f"get objects: {ex}")
    #         # print('Нет подключения к БД')
    #         return None




