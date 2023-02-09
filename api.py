from flask import Flask, jsonify, request
from flask import Response
from werkzeug.exceptions import BadRequestKeyError
from ozon_performance import OzonPerformance
from flasgger import Swagger, swag_from
from config import Configuration
from get_secret_from_db import get_secret_from_db
import logger_api
from db_work import put_query, get_clients, get_objects_from_db
from sqlalchemy import create_engine
import os


logger = logger_api.init_logger()

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
engine = create_engine(db_params)


app = Flask(__name__)
app.config.from_object(Configuration)
app.config['SWAGGER'] = {"title": "Swagger-UI", "uiversion": 3}


swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec_1",
            "route": "/apispec_1.json()",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/swagger/",
}

swagger = Swagger(app, config=swagger_config)


class HttpError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message


@app.route('/ozonperformance/campaigns', methods=['POST'])
@swag_from("swagger_conf/get_campaigns.yml")
def get_campaigns():
    """Метод для вывода списка кампаний"""

    try:
        json_file = request.get_json(force=False)
        client_id = json_file["client_id"]
        # client_secret = json_file["client_secret"]
        client_secret = get_secret_from_db(client_id=client_id, engine=engine, logger=logger)

        ozon = OzonPerformance(client_id, client_secret)

        if ozon.auth is None:
            logger.error("get campaigns: Client authorization failed")
            return jsonify({'error': 'Ошибка авторизации'})
        else:
            return jsonify({'result': ozon.get_campaigns()})

    except BadRequestKeyError:
        logger.error("get campaigns: BadRequest")
        return Response(None, 400)

    except KeyError:
        logger.error("get campaigns: KeyError")
        return Response(None, 400)

    except BaseException as ex:
        logger.error(f'get campaigns: {ex}')
        raise HttpError(400, f'{ex}')


@app.route('/ozonperformance/objects', methods=['POST'])
@swag_from("swagger_conf/get_objects.yml")
def get_objects():
    """Метод для вывода списка рекламируемых объектов """

    try:
        json_file = request.get_json(force=False)
        client_id = json_file["client_id"]
        # client_secret = json_file["client_secret"]
        client_secret = get_secret_from_db(client_id=client_id, engine=engine, logger=logger)

        campaign_id = json_file["campaign_id"]

        ozon = OzonPerformance(client_id, client_secret)

        if ozon.auth is None:
            logger.error("get objects: Client authorization failed")
            return jsonify({'error': 'Ошибка авторизации'})
        else:
            return jsonify({'result': ozon.get_objects(campaign_id)})

    except BadRequestKeyError:
        logger.error("get objects: BadRequest")
        return Response(None, 400)

    except KeyError:
        logger.error("get objects: KeyError")
        return Response(None, 400)

    except BaseException as ex:
        logger.error(f'get objects: {ex}')
        raise HttpError(400, f'{ex}')


@app.route('/ozonperformance/available', methods=['POST'])
@swag_from("swagger_conf/available.yml")
def available():
    """Получить список доступных режимов создания кампаний"""

    try:
        json_file = request.get_json(force=False)
        client_id = json_file["client_id"]
        # client_secret = json_file["client_secret"]
        client_secret = get_secret_from_db(client_id=client_id, engine=engine, logger=logger)

        ozon = OzonPerformance(client_id, client_secret)

        if ozon.auth is None:
            logger.error("get available: Client authorization failed")
            return jsonify({'error': 'Ошибка авторизации'})
        else:
            res = ozon.get_camp_modes()
            try:
                if res.status_code == 200:
                    logger.info(f"get available: OK")
                    return jsonify({'result': res.json()})
                else:
                    logger.error(f"get available: error OZON {res.status_code}")
                    return jsonify({'error': res.text, 'status_code': res.status_code})
            except:
                logger.error(f"get available: unknown error Ozon server")
                return jsonify({'error': 'Не известная ошибка при обращении к серверу OZON'})

    except BadRequestKeyError:
        logger.error("get available: BadRequest")
        return Response(None, 400)

    except KeyError:
        logger.error("get available: KeyError")
        return Response(None, 400)

    except BaseException as ex:
        logger.error(f'get available: {ex}')
        raise HttpError(400, f'{ex}')


