import pandas as pd
import plotly.express as px
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

# Carregar o arquivo CSV
df = pd.read_csv('https://raw.githubusercontent.com/bryanthebem/plot_gustavo/refs/heads/main/Summer_olympic_Medals.csv')

# Filtrar os dados entre 1992 e 2020
df = df[(df['Year'] >= 1992) & (df['Year'] <= 2020)].copy() # Usar .copy() para evitar SettingWithCopyWarning

# Calcular o total de medalhas para cada país por ano
# Agrupar por país e ano antes de calcular o total para ter dados anuais
df_yearly_country = df.groupby(['Country_Name', 'Year'])[['Gold', 'Silver', 'Bronze']].sum().reset_index()
df_yearly_country['Total_Medals'] = df_yearly_country['Gold'] + df_yearly_country['Silver'] + df_yearly_country['Bronze']


# Funções para gerar os gráficos
def create_map_fig(medal_type='Todas'):
    # Agrupar dados por país, somando as medalhas para o período completo
    if medal_type == 'Todas':
        df_country_medals = df_yearly_country.groupby('Country_Name')['Total_Medals'].sum().reset_index()
        color_col = 'Total_Medals'
        title_medal_text = 'Total de Medalhas'
    else:
        df_country_medals = df_yearly_country.groupby('Country_Name')[medal_type].sum().reset_index()
        color_col = medal_type
        title_medal_text = medal_type # Será Gold, Silver ou Bronze

    map_fig = px.choropleth(df_country_medals,
                            locations='Country_Name',
                            locationmode='country names',
                            color=color_col,
                            hover_name='Country_Name',
                            color_continuous_scale=px.colors.sequential.YlOrRd,
                            title=f'{title_medal_text} de 1992 a 2020')
    map_fig.update_layout(title_x=0.5) # Centralizar o título
    return map_fig


def create_area_fig(medal_type='Todas'):
    top_countries = df_yearly_country.groupby('Country_Name')['Total_Medals'].sum().nlargest(10).index

    # Filtrar os dados anuais apenas para os top 10 países
    df_top_10_countries_yearly = df_yearly_country[df_yearly_country['Country_Name'].isin(top_countries)]

    # Definir qual coluna usar para o eixo Y e o título
    y_col = 'Total_Medals' if medal_type == 'Todas' else medal_type
    title_medal_text = 'Total de Medalhas' if medal_type == 'Todas' else medal_type # Será Gold, Silver ou Bronze

    area_fig = px.area(df_top_10_countries_yearly,
                       x="Year",
                       y=y_col,
                       color="Country_Name",
                       title=f'Top 10 Países por {title_medal_text} de 1992 a 2020')
    area_fig.update_layout(title_x=0.5) # Centralizar o título
    return area_fig


def create_bar_fig(year=None, medal_type='Todas'):
    # Filtrar dados pelo ano selecionado, se houver.
    filtered_df = df_yearly_country[df_yearly_country['Year'] == year] if year else df_yearly_country

    # Definir qual coluna usar para o eixo Y e para a seleção dos top 10
    y_col = 'Total_Medals' if medal_type == 'Todas' else medal_type
    title_medal_text = 'Total de Medalhas' if medal_type == 'Todas' else medal_type # Será Gold, Silver ou Bronze

    # Agrupar por país e somar as medalhas (do tipo selecionado ou total) para o período/ano filtrado
    df_country_medals = filtered_df.groupby('Country_Name')[y_col].sum().reset_index()

    # Selecionar os top 10 países com base na coluna definida (y_col)
    df_top_countries = df_country_medals.nlargest(10, y_col)

    # Definir o título do gráfico
    title_year_text = f"em {year}" if year else "de 1992 a 2020"
    title_text = f'Top 10 Países com Mais {title_medal_text} {title_year_text}'

    # Definir a cor da barra (opcionalmente, pode ser baseado no tipo de medalha)
    bar_color = 'gold' if medal_type == 'Gold' else ('silver' if medal_type == 'Silver' else ('#cd7f32' if medal_type == 'Bronze' else px.colors.qualitative.Plotly[0])) # #cd7f32 é um tom de bronze

    bar_fig = px.bar(df_top_countries,
                     x='Country_Name',
                     y=y_col,
                     color_discrete_sequence=[bar_color],
                     title=title_text)
    bar_fig.update_layout(title_x=0.5) # Centralizar o título
    return bar_fig


