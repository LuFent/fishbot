import requests
from datetime import datetime, timedelta
import os
from pathlib import Path


def get_products(api_key):
    url = "https://api.moltin.com/v2/products"
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["data"]


def get_product(api_key, product_id):
    url = f"https://api.moltin.com/v2/products/{product_id}"

    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_cart_products(api_key, cart_id):
    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    url = f"https://api.moltin.com/v2/carts/{cart_id}/items"

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def put_in_cart(api_key, cart_id, product_id, quantity=1):
    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    url = f"https://api.moltin.com/v2/carts/{cart_id}/items"

    json_data = {
        "data": {
            "id": product_id,
            "type": "cart_item",
            "quantity": quantity,
        },
    }

    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    return response.json()


def get_image(api_key, product):
    file_name = f'{product["name"]}.png'
    Path("Images").mkdir(exist_ok=True)
    if file_name in os.listdir("Images"):
        return os.path.join("Images", file_name)

    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    image_url = f'https://api.moltin.com/v2/files/{product["relationships"]["main_image"]["data"]["id"]}'
    image_url = requests.get(image_url, headers=headers)
    image_url.raise_for_status()
    image_url = image_url.json()["data"]["link"]["href"]
    image = requests.get(image_url)
    image.raise_for_status()
    image = image.content
    with open(os.path.join("Images", file_name), "wb") as image_file:
        image_file.write(image)
        return os.path.join("Images", file_name)


def remove_cart_item(api_key, cart_id, cart_item_id):
    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    response = requests.delete(
        f"https://api.moltin.com/v2/carts/{cart_id}/items/{cart_item_id}",
        headers=headers,
    )
    response.raise_for_status()


def clear_cart(api_key, cart_id):
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    url = f"https://api.moltin.com/v2/carts/{cart_id}/items"

    response = requests.delete(url, headers=headers)
    response.raise_for_status()


def create_customer(api_key, tg_name, email):
    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    json_data = {
        "data": {
            "type": "customer",
            "name": tg_name,
            "email": email,
        },
    }

    response = requests.post(
        "https://api.moltin.com/v2/customers", headers=headers, json=json_data
    )
    response.raise_for_status()
    return response.json()["data"]["id"]


def cart_checkout(api_key, cart_id, customer_id, first_name, last_name):
    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    json_data = {
        "data": {
            "customer": {
                "id": customer_id,
            },
            "billing_address": {
                "first_name": first_name,
                "last_name": last_name,
                "company_name": ".",
                "line_1": ".",
                "region": ".",
                "postcode": ".",
                "country": ".",
            },
            "shipping_address": {
                "first_name": first_name,
                "last_name": last_name,
                "line_1": ".",
                "region": ".",
                "postcode": ".",
                "country": ".",
            },
        },
    }

    url = f"https://api.moltin.com/v2/carts/{cart_id}/checkout"
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()


def set_token(redis_db):
    moltin_client_id = redis_db.get('MOLTIN_CLIENT_ID')
    data = {
        "client_id": moltin_client_id,
        "grant_type": "implicit",
    }

    response = requests.post(
        "https://api.moltin.com/oauth/access_token", data=data
    )
    response.raise_for_status()
    token = response.json()
    expire_time = datetime.now() + timedelta(seconds=token['expires_in'] - 10)
    expire_time = format(expire_time, '%d/%m/%y %H:%M:%S')
    redis_db.set("MOLTIN_API_TOKEN", token["access_token"])
    redis_db.set("MOLTIN_API_TOKEN_EXPIRE_TIME", expire_time)
    return token["access_token"]

def get_or_update_token(redis_db):
    expire_time = redis_db.get("MOLTIN_API_TOKEN_EXPIRE_TIME").decode("utf-8")
    expire_time = datetime.strptime(expire_time, '%d/%m/%y %H:%M:%S')

    if expire_time <= datetime.now():
        return set_token(redis_db)
    else:
        return redis_db.get("MOLTIN_API_TOKEN").decode("utf-8")