@app.route('/ozonperformance/addcampcpm', methods=['POST'])
@swag_from("swagger_conf/add_campaign_cpm.yml")
def add_campaign_cpm():
    """Создать кампанию с оплатой за показы"""

    try:
        json_file = request.get_json(force=False)
        client_id = json_file["client_id"]
        # client_secret = json_file["client_secret"]
        client_secret = get_secret_from_db(client_id=client_id, engine=engine, logger=logger)

        ozon = OzonPerformance(client_id, client_secret)

        if ozon.auth is None:
            logger.error("add campaign cpm: Client authorization failed")
            return jsonify({'error': 'Ошибка авторизации'})
        else:
            title = json_file.get("title", None)
            from_date = json_file.get("from_date", None)
            to_date = json_file.get("to_date", None)
            budget = json_file.get("budget", "0")
            daily_budget = json_file.get("daily_budget", None)
            exp_strategy = json_file.get("exp_strategy", None)
            placement = json_file["placement"]
            product_autopilot_strategy = json_file.get("product_autopilot_strategy", None)
            autopilot_category_id = json_file.get("autopilot_category_id", None)
            autopilot_sku_add_mode = json_file.get("autopilot_sku_add_mode", None)
            pcm = json_file.get("pcm", None)

            res = ozon.create_camp_cpm(title, from_date, to_date, daily_budget, budget, exp_strategy, placement,
                                       product_autopilot_strategy, autopilot_category_id, autopilot_sku_add_mode, pcm)

            put_query(json_file=json_file, table_name='ozon_perf_addcampaigns', result=res, engine=engine,
                      logger=logger)

            try:
                if res.status_code == 200:
                    logger.info(f"add campaign cpm: OK")
                    return jsonify({'result': res.json(), 'message': 'Кампания создана'})
                else:
                    logger.error(f"add campaign cpm: error OZON {res.status_code}")
                    return jsonify({'error': res.text, 'message': 'Ошибка запроса', 'status_code': res.status_code})
            except:
                logger.error(f"add campaign cpm: unknown error Ozon server")
                return jsonify({'error': 'Не известная ошибка при обращении к серверу OZON'})

    except BadRequestKeyError:
        logger.error("add campaign cpm: BadRequest")
        return Response(None, 400)

    except KeyError:
        logger.error("add campaign cpm: KeyError")
        return Response(None, 400)

    except BaseException as ex:
        logger.error(f'add campaign cpm: {ex}')
        raise HttpError(400, f'{ex}')


@app.route('/ozonperformance/addcampcpc', methods=['POST'])
@swag_from("swagger_conf/add_campaign_cpc.yml")
def add_campaign_cpc():
    """Создать кампанию с оплатой за клики"""

    try:
        json_file = request.get_json(force=False)
        client_id = json_file["client_id"]
        # client_secret = json_file["client_secret"]
        client_secret = get_secret_from_db(client_id=client_id, engine=engine, logger=logger)

        ozon = OzonPerformance(client_id, client_secret)

        if ozon.auth is None:
            logger.error("add campaign cpc: Client authorization failed")
            return jsonify({'error': 'Ошибка авторизации'})
        else:
            title = json_file.get("title", None)
            from_date = json_file.get("from_date", None)
            to_date = json_file.get("to_date", None)
            daily_budget = json_file.get("daily_budget", None)
            exp_strategy = json_file.get("exp_strategy", None)
            placement = json_file["placement"]
            product_autopilot_strategy = json_file.get("product_autopilot_strategy", None)
            pcm = json_file.get("pcm", None)

            res = ozon.create_camp_cpc(title, from_date, to_date, daily_budget, exp_strategy, placement,
                                       product_autopilot_strategy, pcm)

            put_query(json_file=json_file, table_name='ozon_perf_addcampaigns', result=res, engine=engine,
                      logger=logger)

            try:
                if res.status_code == 200:
                    logger.info(f"add campaign cpc: OK")
                    return jsonify({'result': res.json(), 'message': 'Кампания создана'})
                else:
                    logger.error(f"add campaign cpc: error OZON {res.status_code}")
                    return jsonify({'error': res.text, 'message': 'Ошибка запроса', 'status_code': res.status_code})
            except:
                logger.error(f"add campaign cpc: unknown error Ozon server")
                return jsonify({'error': 'Не известная ошибка при обращении к серверу OZON'})

    except BadRequestKeyError:
        logger.error("add campaign cpc: BadRequest")
        return Response(None, 400)

    except KeyError:
        logger.error("add campaign cpc: KeyError")
        return Response(None, 400)

    except BaseException as ex:
        logger.error(f'add campaign cpc: {ex}')
        raise HttpError(400, f'{ex}')


