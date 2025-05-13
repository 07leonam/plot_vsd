import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Carregando os dados
try:
    df_full = pd.read_csv('https://raw.githubusercontent.com/07leonam/plot_vsd/refs/heads/main/Summer_olympic_Medals.csv')
except FileNotFoundError:
    print("Erro: 'Summer_olympic_Medals.csv' não encontrado. Certifique-se de que o arquivo está no diretório correto.")
    exit()
except Exception as e:
    print(f"Erro ao carregar o CSV: {e}")
    exit()

# Verificando colunas esperadas
expected_cols_from_user = ['Year', 'Host_country', 'Host_city', 'Country_Name', 'Country_Code', 'Gold', 'Silver', 'Bronze']
missing_cols = [col for col in expected_cols_from_user if col not in df_full.columns]
if missing_cols:
    print(f"Erro: O arquivo CSV está faltando as seguintes colunas esperadas: {', '.join(missing_cols)}")
    print(f"Colunas disponíveis são: {', '.join(df_full.columns)}")
    exit()

# Corrigindo nome do país
df_full['Country_Name'] = df_full['Country_Name'].replace('United States', 'United States of America')

# Filtrando anos
df = df_full[(df_full['Year'] >= 1992) & (df_full['Year'] <= 2020)].copy()

# Calculando total de medalhas
df['Total_Medals'] = df['Gold'] + df['Silver'] + df['Bronze']

# Preparando listas para os dropdowns
all_countries = sorted(df['Country_Name'].unique())
medal_types = ['Gold', 'Silver', 'Bronze', 'Total_Medals']

# Criando opções de ano
year_host_info = df[['Year', 'Host_city', 'Host_country']].drop_duplicates().sort_values('Year')
year_options = [{'label': 'Todos os anos (1992-2020)', 'value': 'All'}] + \
               [{'label': f"{row['Year']} - {row['Host_city']}, {row['Host_country']}", 'value': row['Year']}
                for index, row in year_host_info.iterrows()]

# Inicializando o app Dash
app = dash.Dash(__name__)
server = app.server

# Layout do app
app.layout = html.Div(children=[
    html.H1("Painel de Medalhas Olímpicas (1992-2020)", style={'textAlign': 'center'}),

    html.Div(className='filters-row', children=[
        html.Div([
            html.Label("Selecione o ano das Olimpíadas (para o gráfico de barras):"),
            dcc.Dropdown(
                id='year-dropdown',
                options=year_options,
                value='All'
            )
        ], style={'width': '32%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            html.Label("Selecione o tipo de medalha (para o mapa, área e barras):"),
            dcc.Dropdown(
                id='medal-type-dropdown',
                options=[{'label': medal.replace('_', ' '), 'value': medal} for medal in medal_types],
                value='Total_Medals'
            )
        ], style={'width': '32%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            html.Label("Selecione o país (para o gráfico de pizza):"),
            dcc.Dropdown(
                id='country-dropdown',
                options=[{'label': country, 'value': country} for country in all_countries],
                value=all_countries[0] if all_countries else None
            )
        ], style={'width': '32%', 'display': 'inline-block', 'padding': '10px'}),
    ], style={'display': 'flex', 'justifyContent': 'center', 'flexWrap': 'wrap', 'marginBottom': '30px'}),

    html.Div(className='charts-row', children=[
        html.Div([dcc.Graph(id='pie-chart')], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}),
        html.Div([dcc.Graph(id='map-chart')], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}),
    ], style={'display': 'flex', 'justifyContent': 'center', 'flexWrap': 'wrap'}),

    html.Div(className='charts-row', children=[
        html.Div([dcc.Graph(id='area-chart')], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}),
        html.Div([dcc.Graph(id='bar-chart')], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}),
    ], style={'display': 'flex', 'justifyContent': 'center', 'flexWrap': 'wrap'})
])