def create_pie_chart(country):
    # Filtrar dados para o país selecionado para o período completo
    filtered_df = df_yearly_country[df_yearly_country['Country_Name'] == country]
    # Somar as medalhas por tipo para o país selecionado
    medal_counts = filtered_df[['Gold', 'Silver', 'Bronze']].sum()

    fig = px.pie(
        values=medal_counts.values,
        names=medal_counts.index,
        title=f'Distribuição de Medalhas para {country} (1992-2020)',
        hole=0.3,
        labels={'Gold': 'Ouro', 'Silver': 'Prata', 'Bronze': 'Bronze'}
    )
    fig.update_layout(title_x=0.5) # Centralizar o título
    return fig


# Criar um aplicativo Dash
app = dash.Dash(__name__)
server = app.server 

# Layout do aplicativo
app.layout = html.Div([
    html.H1("Dashboard de Medalhas Olímpicas de Verão (1992-2020)", style={'textAlign': 'center'}),

    # Gráfico de Mapa
    dcc.Graph(figure=create_map_fig(), id='map', style={'height': '60vh', 'width': '100%', 'marginBottom': '20px'}), # Aumentei a altura e adicionei margem

    # Container para Gráficos de Área e Barras (usando flexbox para alinhamento lado a lado)
    html.Div([
        dcc.Graph(figure=create_area_fig(), id='area-chart', style={'flex': 1, 'marginRight': '10px'}), # flex: 1 faz os gráficos ocuparem espaço igual
        dcc.Graph(figure=create_bar_fig(), id='bar-chart', style={'flex': 1, 'marginLeft': '10px'})
    ], style={'display': 'flex', 'marginBottom': '20px'}), # display: flex coloca os itens em linha

    # Container para Filtros (usando flexbox para alinhamento lado a lado)
    # Colocamos os filtros abaixo dos gráficos de área/barra, no mesmo nível para alinhá-los.
    html.Div([
        # Filtro de Tipo de Medalha
        html.Div([
            html.Label('Selecione o Tipo de Medalha:'),
            dcc.Dropdown(
                id='medal-type-dropdown',
                options=[
                    {'label': 'Todas', 'value': 'Todas'},
                    {'label': 'Ouro', 'value': 'Gold'},
                    {'label': 'Prata', 'value': 'Silver'},
                    {'label': 'Bronze', 'value': 'Bronze'}
                ],
                value='Todas', # Valor padrão
                clearable=False # Impede que o usuário desmarque tudo
            )
        ], style={'flex': 1, 'marginRight': '10px'}), # Este filtro ficará à esquerda no container flex

        # Filtro de Ano Olímpico
        html.Div([
            html.Label('Selecione o Ano Olímpico:'),
            dcc.Dropdown(
                id='year-dropdown',
                options=[{'label': year, 'value': year} for year in sorted(df_yearly_country['Year'].unique())], # Opções ordenadas
                value=df_yearly_country['Year'].min(), # Valor padrão (primeiro ano)
                clearable=False # Impede que o usuário desmarque tudo
            )
        ], style={'flex': 1, 'marginLeft': '10px'}), # Este filtro ficará à direita no container flex

    ], style={'display': 'flex', 'marginBottom': '20px'}), # display: flex para os filtros ficarem lado a lado

    # Container para Filtro de País e Gráfico de Pizza
    # Mantemos este separado pois o filtro de país só afeta o gráfico de pizza
    html.Div([
        html.Label('Selecione o País (para o Gráfico de Pizza):'), # Rótulo mais claro
        dcc.Dropdown(
            id='country-dropdown',
            options=[{'label': country, 'value': country} for country in sorted(df['Country_Name'].unique())], # Opções ordenadas
            value='Estados Unidos da América' # Valor padrão
        ),
        dcc.Graph(id='pie-chart')
    ], style={'marginTop': '20px'}) # Adiciona um pouco de espaço acima desta seção
])


# Callbacks para atualizar os gráficos
# Callback para o Mapa 
@app.callback(
    Output('map', 'figure'),
    [Input('medal-type-dropdown', 'value')]
)
def update_map(medal_type):
    return create_map_fig(medal_type)

# Callback para o Gráfico de Área
@app.callback(
    Output('area-chart', 'figure'),
    [Input('medal-type-dropdown', 'value')]
)
def update_area_chart(medal_type):
    return create_area_fig(medal_type)

# Callback para o Gráfico de Barras 
@app.callback(
    Output('bar-chart', 'figure'),
    [Input('year-dropdown', 'value'),
     Input('medal-type-dropdown', 'value')] # Adicionado Input para o filtro de tipo de medalha
)
def update_bar_chart(year, medal_type):
    return create_bar_fig(year, medal_type)


# Callback para o Gráfico de Pizza 
@app.callback(
    Output('pie-chart', 'figure'),
    [Input('country-dropdown', 'value')]
)
def update_pie_chart(country):
    return create_pie_chart(country)


# Executar o aplicativo
if __name__ == '__main__':
    app.run_server(debug=True)
