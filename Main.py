import telebot
from telebot import types
import requests

TOKEN = 'ТОКЕН ОТ БОТА'
bot = telebot.TeleBot(TOKEN)
# Словарь для отслеживания текущего шага пользователя
user_steps = {}

# Словарь для хранения собранных данных
user_data = {}

# ID пользователя (администратора), которому будет отправлена собранная информация
ADMIN_CHAT_ID = 'ID АДМИНА,КОТОРОМУ ПРИДУТ ДАННЫЕ'


def add_lead_to_bitrix24(data):
    BITRIX24_WEBHOOK_URL = "https://yourdomain.bitrix24.ru/rest/1/your_webhook_token/crm.lead.add.json"
    payload = {
        "fields": {
            "TITLE": f"{data['surname']} {data['name']} {data['patronymic']}",
            "NAME": data['name'],
            "LAST_NAME": data['surname'],
            "SECOND_NAME": data['patronymic'],
            "PHONE": [{"VALUE": data['phone'], "VALUE_TYPE": "WORK"}]
        }
    }
    response = requests.post(BITRIX24_WEBHOOK_URL, json=payload)
    if response.status_code == 200:
        print("Lead successfully added to Bitrix24")
    else:
        print("Failed to add lead to Bitrix24")
# Функция для сбора данных
def request_next_part_of_data(message):
    chat_id = message.chat.id
    step = user_steps.get(chat_id, 0)

    # Фамилия
    if step == 0:
        msg = bot.send_message(chat_id, "Введите вашу фамилию:")
        bot.register_next_step_handler(msg, request_next_part_of_data)
        user_steps[chat_id] = 1
    # Имя
    elif step == 1:
        user_data[chat_id] = {'surname': message.text}
        msg = bot.send_message(chat_id, "Введите ваше имя:")
        bot.register_next_step_handler(msg, request_next_part_of_data)
        user_steps[chat_id] = 2
    # Отчество
    elif step == 2:
        user_data[chat_id]['name'] = message.text
        msg = bot.send_message(chat_id, "Введите ваше отчество:")
        bot.register_next_step_handler(msg, request_next_part_of_data)
        user_steps[chat_id] = 3
    # Номер телефона
    elif step == 3:
        user_data[chat_id]['patronymic'] = message.text
        msg = bot.send_message(chat_id, "Введите ваш номер телефона:")
        bot.register_next_step_handler(msg, request_next_part_of_data)
        user_steps[chat_id] = 4
    # Отправка данных администратору и отображение кнопок
    elif step == 4:
        user_data[chat_id]['phone'] = message.text
        # Создание карточки лида в Bitrix24
        add_lead_to_bitrix24(user_data[chat_id])
        # Отправка собранных данных администратору
        data = user_data[chat_id]
        bot.send_message(ADMIN_CHAT_ID,
                         f"Фамилия: {data['surname']}\nИмя: {data['name']}\nОтчество: {data['patronymic']}\nТелефон: {data['phone']}")
        # Сброс шага
        user_steps[chat_id] = 0
        # Показываем кнопки пользователю
        send_menu(chat_id)


# Функция для отправки текста из файла
def send_text_from_file(chat_id, filename):
    try:
        with open(f'content/{filename}.txt', 'r', encoding='utf-8') as file:
            text = file.read()
            bot.send_message(chat_id, text)
    except FileNotFoundError:
        bot.send_message(chat_id, "Информация временно недоступна.")

# Функция для отправки файла
def send_file(chat_id, filename):
    try:
        with open(f'files/{filename}.pdf', 'rb') as file:
            bot.send_document(chat_id, file)
    except FileNotFoundError:
        bot.send_message(chat_id, "Файл временно недоступен.")

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    welcome_text = "Добро пожаловать! Для начала давайте соберем некоторую информацию."
    bot.send_message(chat_id, welcome_text)
    request_next_part_of_data(message)

# Функция для отправки меню с inline кнопками
def send_menu(chat_id):
    markup = types.InlineKeyboardMarkup()
    # Добавляем кнопки для первого ряда
    markup.add(types.InlineKeyboardButton("История компании", callback_data='history'),
               types.InlineKeyboardButton("Направления деятельности", callback_data='directions'))
    # Добавляем кнопки для второго ряда
    markup.add(types.InlineKeyboardButton("Объекты с активным сбором", callback_data='objects'),
               types.InlineKeyboardButton("Минимальный порог входа", callback_data='minimal'))
    # Продолжаем добавлять кнопки по две в ряд
    # Третий ряд
    markup.add(types.InlineKeyboardButton("Преимущества работы", callback_data='advantages'),
               types.InlineKeyboardButton("Наши контакты", callback_data='contacts'))
    # Четвертый ряд
    markup.add(types.InlineKeyboardButton("Заявка на консультацию", callback_data='consultation'),
               types.InlineKeyboardButton("Шаблон договора ИЗ", callback_data='loans'))
    # Пятый ряд
    markup.add(types.InlineKeyboardButton("Шаблон договора с фикс. %", callback_data='fixed'),
               types.InlineKeyboardButton("Условия реферальной программы", callback_data='referral'))
    # Шестой ряд
    markup.add(types.InlineKeyboardButton("Режим работы", callback_data='timing'),
               types.InlineKeyboardButton("Построить маршрут до офиса", callback_data='waypoint'))
    # Седьмой ряд
    markup.add(types.InlineKeyboardButton("Наш сайт", url='https://capitalis.pro'),
               types.InlineKeyboardButton("Наш Telegram канал", url='https://t.me/capitalisreal'))
    # Восьмой ряд
    markup.add(types.InlineKeyboardButton("Наш ВК", url='https://vk.com/capitalispro'),
               types.InlineKeyboardButton("Перечень документов для заключения договора", callback_data='list'))
    # И так далее для других кнопок...

    bot.send_message(chat_id, "Выберите необходимый пункт меню", reply_markup=markup)


# Обработчик callback запросов от inline кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    # Получаем chat_id из вызова
    chat_id = call.message.chat.id

    # Словарь с функциями для вызова по callback_data
    actions = {
        'history': lambda: send_text_from_file(chat_id, "company_history"),
        'directions': lambda: send_text_from_file(chat_id, "investment_directions"),
        'objects': lambda: send_text_from_file(chat_id, "active_collection_objects"),
        'minimal': lambda: send_text_from_file(chat_id, "minimal_entry_threshold"),
        'advantages': lambda: send_text_from_file(chat_id, "work_advantages"),
        'contacts': lambda: send_text_from_file(chat_id, "our_contacts"),
        'consultation': lambda: send_text_from_file(chat_id, "consultation_request"),
        'loans': lambda: send_file(chat_id, "loan_agreement_template"),
        'fixed': lambda: send_file(chat_id, "fixed_interest_agreement_template"),
        'referral': lambda: send_text_from_file(chat_id, "referral_program_terms"),
        'timing': lambda: send_text_from_file(chat_id, "working_hours"),
        'waypoint': lambda: send_text_from_file(chat_id, "route_to_office"),
        'site': lambda: send_text_from_file(chat_id, "our_website"),
        'tgchannel': lambda: send_text_from_file(chat_id, "our_telegram_channel"),
        'vk': lambda: send_text_from_file(chat_id, "our_vk"),
        'list': lambda: send_text_from_file(chat_id, "documents_list_for_contract")
    }

    # Вызываем соответствующую функцию, если callback_data существует в словаре
    if call.data in actions:
        actions[call.data]()
    else:
        bot.send_message(chat_id, "Извините, я не понимаю эту команду.")

# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)