# Callback do gráfico de pizza
@app.callback(
    Output('pie-chart', 'figure'),
    [Input('country-dropdown', 'value')]
)
def update_pie_chart(selected_country):
    if not selected_country:
        fig = px.pie(title="Por favor, selecione um país")
        fig.update_layout(annotations=[dict(text='Nenhum país selecionado', showarrow=False)])
        return fig

    country_data = df[df['Country_Name'] == selected_country]
    if country_data.empty:
        fig = px.pie(title=f"Sem dados para {selected_country} (1992-2020)")
        fig.update_layout(annotations=[dict(text='Dados não disponíveis', showarrow=False)])
        return fig

    medal_sum = country_data[['Gold', 'Silver', 'Bronze']].sum()
    medal_counts_df = pd.DataFrame({
        'Tipo de Medalha': ['Ouro', 'Prata', 'Bronze'],
        'Quantidade': [medal_sum.get('Gold', 0), medal_sum.get('Silver', 0), medal_sum.get('Bronze', 0)]
    })

    fig_pie = px.pie(medal_counts_df,
                     names='Tipo de Medalha',
                     values='Quantidade',
                     title=f'Distribuição de Medalhas de {selected_country} (1992-2020)',
                     color='Tipo de Medalha',
                     color_discrete_map={'Ouro': 'gold', 'Prata': 'silver', 'Bronze': '#cd7f32'})
    fig_pie.update_traces(textposition='inside', textinfo='percent+label+value')
    return fig_pie

# Callback do mapa
@app.callback(
    Output('map-chart', 'figure'),
    [Input('medal-type-dropdown', 'value')]
)
def update_map_chart(selected_medal_type):
    medal_col = selected_medal_type
    map_data = df.groupby('Country_Name', as_index=False)[medal_col].sum()

    fig_map = px.choropleth(map_data,
                            locations='Country_Name',
                            locationmode='country names',
                            color=medal_col,
                            hover_name='Country_Name',
                            color_continuous_scale=px.colors.sequential.YlOrRd,
                            title=f'Total de {medal_col.replace("_", " ")} por país (1992-2020)')
    return fig_map

# Callback da área
@app.callback(
    Output('area-chart', 'figure'),
    [Input('medal-type-dropdown', 'value')]
)
def update_area_chart(selected_medal_type):
    medal_col = selected_medal_type

    df_country_year_medals = df.groupby(['Country_Name', 'Year'], as_index=False)[medal_col].sum()
    top_10_countries_overall = df.groupby('Country_Name')[medal_col].sum().nlargest(10).index
    df_top_10 = df_country_year_medals[df_country_year_medals['Country_Name'].isin(top_10_countries_overall)]

    fig_area = px.area(df_top_10,
                       x="Year",
                       y=medal_col,
                       color="Country_Name",
                       title=f'Top 10 países por {medal_col.replace("_", " ")} (1992-2020)',
                       labels={medal_col: medal_col.replace("_", " ") + ' conquistadas'})
    fig_area.update_xaxes(type='category')
    return fig_area

# Callback do gráfico de barras
@app.callback(
    Output('bar-chart', 'figure'),
    [Input('medal-type-dropdown', 'value'),
     Input('year-dropdown', 'value')]
)
def update_bar_chart(selected_medal_type, selected_year_value):
    medal_col = selected_medal_type
    current_df_bar = df.copy()
    
    year_title_segment = "Todos os anos (1992-2020)"
    if selected_year_value != 'All':
        current_df_bar = current_df_bar[current_df_bar['Year'] == selected_year_value]
        year_label_info_obj = next((item for item in year_options if item['value'] == selected_year_value), None)
        if year_label_info_obj:
            year_title_segment = year_label_info_obj['label']
        else:
            year_title_segment = str(selected_year_value)

    df_grouped_bar = current_df_bar.groupby('Country_Name', as_index=False)[medal_col].sum()
    df_grouped_bar = df_grouped_bar.nlargest(10, medal_col)

    bar_color_val = None
    if medal_col == 'Gold': bar_color_val = 'gold'
    elif medal_col == 'Silver': bar_color_val = 'silver'
    elif medal_col == 'Bronze': bar_color_val = '#cd7f32'

    fig_bar = px.bar(df_grouped_bar,
                     x='Country_Name',
                     y=medal_col,
                     title=f'Top 10 países por {medal_col.replace("_", " ")} em {year_title_segment}',
                     labels={'Country_Name': 'País', medal_col: medal_col.replace("_", " ")})
    if bar_color_val:
        fig_bar.update_traces(marker_color=bar_color_val)
    return fig_bar

if __name__ == '__main__':
    app.run_server(debug=True)