@app.route('/ozonperformance/activate', methods=['POST'])
@swag_from("swagger_conf/activate.yml")
def activate_camp():
    """Активировать кампанию"""

    try:
        json_file = request.get_json(force=False)
        client_id = json_file["client_id"]
        # client_secret = json_file["client_secret"]
        client_secret = get_secret_from_db(client_id=client_id, engine=engine, logger=logger)

        campaign_id = json_file["campaign_id"]

        ozon = OzonPerformance(client_id, client_secret)

        if ozon.auth is None:
            logger.error("activate campaign: Client authorization failed")
            return jsonify({'error': 'Ошибка авторизации'})
        else:
            res = ozon.camp_activate(campaign_id)
            try:
                if res.status_code == 200:
                    logger.info(f"activate campaign: OK")
                    return jsonify({'result': res.json(), 'message': 'Кампания активирована'})
                else:
                    logger.error(f"activate campaign: error OZON {res.status_code}")
                    return jsonify({'error': res.text, 'message': 'Ошибка запроса', 'status_code': res.status_code})
            except:
                logger.error(f"activate campaign: unknown error Ozon server")
                return jsonify({'error': 'Не известная ошибка при обращении к серверу OZON'})

    except BadRequestKeyError:
        logger.error("activate campaign: BadRequest")
        return Response(None, 400)

    except KeyError:
        logger.error("activate campaign: KeyError")
        return Response(None, 400)

    except BaseException as ex:
        logger.error(f'activate campaign: {ex}')
        raise HttpError(400, f'{ex}')


@app.route('/ozonperformance/deactivate', methods=['POST'])
@swag_from("swagger_conf/deactivate.yml")
def deactivate_camp():
    """Деактивировать кампанию"""

    try:
        json_file = request.get_json(force=False)
        client_id = json_file["client_id"]
        # client_secret = json_file["client_secret"]
        client_secret = get_secret_from_db(client_id=client_id, engine=engine, logger=logger)

        ozon = OzonPerformance(client_id, client_secret)

        if ozon.auth is None:
            logger.error("deactivate campaign: Client authorization failed")
            return jsonify({'error': 'Ошибка авторизации'})
        else:
            campaign_id = json_file["campaign_id"]

            res = ozon.camp_deactivate(campaign_id)
            try:
                if res.status_code == 200:
                    logger.info(f"deactivate campaign: OK")
                    return jsonify({'result': res.json(), 'message': 'Кампания деактивирована'})
                else:
                    logger.error(f"deactivate campaign: error OZON {res.status_code}")
                    return jsonify({'error': res.text, 'message': 'Ошибка запроса', 'status_code': res.status_code})
            except:
                logger.error(f"deactivate campaign: unknown error Ozon server")
                return jsonify({'error': 'Не известная ошибка при обращении к серверу OZON'})

    except BadRequestKeyError:
        logger.error("deactivate campaign: BadRequest")
        return Response(None, 400)

    except KeyError:
        logger.error("deactivate campaign: KeyError")
        return Response(None, 400)

    except BaseException as ex:
        logger.error(f'deactivate campaign: {ex}')
        raise HttpError(400, f'{ex}')


@app.route('/ozonperformance/period', methods=['POST'])
@swag_from("swagger_conf/period.yml")
def campaign_period():
    """Изменить сроки проведения кампании"""

    try:
        json_file = request.get_json(force=False)
        client_id = json_file["client_id"]
        # client_secret = json_file["client_secret"]
        client_secret = get_secret_from_db(client_id=client_id, engine=engine, logger=logger)

        ozon = OzonPerformance(client_id, client_secret)

        if ozon.auth is None:
            logger.error("period campaign: Client authorization failed")
            return jsonify({'error': 'Ошибка авторизации'})
        else:
            campaign_id = json_file["campaign_id"]
            date_from = json_file.get("date_from", None)
            date_to = json_file.get("date_to", None)

            res = ozon.camp_period(campaign_id, date_from, date_to)

            try:
                if res.status_code == 200:
                    logger.info(f"period campaign: OK")
                    return jsonify({'result': res.json(), 'message': 'Сроки изменены'})
                else:
                    logger.error(f"period campaign: error OZON {res.status_code}")
                    return jsonify({'error': res.text, 'message': 'Ошибка запроса', 'status_code': res.status_code})
            except:
                logger.error(f"period campaign: unknown error Ozon server")
                return jsonify({'error': 'Не известная ошибка при обращении к серверу OZON'})

    except BadRequestKeyError:
        logger.error("period campaign: BadRequest")
        return Response(None, 400)

    except KeyError:
        logger.error("period campaign: KeyError")
        return Response(None, 400)

    except BaseException as ex:
        logger.error(f'period campaign: {ex}')
        raise HttpError(400, f'{ex}')


