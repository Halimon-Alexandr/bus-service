# -*- coding: utf-8 -*-

from decouple import config
import os
import pickle
import pytz
import telebot
from telebot import types
from datetime import datetime, timedelta
import locale
from BusTrafficService import Tracking

locale.setlocale(locale.LC_ALL, ("uk_UA", "UTF-8"))

admin = config("TG_CHAT_ADMIN")
token = config("TG_BOT_TOKEN")
bot = telebot.TeleBot(token)
kiev_timezone = pytz.timezone("Europe/Kiev")

user_data = {}
tracking = Tracking()

# Клас для зберігання даних користувача
class User:
    def __init__(self, username):
        self.username = username
        self.search_query = ""
        self.last_visit = datetime.now(kiev_timezone)
        self.offset = 0
        self.interaction_count = 0

def fetch_and_parse_schedule(user):
    try:
        tracking.offset = user.offset
        result = tracking.get_bus_schedule(user.search_query)
        if "stops" in result:
            message_text = "Оберіть потрібну зупинку"
            button_texts = result.get("stops", [])
        else:
            next_bus_info = result
            message_text = (
                f"🚏 {next_bus_info['bus_stop']}.\n"
                f"\n👉 В напрямку {next_bus_info['direction']}.\n"
                f"\n🚌 №{next_bus_info['bus_number']}, "
                f"⌚ о {next_bus_info['arrival_time']}.\n"
                f"Через {next_bus_info['time_left']}\n"
            )
            button_texts = ["⬅️ Попередній", "🔄 Оновити", "➡️ Наступний", "🏠 Основне меню"]
    except ValueError as e:
        message_text = str(e)
        button_texts = ["Пошук 🔍", "Список 📄", "Допомога 🙋"]

    return message_text, button_texts

def help_menu():
    help_message = "📋 Коротенька допомога по кнопкам бота:\n\n"
    help_message += "🟢 /start - Початок роботи з ботом та головне меню.\n"
    help_message += "🔍 Пошук - Здійснення пошуку розкладу автобусів за назвою зупинки. Можна писати неповну назву.\n"
    help_message += "📄 Список - Перегляд списку всіх доступних зупинок.\n"
    help_message += "⬅️ Попередній - Перехід до попереднього результату пошуку.\n"
    help_message += "🔄 Оновити - Оновлення результатів пошуку відносно поточного часу.\n"
    help_message += "➡️ Наступний - Перехід до наступного результату пошуку.\n"
    help_message += "🏠 Основне меню - Повернення до головного меню.\n"
    help_message += "💬 'Адмін текст повідомлення' - надіслати повідомлення адміністратору бота.\n"
    return help_message

def generate_keyboard(button_texts):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    rows = [button_texts[i : i + 3] for i in range(0, len(button_texts), 3)]
    for row in rows:
        markup.add(*[types.KeyboardButton(text) for text in row])
    return markup

@bot.message_handler(commands=["start"])
def start(message):
    user_name = message.from_user.first_name if message.from_user.first_name else "друже"
    button_texts = ["Пошук 🔍", "Список 📄", "Допомога 🙋"]
    markup = generate_keyboard(button_texts)
    bot.send_message(
        message.chat.id,
        f"Привіт, {user_name}! 🤖 \nЯ бот для пошуку графіку руху міських автобусів в місті Могилів-Подільський",
        reply_markup=markup,
    )

