# ATELIERBOT
Данный телеграмм-бот предназначен для использования работниками ателье. Бот ускоряет процесс поиска материалов с помощью ведения их учёта в csv-файле. При помощи бота, работники списывают, отправляют запрос на доставку и поставку материалов.

## Запуск на локальной машине

Чтобы запустить бота на локальной машине, необходимо вставить id бота в телеграмм, а затем запустить код бота в среде предназначенной для Python. Ссылка на бота [https://t.me/Atelier2004_bot]

## Как пользоваться ботом
1. Чтобы начать работать с ботом необходимо написать команду «/start», после чего появится кнопка «Показать имеющиеся материалы». 
2. При нажатии на кнопку появляется таблица и кнопки для выбора материала.
3. После выбора материала, бот предоставляет выбор: списать или доставить. В обоих случаях работник вводит нужное ему количество материала.
   а) Списание чаще всего производит мастер, списывая затраченные в ходе работы материалы.
   б) "Доставка" отправляет запрос заведующему складом на необходимое количество материалов, которое нужно доставить в цех.
   в) В случае, если материалы на складе заканчиваются, заведующий складом проводит закупку соответствующего материала на 50 ед.
   
## Код телеграмм-бота

```from telebot import TeleBot, types
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
    bot.send_message(message.chat.id, "Добро пожаловать!", reply_markup=markup)

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
```

## Код дашборда

```import dash
from dash import dcc, html, dash_table, Input, Output, State
import pandas as pd
import plotly.express as px

# Загружаем данные из CSV
data = pd.read_csv('materials.csv')

# Инициализация приложения Dash
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Дашборд остатков материалов в Ателье"),
    
    # Фильтр по типу ткани
    html.Label("Фильтрация по типу ткани:"),
    dcc.Dropdown(
        id='filter_material_type',
        options=[{'label': material, 'value': material} for material in data['Ткань'].unique()],
        multi=True,
        placeholder="Выберите тип ткани"
    ),

    # Фильтр по местоположению
    html.Label("Фильтрация по местоположению:"),
    dcc.RadioItems(
        id='filter_location',
        options=[
            {'label': 'ЦЕХ', 'value': 'ЦЕХ'},
            {'label': 'СКЛАД', 'value': 'СКЛАД'},
            {'label': 'Оба', 'value': 'Оба'}
        ],
        value='Оба',
        inline=True
    ),
    
    # Таблица остатков
    dash_table.DataTable(
        id='materials_table',
        columns=[{"name": i, "id": i} for i in data.columns],
        data=data.to_dict('records'),
        style_cell={'textAlign': 'left'},
        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
    ),

    # Гистограмма остатков
    dcc.Graph(id='inventory_chart'),

    # Панель предупреждений
    html.Div(id='warning_panel', style={'color': 'red', 'fontWeight': 'bold', 'marginTop': '20px'}),

    # Кнопка обновления данных
    html.Button("Обновить данные", id="refresh_button", n_clicks=0),
])

# Функция для обновления таблицы и графика при изменении фильтров
@app.callback(
    [Output('materials_table', 'data'), Output('inventory_chart', 'figure'), Output('warning_panel', 'children')],
    [Input('filter_material_type', 'value'), Input('filter_location', 'value'), Input('refresh_button', 'n_clicks')]
)
def update_dashboard(selected_materials, selected_location, n_clicks):
    # Загружаем данные
    data = pd.read_csv('materials.csv')
    
    # Применение фильтров
    if selected_materials:
        data = data[data['Ткань'].isin(selected_materials)]
    if selected_location != 'Оба':
        data = data[data['Место'] == selected_location]

    # Обновление таблицы
    table_data = data.to_dict('records')
    
    # Гистограмма остатков
    fig = px.bar(data, x='Ткань', y='Количество', color='Место', barmode='group',
                 title="Остатки материалов по местоположению")

    # Панель предупреждений
    warnings = []
    for _, row in data.iterrows():
        if row['Количество'] <= 5:
            warnings.append(f"{row['Ткань']} в {row['Место']} заканчивается: осталось {row['Количество']} ед.")
    warning_text = "\n".join(warnings) if warnings else "Все материалы в достаточном количестве."

    return table_data, fig, warning_text

# Запуск приложения
if __name__ == '__main__':
    app.run_server(debug=True)
```

## Контактная информация

GitHub [https://github.com/KatarsisOn] Email [maks.kashkarov@gmail.com]