@app.route('/ozonperformance/budget', methods=['POST'])
@swag_from("swagger_conf/budget.yml")
def campaign_budget():
    """Изменить ограничения дневного бюджета кампании"""

    try:
        json_file = request.get_json(force=False)
        client_id = json_file["client_id"]
        # client_secret = json_file["client_secret"]
        client_secret = get_secret_from_db(client_id=client_id, engine=engine, logger=logger)

        ozon = OzonPerformance(client_id, client_secret)

        if ozon.auth is None:
            logger.error("budget campaign: Client authorization failed")
            return jsonify({'error': 'Ошибка авторизации'})
        else:
            campaign_id = json_file["campaign_id"]
            daily_budget = json_file["daily_budget"]
            exp_str = json_file.get("exp_str", None)

            res = ozon.camp_budget(campaign_id, daily_budget, exp_str)
            try:
                if res.status_code == 200:
                    logger.info(f"budget campaign: OK")
                    return jsonify({'result': res.json(), 'message': 'Дневной бюджет изменен'})
                else:
                    logger.error(f"budget campaign: error OZON {res.status_code}")
                    return jsonify({'error': res.text, 'message': 'Ошибка запроса', 'status_code': res.status_code})
            except:
                logger.error(f"budget campaign: unknown error Ozon server")
                return jsonify({'error': 'Не известная ошибка при обращении к серверу OZON'})

    except BadRequestKeyError:
        logger.error("budget campaign: BadRequest")
        return Response(None, 400)

    except KeyError:
        logger.error("budget campaign: KeyError")
        return Response(None, 400)

    except BaseException as ex:
        logger.error(f'budget campaign: {ex}')
        raise HttpError(400, f'{ex}')


@app.route('/ozonperformance/addgroup', methods=['POST'])
@swag_from("swagger_conf/add_group.yml")
def add_group():
    """Создать группу"""

    try:
        json_file = request.get_json(force=False)
        client_id = json_file["client_id"]
        # client_secret = json_file["client_secret"]
        client_secret = get_secret_from_db(client_id=client_id, engine=engine, logger=logger)

        ozon = OzonPerformance(client_id, client_secret)

        if ozon.auth is None:
            logger.error("add group: Client authorization failed")
            return jsonify({'error': 'Ошибка авторизации'})
        else:
            campaign_id = json_file["campaign_id"]
            title = json_file.get("title", None)
            stopwords = json_file.get("stopwords", None)
            phrases = json_file.get("phrases", None)
            bids_list = json_file.get("bids_list", None)
            relevance_status = json_file.get("relevance_status", None)

            res = ozon.add_group(campaign_id, title, stopwords, phrases, bids_list, relevance_status)

            put_query(json_file=json_file, table_name='ozon_perf_addgroups', result=res, engine=engine, logger=logger)

            try:
                if res.status_code == 200:
                    logger.info(f"add group: OK")
                    return jsonify({'result': res.json(), 'message': 'Группа создана'})
                else:
                    logger.error(f"add group: error OZON {res.status_code}")
                    return jsonify({'error': res.text, 'message': 'Ошибка запроса', 'status_code': res.status_code})
            except:
                logger.error(f"add group: unknown error Ozon server")
                return jsonify({'error': 'Не известная ошибка при обращении к серверу OZON'})

    except BadRequestKeyError:
        logger.error("add group: BadRequest")
        return Response(None, 400)

    except KeyError:
        logger.error("add group: KeyError")
        return Response(None, 400)

    except BaseException as ex:
        logger.error(f'add group: {ex}')
        raise HttpError(400, f'{ex}')


