import requests
from pprint import pprint
import json
from moltin_tools import *
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    Filters,
    Updater,
    ConversationHandler,
    CallbackQueryHandler,
)
import os
import telegram
from dotenv import load_dotenv
from functools import partial
import logging
from email_validator import validate_email, EmailNotValidError
import redis


logger = logging.getLogger(__name__)


def build_products_menu_keyboard(moltin_api_key):
    products_keyboard = [
        [
            telegram.InlineKeyboardButton(
                f"🐟 {product['name']}", callback_data=product["id"]
            )
        ]
        for product in get_products(moltin_api_key)
    ]
    products_keyboard.append(
        [telegram.InlineKeyboardButton("🧺 Корзина", callback_data="Корзина")]
    )
    products_keyboard = telegram.InlineKeyboardMarkup(products_keyboard)
    return products_keyboard


def build_product_keyboard(moltin_api_key, product_id):
    product_keyboard = [
        [
            telegram.InlineKeyboardButton(
                f"{5*k} kg", callback_data=f"{5*k}|{product_id}"
            )
            for k in range(1, 4)
        ],
        [telegram.InlineKeyboardButton("↩️Назад", callback_data="Назад")],
        [telegram.InlineKeyboardButton("🧺 Корзина", callback_data="Корзина")],
    ]

    product_keyboard = telegram.InlineKeyboardMarkup(product_keyboard)
    return product_keyboard


def start(bot, update, redis_db):

    moltin_api_key = redis_db.get("MOLTIN_API_TOKEN").decode("utf-8")

    products_keyboard = build_products_menu_keyboard(moltin_api_key)
    update.message.reply_text(
        text="Привет, я бот для продажи рыбы!\nВыберете продукт",
        reply_markup=products_keyboard,
    )
    return "MAIN_MENU"


def main_menu(bot, update, redis_db):
    moltin_api_key = redis_db.get("MOLTIN_API_TOKEN").decode("utf-8")
    query = update.callback_query
    user_id = query.from_user.id

    products_keyboard = build_products_menu_keyboard(moltin_api_key)
    message = "Привет, я бот для продажи рыбы!\nВыберете продукт"

    bot.send_message(user_id, text=message, reply_markup=products_keyboard)
    bot.delete_message(chat_id=user_id, message_id=query["message"].message_id)
    return "MAIN_MENU"


def product(bot, update, redis_db):
    moltin_api_key = redis_db.get("MOLTIN_API_TOKEN").decode("utf-8")
    query = update.callback_query
    product_id = query["data"]
    user_id = query.from_user.id

    product = get_product(moltin_api_key, product_id)["data"]
    cart = get_cart_products(moltin_api_key, user_id)
    for cart_product in cart["data"]:
        if cart_product["product_id"] == product_id:
            product_quantity = cart_product["quantity"]
            product_price = cart_product["value"]["amount"]
            break
    else:
        product_quantity, product_price = 0, 0
    message = f'🐟{product["name"]}\n\n💰{product["price"][0]["amount"]/100}$ per kg\n\n💵{product_quantity} kg' \
              f' in cart for {product_price/100} $ \n\n🤓{product["description"]}'
    image_file = get_image(moltin_api_key, product)
    product_keyboard = build_product_keyboard(moltin_api_key, product_id)

    bot.send_photo(
        user_id, open(image_file, "rb"), caption=message, reply_markup=product_keyboard
    )
    bot.delete_message(chat_id=user_id, message_id=query["message"].message_id)
    return "PRODUCT"


def cart(bot, update, redis_db):
    moltin_api_key = redis_db.get("MOLTIN_API_TOKEN").decode("utf-8")
    query = update.callback_query
    user_id = query.from_user.id
    cart = get_cart_products(moltin_api_key, user_id)
    cart_sum = 0
    cart_keyboard = []
    message = "🧺Ваша корзина:\n\n"
    for product in cart["data"]:
        message += f'🐟{product["name"]}\n{product["unit_price"]["amount"]/100}$ per kg\n{product["quantity"]} kg ' \
                   f'in cart for {product["value"]["amount"]/100}$\n\n'
        cart_sum += product["value"]["amount"]
        cart_keyboard.append(
            [
                telegram.InlineKeyboardButton(
                    f'❌ Убрать из корзины {product["name"]}',
                    callback_data=product["id"],
                )
            ]
        )

    cart_keyboard.append(
        [telegram.InlineKeyboardButton("В меню", callback_data="В меню")]
    )
    cart_keyboard.append(
        [telegram.InlineKeyboardButton("Оплата", callback_data="Оплата")]
    )
    message += f"Итого: {cart_sum/100}$"

    bot.send_message(
        text=message,
        chat_id=user_id,
        reply_markup=telegram.InlineKeyboardMarkup(cart_keyboard),
    )

    bot.delete_message(chat_id=user_id, message_id=query["message"].message_id)

    return "CART"


