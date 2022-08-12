import requests
import json
import os


def get_products(api_key):
    url = "https://api.moltin.com/v2/products"
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    response = requests.get(url, headers=headers).json()
    return response["data"]


def get_product(api_key, product_id):
    url = f"https://api.moltin.com/v2/products/{product_id}"

    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    response = requests.get(url, headers=headers).json()
    return response


def get_cart_products(api_key, cart_id):
    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    url = f"https://api.moltin.com/v2/carts/{cart_id}/items"

    response = requests.get(url, headers=headers).json()
    return response


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

    response = requests.post(url, headers=headers, json=json_data).json()
    return response


def get_image(api_key, product):
    file_name = f'{product["name"]}.png'
    if file_name in os.listdir("Images"):
        return os.path.join("Images", file_name)

    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    image_url = f'https://api.moltin.com/v2/files/{product["relationships"]["main_image"]["data"]["id"]}'
    image_url = requests.get(image_url, headers=headers).json()["data"]["link"]["href"]
    image = requests.get(image_url).content
    with open(os.path.join("Images", file_name), "wb") as image_file:
        image_file.write(image)
        return os.path.join("Images", file_name)


def remove_cart_item(api_key, cart_id, cart_item_id):
    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    requests.delete(
        f"https://api.moltin.com/v2/carts/{cart_id}/items/{cart_item_id}",
        headers=headers,
    )


def clear_cart(api_key, cart_id):
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    url = f"https://api.moltin.com/v2/carts/{cart_id}/items"

    requests.delete(url, headers=headers)


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
    ).json()
    return response["data"]["id"]


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
    response = requests.post(url, headers=headers, json=json_data).json()