@app.route('/ozonperformance/editgroup', methods=['POST'])
@swag_from("swagger_conf/edit_group.yml")
def edit_group():
    """Редактировать группу"""

    try:
        json_file = request.get_json(force=False)
        client_id = json_file["client_id"]
        # client_secret = json_file["client_secret"]
        client_secret = get_secret_from_db(client_id=client_id, engine=engine, logger=logger)

        ozon = OzonPerformance(client_id, client_secret)

        if ozon.auth is None:
            logger.error("edit group: Client authorization failed")
            return jsonify({'error': 'Ошибка авторизации'})
        else:
            campaign_id = json_file["campaign_id"]
            group_id = json_file["group_id"]
            title = json_file.get("title", None)
            stopwords = json_file.get("stopwords", None)
            phrases = json_file.get("phrases", None)
            bids_list = json_file.get("bids_list", None)
            relevance_status = json_file.get("relevance_status", None)

            res = ozon.edit_group(campaign_id, group_id, title, stopwords, phrases, bids_list, relevance_status)
            try:
                if res.status_code == 200:
                    logger.info(f"edit group: OK")
                    return jsonify({'result': res.json(), 'message': 'Группа изменена'})
                else:
                    logger.error(f"edit group: error OZON {res.status_code}")
                    return jsonify({'error': res.text, 'message': 'Ошибка запроса', 'status_code': res.status_code})
            except:
                logger.error(f"edit group: unknown error Ozon server")
                return jsonify({'error': 'Не известная ошибка при обращении к серверу OZON'})

    except BadRequestKeyError:
        logger.error("edit group: BadRequest")
        return Response(None, 400)

    except KeyError:
        logger.error("edit group: KeyError")
        return Response(None, 400)

    except BaseException as ex:
        logger.error(f'edit group: {ex}')
        raise HttpError(400, f'{ex}')


@app.route('/ozonperformance/addcardproducts', methods=['POST'])
@swag_from("swagger_conf/add_card_products.yml")
def addcardproducts():
    """Добавить товары в кампанию с размещением в карточке товара"""

    try:
        json_file = request.get_json(force=False)
        client_id = json_file["client_id"]
        # client_secret = json_file["client_secret"]
        client_secret = get_secret_from_db(client_id=client_id, engine=engine, logger=logger)

        ozon = OzonPerformance(client_id, client_secret)

        if ozon.auth is None:
            logger.error("add card products: Client authorization failed")
            return jsonify({'error': 'Ошибка авторизации'})
        else:
            sku_list = json_file.get("sku_list", None)
            bids_list = json_file.get("bids_list", None)

            bids = ozon.card_bids(sku_list, bids_list)
            if bids is not None:
                campaign_id = json_file["campaign_id"]

                res = ozon.add_products(campaign_id=campaign_id, bids=bids)

                put_query(json_file=json_file, table_name='ozon_perf_addproducts', result=res, engine=engine,
                          logger=logger)

                try:
                    if res.status_code == 200:
                        logger.info(f"add card products: OK")
                        return jsonify({'result': res.json(), 'message': 'Добавлено'})
                    else:
                        logger.error(f"add card products: error OZON {res.status_code}")
                        return jsonify({'error': res.text, 'message': 'Ошибка при обращении к серверу OZON',
                                        'status_code': res.status_code})
                except:
                    logger.error(f"add card products: unknown error Ozon server")
                    return jsonify({'error': 'Не известная ошибка при обращении к серверу OZON'})
            else:
                logger.info(f"add card products: incorrect data")
                return jsonify({'error': 'Не правильный формат данных'})

    except BadRequestKeyError:
        logger.error("add card products: BadRequest")
        return Response(None, 400)

    except KeyError:
        logger.error("add card products: KeyError")
        return Response(None, 400)

    except BaseException as ex:
        logger.error(f'add card products: {ex}')
        raise HttpError(400, f'{ex}')


@app.route('/ozonperformance/addgroupproducts', methods=['POST'])
@swag_from("swagger_conf/add_group_products.yml")
def addgroupproducts():
    """Добавление в кампанию товаров в ранее созданные группы с размещением на страницах каталога и поиска"""

    try:
        json_file = request.get_json(force=False)
        client_id = json_file["client_id"]
        # client_secret = json_file["client_secret"]
        client_secret = get_secret_from_db(client_id=client_id, engine=engine, logger=logger)

        ozon = OzonPerformance(client_id, client_secret)

        if ozon.auth is None:
            logger.error("add group products: Client authorization failed")
            return jsonify({'error': 'Ошибка авторизации'})
        else:
            sku_list = json_file.get("sku_list", None)
            bids_list = json_file.get("bids_list", None)
            groups_list = json_file.get("groups_list", None)

            bids = ozon.group_bids(sku_list, bids_list, groups_list)
            if bids is not None:
                campaign_id = json_file["campaign_id"]

                res = ozon.add_products(campaign_id=campaign_id, bids=bids)

                put_query(json_file=json_file, table_name='ozon_perf_addproducts', result=res, engine=engine,
                          logger=logger)

                try:
                    if res.status_code == 200:
                        logger.info(f"add group products: OK")
                        return jsonify({'result': res.json(), 'message': 'Добавлено'})
                    else:
                        logger.error(f"add group products: error OZON {res.status_code}")
                        return jsonify({'error': res.text, 'message': 'Ошибка при обращении к серверу OZON',
                                        'status_code': res.status_code})
                except:
                    logger.error(f"add group products: unknown error Ozon server")
                    return jsonify({'error': 'Не известная ошибка при обращении к серверу OZON'})
            else:
                logger.info(f"add group products: incorrect data")
                return jsonify({'error': 'Не правильный формат данных'})

    except BadRequestKeyError:
        logger.error("add group products: BadRequest")
        return Response(None, 400)

    except KeyError:
        logger.error("add group products: KeyError")
        return Response(None, 400)

    except BaseException as ex:
        logger.error(f'add group products: {ex}')
        raise HttpError(400, f'{ex}')