def add_to_cart(bot, update, redis_db):
    moltin_api_key = redis_db.get("MOLTIN_API_TOKEN").decode("utf-8")
    query = update.callback_query
    user_id = query.from_user.id

    quantity, product_id = query["data"].split("|")

    put_in_cart(moltin_api_key, user_id, product_id, int(quantity))

    products_keyboard = build_products_menu_keyboard(moltin_api_key)
    message = "🐟Привет, я бот для продажи рыбы!🐟\nВыберете продукт"

    bot.send_message(user_id, text=message, reply_markup=products_keyboard)
    bot.delete_message(chat_id=user_id, message_id=query["message"].message_id)
    return "MAIN_MENU"


def remove_from_cart(bot, update, redis_db):
    moltin_api_key = redis_db.get("MOLTIN_API_TOKEN").decode("utf-8")
    query = update.callback_query
    user_id = query.from_user.id
    cart_item_id = query["data"]

    remove_cart_item(moltin_api_key, cart_id=user_id, cart_item_id=cart_item_id)

    cart = get_cart_products(moltin_api_key, user_id)
    cart_sum = 0
    cart_keyboard = []
    message = "🧺Ваша корзина:\n\n"
    for product in cart["data"]:
        message += f'🐟{product["name"]}\n{product["unit_price"]["amount"] / 100}$ per kg\n{product["quantity"]} kg in ' \
                   f'cart for {product["value"]["amount"] / 100}$\n\n'
        cart_sum += product["value"]["amount"]
        cart_keyboard.append(
            [
                telegram.InlineKeyboardButton(
                    f'❌ Убрать из корзины {product["name"]}',
                    callback_data=product["id"],
                )
            ]
        )

    cart_keyboard.append(
        [telegram.InlineKeyboardButton("В меню", callback_data="В меню")]
    )
    cart_keyboard.append(
        [telegram.InlineKeyboardButton("Оплата", callback_data="Оплата")]
    )
    message += f"Итого: {cart_sum / 100}$"

    bot.send_message(
        text=message,
        chat_id=user_id,
        reply_markup=telegram.InlineKeyboardMarkup(cart_keyboard),
    )
    bot.delete_message(chat_id=user_id, message_id=query["message"].message_id)

def registration_start(bot, update, redis_db):
    query = update.callback_query
    user_id = query.from_user.id

    bot.send_message(chat_id=user_id, text="Введите ваш емейл")

    return "WAITING_EMAIL"


def accept_email(bot, update, redis_db):
    moltin_api_key = redis_db.get("MOLTIN_API_TOKEN").decode("utf-8")
    email = update.message.text
    try:
        email = validate_email(email).email
        user_name = f"{update.message.from_user.first_name} {update.message.from_user.last_name}"
        tg_id = update.message.from_user.id
        customer_id = redis_db.get(f"moltin_customer:{tg_id}")

        if not customer_id:
            customer_id = create_customer(moltin_api_key, user_name, email)
            redis_db.set(f"moltin_customer:{tg_id}", customer_id)
        else:
            customer_id = customer_id.decode("utf-8")

        cart_checkout(moltin_api_key, tg_id, customer_id, *user_name.split())

        products_keyboard = build_products_menu_keyboard(moltin_api_key)
        clear_cart(moltin_api_key, tg_id)
        update.message.reply_text(
            text="Емейл принят, с вами свяжутся", reply_markup=products_keyboard
        )

        return "MAIN_MENU"

    except EmailNotValidError:
        update.message.reply_text(text="Невалидный адрес, попробуйте заново:")
        return "WAITING_EMAIL"


def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    load_dotenv()

    TG_API_TOKEN = os.environ.get("TG_API")

    REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT = os.environ.get("REDIS_PORT", 6379)
    REDIS_DB_NUM = os.environ.get("REDIS_DB_NUM", 0)

    redis_db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_NUM)

    updater = Updater(TG_API_TOKEN)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler(
                "start",
                partial(
                    start,
                    redis_db=redis_db,
                ),
            )
        ],
        states={
            "MAIN_MENU": [
                CallbackQueryHandler(
                    callback=partial(
                        cart,
                        redis_db=redis_db,
                    ),
                    pattern=r"Корзина",
                ),
                CallbackQueryHandler(
                    partial(
                        product,
                        redis_db=redis_db,
                    )
                ),
            ],
            "PRODUCT": [
                CallbackQueryHandler(
                    callback=partial(
                        main_menu,
                        redis_db=redis_db,
                    ),
                    pattern=r"Назад",
                ),
                CallbackQueryHandler(
                    callback=partial(
                        cart,
                        redis_db=redis_db,
                    ),
                    pattern=r"Корзина",
                ),
                CallbackQueryHandler(
                    callback=partial(
                        add_to_cart,
                        redis_db=redis_db,
                    )
                ),
            ],
            "CART": [
                CallbackQueryHandler(
                    callback=partial(
                        registration_start,
                        redis_db=redis_db,
                    ),
                    pattern=r"Оплата",
                ),
                CallbackQueryHandler(
                    callback=partial(
                        main_menu,
                        redis_db=redis_db,
                    ),
                    pattern=r"В меню",
                ),
                CallbackQueryHandler(
                    callback=partial(
                        remove_from_cart,
                        redis_db=redis_db,
                    )
                ),
            ],
            "WAITING_EMAIL": [
                MessageHandler(
                    Filters.text,
                    partial(
                        accept_email,
                        redis_db=redis_db,
                    ),
                ),
            ],
        },
        fallbacks=[],
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
