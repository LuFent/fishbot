import requests
from dotenv import load_dotenv
import os
from time import sleep
import redis

load_dotenv()

MOLTIN_CLIENT_ID = os.environ.get("MOLTIN_CLIENT_ID")


REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)
REDIS_DB_NUM = os.environ.get("REDIS_DB_NUM", 0)

redis_db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_NUM)


data = {
    "client_id": MOLTIN_CLIENT_ID,
    "grant_type": "implicit",
}

token = requests.post("https://api.moltin.com/oauth/access_token", data=data).json()[
    "access_token"
]

redis_db.set("MOLTIN_API_TOKEN", token)