@app.route('/ozonperformance/addproduct', methods=['POST'])
@swag_from("swagger_conf/add_product.yml")
def addproduct():
    """Добавление товара на страницах каталога и поиска — добавление без группы"""

    try:
        json_file = request.get_json(force=False)
        client_id = json_file["client_id"]
        # client_secret = json_file["client_secret"]
        client_secret = get_secret_from_db(client_id=client_id, engine=engine, logger=logger)

        ozon = OzonPerformance(client_id, client_secret)

        if ozon.auth is None:
            logger.error("add product: Client authorization failed")
            return jsonify({'error': 'Ошибка авторизации'})
        else:
            sku = json_file["sku"]
            stopwords = json_file["stopwords"]
            phrases = json_file["phrases"]
            bids_list = json_file.get("bids_list", None)

            bids = ozon.phrases_bid(sku, stopwords, phrases, bids_list)
            if bids is not None:
                campaign_id = json_file["campaign_id"]

                res = ozon.add_products(campaign_id=campaign_id, bids=bids)

                put_query(json_file=json_file, table_name='ozon_perf_addproducts', result=res, engine=engine,
                          logger=logger)

                try:
                    if res.status_code == 200:
                        logger.info(f"add product: OK")
                        return jsonify({'result': res.json(), 'message': 'Добавлено'})
                    else:
                        logger.error(f"add product: error OZON {res.status_code}")
                        return jsonify({'error': res.text, 'message': 'Ошибка при обращении к серверу OZON',
                                        'status_code': res.status_code})
                except:
                    logger.error(f"add product: unknown error Ozon server")
                    return jsonify({'error': 'Не известная ошибка при обращении к серверу OZON'})
            else:
                logger.info(f"add product: incorrect data")
                return jsonify({'error': 'Не правильный формат данных'})

    except BadRequestKeyError:
        logger.error("add product: BadRequest")
        return Response(None, 400)

    except KeyError:
        logger.error("add product: KeyError")
        return Response(None, 400)

    except BaseException as ex:
        logger.error(f'add product: {ex}')
        raise HttpError(400, f'{ex}')


@app.route('/ozonperformance/updbidscardproducts', methods=['POST'])
@swag_from("swagger_conf/upd_bids_card_products.yml")
def updbidscardproducts():
    """Обновление ставок товаров с размещением в карточке товара"""

    try:
        json_file = request.get_json(force=False)
        client_id = json_file["client_id"]
        # client_secret = json_file["client_secret"]
        client_secret = get_secret_from_db(client_id=client_id, engine=engine, logger=logger)

        ozon = OzonPerformance(client_id, client_secret)

        if ozon.auth is None:
            logger.error("update bids card products: Client authorization failed")
            return jsonify({'error': 'Ошибка авторизации'})
        else:
            sku_list = json_file.get("sku_list", None)
            bids_list = json_file.get("bids_list", None)

            bids = ozon.card_bids(sku_list, bids_list)
            if bids is not None:
                campaign_id = json_file["campaign_id"]
                res = ozon.upd_bids(campaign_id=campaign_id, bids=bids)
                try:
                    if res.status_code == 200:
                        logger.info(f"update bids card products: OK")
                        return jsonify({'result': res.json(), 'message': 'Обновлено'})
                    else:
                        logger.error(f"update bids card products: error OZON {res.status_code}")
                        return jsonify({'error': res.text, 'message': 'Ошибка при обращении к серверу OZON',
                                        'status_code': res.status_code})
                except:
                    logger.error(f"update bids card products: unknown error Ozon server")
                    return jsonify({'error': 'Не известная ошибка при обращении к серверу OZON'})
            else:
                logger.info(f"update bids card products: incorrect data")
                return jsonify({'error': 'Не правильный формат данных'})

    except BadRequestKeyError:
        logger.error("update bids card products: BadRequest")
        return Response(None, 400)

    except KeyError:
        logger.error("update bids card products: KeyError")
        return Response(None, 400)

    except BaseException as ex:
        logger.error(f'update bids card products: {ex}')
        raise HttpError(400, f'{ex}')


