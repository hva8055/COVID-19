import requests
import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN])  
app.title = "COVID-19 Global Tracker Dashboard"

def get_country_data():     
    url = "https://disease.sh/v3/covid-19/countries"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data)
    df = df[['country', 'cases', 'todayCases', 'deaths', 'todayDeaths', 'recovered', 'active', 'critical', 'countryInfo']]
    df['lat'] = df['countryInfo'].apply(lambda x: x['lat'])
    df['long'] = df['countryInfo'].apply(lambda x: x['long'])
    return df

# Function to create today's summary cards
def generate_cards(df):
    total_cases = int(df['cases'].sum())
    total_deaths = int(df['deaths'].sum())
    total_recovered = int(df['recovered'].sum())

    card_style = {'textAlign': 'center', 'padding': '10px'}

    cards = dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("Total Cases", className="card-title"),
                html.H2(f"{total_cases:,}", className="card-text text-warning")
            ])
        ], color="dark"), width=4),

        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("Total Deaths", className="card-title"),
                html.H2(f"{total_deaths:,}", className="card-text text-danger")
            ])
        ], color="dark"), width=4),

        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("Total Recovered", className="card-title"),
                html.H2(f"{total_recovered:,}", className="card-text text-success")
            ])
        ], color="dark"), width=4)
    ])
    return cards

# Layout of the app
app.layout = dbc.Container([
    html.H1("🌎 COVID-19 Global Tracker Dashboard", style={'textAlign': 'center', 'marginTop': 20}),
    html.Hr(),

    # Summary cards
    html.Div(id="summary-cards"),
    html.Br(),

    # World map
    dcc.Graph(id="world-map"),

    html.Br(),

    # Dropdown for country selection
    html.H4("Compare Country Trends (Last 30 Days):", style={'textAlign': 'center'}),
    dcc.Dropdown(id="country-dropdown",
                 multi=True,
                 placeholder="Select one or more countries...",
                 style={'width': '80%', 'margin': 'auto'}),

    dcc.Graph(id="country-trend"),

    # Refresh data every 10 minutes
    dcc.Interval(id="interval-component", interval=600*1000, n_intervals=0)  # 600 seconds = 10 minutes

], fluid=True)

# Callback to update map, summary, dropdown and graph
@app.callback(
    [Output("world-map", "figure"),
     Output("summary-cards", "children"),
     Output("country-dropdown", "options")],
    [Input("interval-component", "n_intervals")]
)
def update_data(n):
    df = get_country_data()

    # World Map
    fig_map = px.scatter_geo(
        df,
        lat='lat',
        lon='long',
        hover_name="country",
        size="cases",
        size_max=40,
        template="plotly_dark",
        color="cases",
        color_continuous_scale="reds",
        title="Worldwide COVID-19 Cases",
        projection="natural earth"
    )

    # Update dropdown options
    options = [{"label": country, "value": country} for country in df['country'].unique()]

    # Update summary cards
    cards = generate_cards(df)

    return fig_map, cards, options

# Callback to update trend graph
@app.callback(
    Output("country-trend", "figure"),
    Input("country-dropdown", "value")
)
def update_trend(selected_countries):
    if not selected_countries:
        return px.line(title="Select countries to view trends.")

    if isinstance(selected_countries, str):
        selected_countries = [selected_countries]

    fig = px.line()
    for country in selected_countries:
        url = f"https://disease.sh/v3/covid-19/historical/{country}?lastdays=30"
        response = requests.get(url)
        data = response.json()

        if "timeline" not in data:
            continue

        timeline = data['timeline']
        dates = list(timeline['cases'].keys())

        df_country = pd.DataFrame({
            'Date': pd.to_datetime(dates),
            'Cases': list(timeline['cases'].values()),
            'Deaths': list(timeline['deaths'].values()),
            'Recovered': list(timeline['recovered'].values())
        })

        fig.add_scatter(x=df_country['Date'], y=df_country['Cases'], mode='lines+markers', name=f"{country} - Cases")
        fig.add_scatter(x=df_country['Date'], y=df_country['Deaths'], mode='lines+markers', name=f"{country} - Deaths")
        fig.add_scatter(x=df_country['Date'], y=df_country['Recovered'], mode='lines+markers', name=f"{country} - Recovered")

    fig.update_layout(title="COVID-19 Trends", template="plotly_dark", xaxis_title="Date", yaxis_title="Count")
    return fig

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