@bot.message_handler(content_types=["text"])
def func(message):
    if message.chat.id not in user_data:
        username = message.from_user.first_name
        if message.from_user.last_name is not None:
            username += f" {message.from_user.last_name}"
        bot.send_message(admin, f"Ура-а-а! У нас новий користувач {username}.")
        user_data[message.chat.id] = User(username=username)
    user_data[message.chat.id].last_visit = datetime.now(kiev_timezone)
    user_data[message.chat.id].interaction_count += 1

    if message.text == "Звіт":
        current_time = datetime.now(kiev_timezone)
        sorted_user_list = sorted(user_data.items(), key=lambda item: item[1].last_visit, reverse=True)[:10]
        sum_interaction_count = sum(map(lambda item: item[1].interaction_count, user_data.items()))
        for user_id, user in sorted_user_list:
            if user.last_visit.date() == current_time.date():
                formatted_time = f"сьогодні о {user.last_visit.strftime('%H:%M')}"
            elif user.last_visit.date() == current_time.date() - timedelta(days=1):
                formatted_time = f"вчора о {user.last_visit.strftime('%H:%M')}"
            else:
                formatted_time = f"{user.last_visit.strftime('%d %B')}, о {user.last_visit.strftime('%H:%M')}"

            bot.send_message(
                message.chat.id,
                f"{user.username},\nЗапит: {user.search_query}.\nДата: {formatted_time}",
            )
        bot.send_message(
            message.chat.id,
            f"Всього користувачів {len(user_data)}, загальна кількість запитів від останнього перезавантаження {sum_interaction_count}",
        )

    elif "закріпити" in message.text.lower():
        text = " ".join(message.text.split()[1:])
        for user_id, user in user_data.items():
            to_pin = bot.send_message(user_id, text).message_id
            bot.pin_chat_message(chat_id=user_id, message_id=to_pin)

    elif "адмін" in message.text.lower():
        global sender_chat_id
        sender_chat_id = message.chat.id
        text = " ".join(message.text.split()[1:])
        bot.send_message(admin, f"{user_data[message.chat.id].username}: {text}")

    elif "відповідь" in message.text.lower():
        text = " ".join(message.text.split()[1:])
        bot.send_message(sender_chat_id, f"{user_data[message.chat.id].username}: {text}")

    elif message.text == "Список 📄":
        user_data[message.chat.id].search_query =""
        message_text, button_texts = fetch_and_parse_schedule(user_data[message.chat.id])
        if message_text:
            markup = generate_keyboard(button_texts)
            bot.send_message(message.chat.id, message_text, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Не вдалося отримати список зупинок.")

    elif message.text == "Пошук 🔍":
        bot.send_message(message.chat.id, "Введіть назву зупинки! \nНе обов'язково писати повну назву")

    elif message.text == "Допомога 🙋":
        bot.send_message(message.chat.id, help_menu())

    elif message.text == "⬅️ Попередній":
        user_data[message.chat.id].offset -= 1
        message_text, button_texts = fetch_and_parse_schedule(user_data[message.chat.id])
        if message_text:
            markup = generate_keyboard(button_texts)
            bot.send_message(message.chat.id, message_text, reply_markup=markup)

    elif message.text == "🔄 Оновити":
        user_data[message.chat.id].offset = 0
        message_text, button_texts = fetch_and_parse_schedule(user_data[message.chat.id])
        if message_text:
            markup = generate_keyboard(button_texts)
            bot.send_message(message.chat.id, message_text, reply_markup=markup)

    elif message.text == "➡️ Наступний":
        user_data[message.chat.id].offset += 1
        message_text, button_texts = fetch_and_parse_schedule(user_data[message.chat.id])
        if message_text:
            markup = generate_keyboard(button_texts)
            bot.send_message(message.chat.id, message_text, reply_markup=markup)

    elif message.text == "🏠 Основне меню":
        button_texts = ["Пошук 🔍", "Список 📄", "Допомога 🙋"]
        markup = generate_keyboard(button_texts)
        bot.send_message(message.chat.id, "Ви повернулись до основного меню.", reply_markup=markup)

    else:
        user_data[message.chat.id].search_query = message.text
        user_data[message.chat.id].offset = 0
        message_text, button_texts = fetch_and_parse_schedule(user_data[message.chat.id])
        if message_text:
            markup = generate_keyboard(button_texts)
            bot.send_message(message.chat.id, message_text, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Розклад не знайдено, спробуйте ще раз.")

    # Збереження користувацьких даних в файл
    with open("user_data.pickle", "wb") as f:
        pickle.dump(user_data, f)

bot.send_message(admin, "Бот перезавантажено!")
# Відновлення даних з файлу
if os.path.exists("user_data.pickle"):
    with open("user_data.pickle", "rb") as file:
        user_data = pickle.load(file)

    current_time = datetime.now(kiev_timezone)
    inactive_users = []

    for user_id, user in user_data.items():
        if (current_time - user.last_visit).days > 30:
            inactive_users.append(user_id)

    for user_id in inactive_users:
        del user_data[user_id]

    with open("user_data.pickle", "wb") as file:
        pickle.dump(user_data, file)
else:
    user_data = {}

# Processing other commands and text messages
bot.polling(none_stop=True)