@app.route('/ozonperformance/updbidsgroupproducts', methods=['POST'])
@swag_from("swagger_conf/upd_bids_group_products.yml")
def updbidsgroupproducts():
    """Обновление ставок товаров в группах с размещением на страницах каталога и поиска"""

    try:
        json_file = request.get_json(force=False)
        client_id = json_file["client_id"]
        # client_secret = json_file["client_secret"]
        client_secret = get_secret_from_db(client_id=client_id, engine=engine, logger=logger)

        ozon = OzonPerformance(client_id, client_secret)

        if ozon.auth is None:
            logger.error("update bids group products: Client authorization failed")
            return jsonify({'error': 'Ошибка авторизации'})
        else:
            sku_list = json_file.get("sku_list", None)
            bids_list = json_file.get("bids_list", None)
            groups_list = json_file.get("groups_list", None)

            bids = ozon.group_bids(sku_list, bids_list, groups_list)

            if bids is not None:
                campaign_id = json_file["campaign_id"]
                res = ozon.upd_bids(campaign_id=campaign_id, bids=bids)
                try:
                    if res.status_code == 200:
                        logger.info(f"update bids group products: OK")
                        return jsonify({'result': 'Обновлено'})
                    else:
                        logger.error(f"update bids group products: error OZON {res.status_code}")
                        return jsonify({'error': 'Ошибка при обращении к серверу OZON', 'status_code': res.status_code})
                except:
                    logger.error(f"update bids group products: unknown error Ozon server")
                    return jsonify({'error': 'Не известная ошибка при обращении к серверу OZON'})
            else:
                logger.info(f"update bids group products: incorrect data")
                return jsonify({'error': 'Не правильный формат данных'})

    except BadRequestKeyError:
        logger.error("update bids group products: BadRequest")
        return Response(None, 400)

    except KeyError:
        logger.error("update bids group products: KeyError")
        return Response(None, 400)

    except BaseException as ex:
        logger.error(f'update bids group products: {ex}')
        raise HttpError(400, f'{ex}')


@app.route('/ozonperformance/updbidsproduct', methods=['POST'])
@swag_from("swagger_conf/upd_bids_product.yml")
def updbidsproduct():
    """Обновление ставок товара на страницах каталога и поиска — без группы"""

    try:
        json_file = request.get_json(force=False)
        client_id = json_file["client_id"]
        # client_secret = json_file["client_secret"]
        client_secret = get_secret_from_db(client_id=client_id, engine=engine, logger=logger)

        ozon = OzonPerformance(client_id, client_secret)

        if ozon.auth is None:
            logger.error("update bids product: Client authorization failed")
            return jsonify({'error': 'Ошибка авторизации'})
        else:
            sku = json_file["sku"]
            stopwords = json_file["stopwords"]
            phrases = json_file["phrases"]
            bids_list = json_file.get("bids_list", None)

            bids = ozon.phrases_bid(sku, stopwords, phrases, bids_list)

            if bids is not None:
                campaign_id = json_file["campaign_id"]
                res = ozon.upd_bids(campaign_id=campaign_id, bids=bids)
                try:
                    if res.status_code == 200:
                        logger.info(f"update bids product: OK")
                        return jsonify({'result': res.json(), 'message': 'Обновлено'})
                    else:
                        logger.error(f"update bids product: error OZON {res.status_code}")
                        return jsonify({'error': res.text, 'message': 'Ошибка при обращении к серверу OZON',
                                        'status_code': res.status_code})
                except:
                    logger.error(f"update bids product: unknown error Ozon server")
                    return jsonify({'error': 'Не известная ошибка при обращении к серверу OZON'})
            else:
                logger.info(f"update bids product: incorrect data")
                return jsonify({'error': 'Не правильный формат данных'})

    except BadRequestKeyError:
        logger.error("update bids product: BadRequest")
        return Response(None, 400)

    except KeyError:
        logger.error("update bids product: KeyError")
        return Response(None, 400)

    except BaseException as ex:
        logger.error(f'update bids product: {ex}')
        raise HttpError(400, f'{ex}')


