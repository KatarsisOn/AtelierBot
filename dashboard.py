import dash
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

