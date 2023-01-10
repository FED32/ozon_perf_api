# syntax=docker/dockerfile:1
FROM python:3

WORKDIR ./app
COPY . ./
RUN chmod 775 script.sh

RUN pip install --upgrade pip && pip install --no-cache-dir --upgrade -r requirements.txt

CMD gunicorn -b 0.0.0.0:5000 --timeout 9999 --workers 8 main:app --reload

# RUN apt update
# RUN apt install -y wget
# RUN mkdir -p ~/.postgresql && \
#     wget "https://storage.yandexcloud.net/cloud-certs/CA.pem" -O ~/.postgresql/root.crt && \
#     chmod 0600 ~/.postgresql/root.crt
