import pandas as pd
import numpy as np
from sqlalchemy import exc


def get_secret_from_db(client_id: str, engine, logger):
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
            WHERE al.mp_id = 14 AND asd.attribute_id = 9 AND asd.attribute_value = '{client_id}' 
            GROUP BY asd.attribute_id, asd.attribute_value, asd2.attribute_id, asd2.attribute_value, al.id
            """

    # with engine.begin() as connection:
    #     try:
    #         data = pd.read_sql(query, con=connection)
    #
    #         if data is None:
    #             logger.error("accounts database error")
    #             return ''
    #         elif data.shape[0] == 0:
    #             logger.info("non-existent account")
    #             return ''
    #         else:
    #             data = data.drop_duplicates(subset=['client_id', 'client_secret'], keep='first')
    #             return data['client_secret'][0]
    #
    #     except:
    #         print('Нет подключения к БД')
    #         return ''

    with engine.connect() as connection:
        with connection.begin() as transaction:
            try:
                data = pd.read_sql(query, con=connection)

                if data is None:
                    logger.error("accounts database error")
                    return ''
                elif data.shape[0] == 0:
                    logger.info("no data")
                    return ''
                else:
                    data = data.drop_duplicates(subset=['client_id', 'client_secret'], keep='first')
                    return data['client_secret'][0]

            except (exc.DBAPIError, exc.SQLAlchemyError):
                logger.error("db error")
                transaction.rollback()
                raise

            except BaseException as ex:
                logger.error(f"get tok: {ex}")
                transaction.rollback()
                raise

            finally:
                connection.close()


