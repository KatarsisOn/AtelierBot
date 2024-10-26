from telebot import TeleBot, types
import pandas as pd

# Инициализация бота и загрузка данных из csv
bot = TeleBot('7587635774:AAHF4WBq9wKxHgonlG2NPRVTs6Y2ufJb218')
data = pd.read_csv('materials.csv')

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(row_width=1)
    button_show = types.KeyboardButton("Показать имеющиеся материалы")
    markup.add(button_show)
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие.", reply_markup=markup)

# Показ списка материалов
@bot.message_handler(func=lambda message: message.text == "Показать имеющиеся материалы")
def show_materials(message):
    # Формирование списка материалов в ЦЕХУ и на СКЛАДЕ
    materials_text = "Материалы в ЦЕХУ:\n" + str(data[data['Место'] == 'ЦЕХ'][['Ткань', 'Количество']]) + \
                     "\n\nМатериалы на СКЛАДЕ:\n" + str(data[data['Место'] == 'СКЛАД'][['Ткань', 'Количество']])
    bot.send_message(message.chat.id, materials_text)

    # Выбор ткани для ЦЕХА
    materials = data[data['Место'] == 'ЦЕХ']['Ткань'].unique()
    markup = types.InlineKeyboardMarkup()
    for material in materials:
        markup.add(types.InlineKeyboardButton(material, callback_data=f"choose_{material}"))
    bot.send_message(message.chat.id, "Выберите вид материала для списания/доставки из ЦЕХА:", reply_markup=markup)

# Обработчик выбора ткани в ЦЕХУ
@bot.callback_query_handler(func=lambda call: call.data.startswith("choose_"))
def choose_material(call):
    material = call.data.split("_")[1]

    # Предложение списать выбранную ткань и кнопка доставки
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Списать", callback_data=f"spisat_{material}"),
               types.InlineKeyboardButton("Доставить", callback_data=f"dostavit_{material}"))
    bot.send_message(call.message.chat.id, f"Выберите действие для материала {material}:", reply_markup=markup)

# Обработчик списания ткани в ЦЕХУ
@bot.callback_query_handler(func=lambda call: call.data.startswith("spisat_"))
def spisat_material(call):
    material = call.data.split("_")[1]
    bot.send_message(call.message.chat.id, f"Введите количество для списания материала {material}.")
    bot.register_next_step_handler(call.message, lambda msg: apply_change(msg, material, action="spisat"))

# Обработчик доставки ткани из СКЛАДА в ЦЕХ
@bot.callback_query_handler(func=lambda call: call.data.startswith("dostavit_"))
def dostavit_material(call):
    material = call.data.split("_")[1]
    bot.send_message(call.message.chat.id, f"Введите количество для доставки материала {material} из СКЛАДА в ЦЕХ.")
    bot.register_next_step_handler(call.message, lambda msg: apply_change(msg, material, action="dostavit"))

# Обработчик изменения количества ткани
def apply_change(message, material, action):
    try:
        quantity = int(message.text)
        if action == "spisat":
            # Проверка наличия ткани в ЦЕХУ и списание
            current_quantity_ceh = data.loc[(data['Место'] == "ЦЕХ") & (data['Ткань'] == material), 'Количество'].values[0]
            if current_quantity_ceh < quantity:
                bot.send_message(message.chat.id, f"Недостаточно ед. материала {material} в ЦЕХУ. Доступно {current_quantity_ceh} штук.")
                return
            data.loc[(data['Место'] == "ЦЕХ") & (data['Ткань'] == material), 'Количество'] -= quantity
            bot.send_message(message.chat.id, f"Списано {quantity} ед. материала {material} из ЦЕХА.")

        elif action == "dostavit":
            # Проверка наличия ткани на СКЛАДЕ и доставка в ЦЕХ
            current_quantity_sklad = data.loc[(data['Место'] == "СКЛАД") & (data['Ткань'] == material), 'Количество'].values[0]
            if current_quantity_sklad < quantity:
                bot.send_message(message.chat.id, f"Недостаточно ед. материала {material} на СКЛАДЕ. Доступно {current_quantity_sklad} штук.")
                return
            data.loc[(data['Место'] == "СКЛАД") & (data['Ткань'] == material), 'Количество'] -= quantity
            data.loc[(data['Место'] == "ЦЕХ") & (data['Ткань'] == material), 'Количество'] += quantity
            bot.send_message(message.chat.id, f"Доставлено {quantity} ед. материала {material} из СКЛАДА в ЦЕХ.")

        # Проверка и пополнение склада, если количество ткани <= 0
        if action == "dostavit" or action == "spisat":
            current_quantity_sklad = data.loc[(data['Место'] == "СКЛАД") & (data['Ткань'] == material), 'Количество'].values[0]
            if current_quantity_sklad <= 0:
                data.loc[(data['Место'] == "СКЛАД") & (data['Ткань'] == material), 'Количество'] += 50
                bot.send_message(message.chat.id, f"Ткань {material} на СКЛАДЕ закончилась. Закуплено дополнительно 50 ед. материала.")

        # Сохранение изменений
        data.to_csv('materials.csv', index=False)
        
        # Возврат к кнопке "Показать имеющиеся материалы"
        markup = types.ReplyKeyboardMarkup(row_width=1)
        button_show = types.KeyboardButton("Показать имеющиеся материалы")
        markup.add(button_show)
        # bot.send_message(message.chat.id, "Выберите следующее действие.", reply_markup=markup)

    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат. Введите целое число.")

# Запуск бота
bot.polling(none_stop=True)