@app.route('/ozonperformance/prodlist', methods=['POST'])
@swag_from("swagger_conf/prod_list.yml")
def prodlist():
    """Cписок товаров кампании"""

    try:
        json_file = request.get_json(force=False)
        client_id = json_file["client_id"]
        # client_secret = json_file["client_secret"]
        client_secret = get_secret_from_db(client_id=client_id, engine=engine, logger=logger)

        ozon = OzonPerformance(client_id, client_secret)

        if ozon.auth is None:
            logger.error("products list: Client authorization failed")
            return jsonify({'error': 'Ошибка авторизации'})
        else:
            campaign_id = json_file["campaign_id"]
            res = ozon.prod_list(campaign_id)
            try:
                if res.status_code == 200:
                    logger.info(f"products list: OK")
                    return jsonify({'result': res.json()})
                else:
                    logger.error(f"products list: error OZON {res.status_code}")
                    return jsonify({'error': res.text, 'message': 'Ошибка запроса',
                                    'status_code': res.status_code})
            except:
                logger.error(f"products list: unknown error Ozon server")
                return jsonify({'error': 'Не известная ошибка при обращении к серверу OZON'})

    except BadRequestKeyError:
        logger.error("products list: BadRequest")
        return Response(None, 400)

    except KeyError:
        logger.error("products list: KeyError")
        return Response(None, 400)

    except BaseException as ex:
        logger.error(f'products list: {ex}')
        raise HttpError(400, f'{ex}')


@app.route('/ozonperformance/delproducts', methods=['POST'])
@swag_from("swagger_conf/del_products.yml")
def delproducts():
    """Удалить товары из кампании"""

    try:
        json_file = request.get_json(force=False)
        client_id = json_file["client_id"]
        # client_secret = json_file["client_secret"]
        client_secret = get_secret_from_db(client_id=client_id, engine=engine, logger=logger)

        ozon = OzonPerformance(client_id, client_secret)

        if ozon.auth is None:
            logger.error("delete products: Client authorization failed")
            return jsonify({'error': 'Ошибка авторизации'})
        else:
            campaign_id = json_file["campaign_id"]
            sku_list = json_file.get("sku_list", None)

            res = ozon.del_products(campaign_id=campaign_id, sku_list=sku_list)
            try:
                if res.status_code == 200:
                    logger.info(f"del products: {sku_list} - deleted")
                    return jsonify({'result': res.json(), 'message': 'Удалено'})
                else:
                    logger.error(f"del products: error OZON {res.status_code}")
                    return jsonify({'error': res.text, 'message': 'Ошибка при обращении к серверу OZON',
                                    'status_code': res.status_code})
            except:
                logger.error(f"delete products: unknown error Ozon server")
                return jsonify({'error': 'Не известная ошибка при обращении к серверу OZON'})

    except BadRequestKeyError:
        logger.error("delete products: BadRequest")
        return Response(None, 400)

    except KeyError:
        logger.error("delete products: KeyError")
        return Response(None, 400)

    except BaseException as ex:
        logger.error(f'delete products: {ex}')
        raise HttpError(400, f'{ex}')


@app.route('/ozonperformance/getclients', methods=['POST'])
@swag_from("swagger_conf/get_clients.yml")
def get_clients_():
    """Получить список доступных аккаунтов для клиента"""

    try:
        json_file = request.get_json(force=False)
        account_id = json_file["account_id"]

        res = get_clients(account_id, engine, logger)

        if res is None:
            raise HttpError(400, f'accounts database error')
        else:
            logger.info(f"get_clients: OK")
            return jsonify({'result': res})

    except BadRequestKeyError:
        logger.error("get_clients: BadRequest")
        return Response(None, 400)

    except KeyError:
        logger.error("get_clients: KeyError")
        return Response(None, 400)

    except BaseException as ex:
        logger.error(f'get_clients: {ex}')
        raise HttpError(400, f'{ex}')


@app.route('/ozonperformance/getcampaignsdb', methods=['POST'])
@swag_from("swagger_conf/get_campaigns_db.yml")
def get_campaigns_db():
    """Получить кампании из БД"""

    try:
        json_file = request.get_json(force=False)
        client_id = json_file["client_id"]

        res =  get_objects_from_db(client_id, table_name='ozon_perf_addcampaigns', engine=engine, logger=logger)

        if res is None:
            raise HttpError(400, f'accounts database error')

        else:
            logger.info(f"get_campaigns_db: OK")
            return jsonify({'result': res})

    except BadRequestKeyError:
        logger.error("get_campaigns_db: BadRequest")
        return Response(None, 400)

    except KeyError:
        logger.error("get_campaigns_db: KeyError")
        return Response(None, 400)

    except BaseException as ex:
        logger.error(f'get_campaigns_db: {ex}')
        raise HttpError(400, f'{ex}')






