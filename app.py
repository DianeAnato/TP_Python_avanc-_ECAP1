# ===== Importation des librairies =====#
import dash
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, callback
from dash import dash_table

# ===== Initialisation =====#
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# ===== Chargement des données =====#
df = pd.read_csv("datasets/data.csv")
df=df[['CustomerID', 'Gender', 'Location', 'Product_Category', 
       'Quantity', 'Avg_Price', 'Transaction_Date', 'Month', 'Discount_pct']]

df['CustomerID']=df['CustomerID'].fillna(0)
df["Location"] = df["Location"].fillna("Unknown")
df['CustomerID']= pd.to_numeric(df['CustomerID']).astype(int)
df["Transaction_Date"] = pd.to_datetime(df["Transaction_Date"])
df["Total_price"]=df['Avg_Price']*df['Quantity']*(1-(df['Discount_pct'])/100)

# ===== Fonctions métiers =====#
# CA
def calculer_chiffre_affaire(data):
   return data['Total_price'].sum()

#TOP 10
def frequence_meilleure_vente(data, top=10):
    # 1. Top 10 des produits les plus vendus 
    top_products = (
        data.groupby('Product_Category')['Quantity']
            .sum()
            .sort_values(ascending=False)
            .head(top)
            .index
    )

    # 2. Filtrer le dataset pour ne garder que ces produits
    filtered = data[data['Product_Category'].isin(top_products)]

    # 3. Calculer les ventes par sexe pour ces produits
    result = (
        filtered.groupby(['Product_Category', 'Gender'])['Quantity']
            .sum()
            .reset_index()
            .sort_values(['Quantity'], ascending=False)
    )

    return result

#Mois
def indicateur_du_mois(data, current_month=12):
    monthly_vente = data.groupby("Month")["Total_price"].sum()
    monthly_quant = data.groupby("Month")["Quantity"].sum()

    quant = monthly_quant.get(current_month, 0)
    vente = monthly_vente.get(current_month, 0)

    return quant, vente

### Graphique

#TOP 10
def barplot_top_10_ventes(data):
    # 1. Utilisation de ta fonction (ne pas modifier)
    df_plot = frequence_meilleure_vente(data)
    
    # 2. Création du graphique avec Plotly Express
    fig = px.bar(
        df_plot, 
        x='Quantity',           
        y='Product_Category',      
        color='Gender',            # Différencier par sexe
        barmode='group',           # Groupé 
        orientation='h',           # Horizontal
        title="Frequence des 10 meilleures ventes",
        labels={'Quantity': 'Total vente', 
                'Product_Category': 'Catégorie produit', 
                'Gender': 'Sexe'},
        # Pour garder l'ordre décroissant de ta fonction :
        category_orders={"Product_Category": df_plot['Product_Category'].unique().tolist()}
    )

    # 3. Ajustement esthétiqu
    fig.update_layout(
        plot_bgcolor='rgba(240, 245, 250, 1)', 
        bargap=0.2,      
        bargroupgap=0.1   
    )
    return fig

#CA
def plot_evolution_chiffre_affaire(data):
        # Agrégation par semaine du CA
    df_weekly = (
        data
        .set_index("Transaction_Date")
        .resample("W")["Total_price"]
        .sum()
        .reset_index()
    )

    fig_CA = go.Figure()

    fig_CA.add_trace(
        go.Scatter(
            x=df_weekly["Transaction_Date"],
            y=df_weekly["Total_price"],
            mode="lines",
            name="Chiffre d'affaires"
        )
    )

    fig_CA.update_layout(
        title="Evolution du Chiffre d'Affaire par semaine",  
        xaxis_title="Semaines",
        yaxis_title="Chiffre d'affaire"
    )
    return fig_CA
    

def plot_chiffre_affaire_mois(data): 
    _, dec_tp = indicateur_du_mois(data, 12)
    _, nov_tp = indicateur_du_mois(data, 11)
    fig = go.Figure()

    fig.add_trace(
        go.Indicator(
            mode="number+delta",
            value=dec_tp,
            title={"text": "CA Décembre",
                   "font": {"size": 20},
                   "align": "center"},
            delta={
                "reference": nov_tp,
                "relative": False,
                "valueformat": ".2s",
                "increasing": {"color": "green"},
                "decreasing": {"color": "red"}
            },
            number={"font": {"size": 45}}  
        )
    )

    fig.update_layout(height=300)  #  agrandir

    return fig

def plot_vente_mois(data):
    dec_qt, _ = indicateur_du_mois(data, 12)
    nov_qt, _ = indicateur_du_mois(data, 11)
    fig = go.Figure()

    fig.add_trace(
        go.Indicator(
            mode="number+delta",
            value=dec_qt,
            title={"text": "Vente Décembre",
                   "font": {"size": 20},
                   "align": "center"},
            delta={
                "reference": nov_qt,
                "relative": False,
                "valueformat": ".2s",
                "increasing": {"color": "green"},
                "decreasing": {"color": "red"}
            },
            number={"font": {"size": 45}}
        )
    )

    fig.update_layout(height=300,margin=dict(l=0, r=0, t=30, b=0))

    return fig

#table
def table_dernieres_ventes(data):
    table = data.sort_values(by="Transaction_Date", ascending=False).head(100)
    return table

# Liste des options du dropdown avec les bons noms de propriétés
zone=[{"label": "All", "value": "All"}] + [{"label": z, "value": z} for z in df["Location"].unique()]

# ===== Layout =====#
app.layout = dbc.Container([

    # Première ligne
    dbc.Row([
        dbc.Col(html.H3("ECAP Store", style={"fontWeight": "bold"}), width=9),

        dbc.Col(
            dcc.Dropdown(
                id='filtre',
                options=zone,
                value="All",
                placeholder="Choisissez des zones",
                style={"backgroundColor": "white"}
            ),
            width=3
        )
    ],
    style={
        "backgroundColor": "#a8c6cf",  
        "padding": "5px 15px",
        "borderRadius": "5px",
        "marginBottom": "15px"
    }),

    # Deuxième ligne
    dbc.Row([
        # 1ere colonne
        dbc.Col([
            dbc.Row([
                dbc.Col(dcc.Graph(id="ca_mois"),
                         width=6
                         ),
                dbc.Col(dcc.Graph(id="vente_mois"), 
                        width=6
                        ),
            ] ,style={"marginBottom": "15px"} ),

            dbc.Row([
                    dbc.Col(dcc.Graph(id="plot_hf"),
                            width=12 
                            )
            ], style={"height": "350px"})
         ],width=5, ), 
            

        # 2e colonne
        dbc.Col([
            #
            dbc.Row([
                dbc.Col(dcc.Graph(id="evol_ca"), 
                        width=12, 
                        )
            ], style={"marginBottom": "20px"}) ,

            #Table                  
            dbc.Row([
                dbc.Col([ 
                    html.H5("Tables des 100 dernières ventes", 
                            style={"color": "black","fontSize": "24px"}),
                    dash_table.DataTable(
                            id="table_ventes",
                            page_size=10,
                            style_table={
                                "height": "300px",
                                "overflowY": "auto",
                                "overflowX": "auto"
                            },
                            style_cell={
                                "textAlign": "center",
                                "padding": "5px",
                                "fontSize": "12px"
                            },
                            style_header={
                                "backgroundColor": "#f1f1f1",
                                "fontWeight": "bold"
                            }
                
                     )   
                 ],style={"backgroundColor": "white",
                          "padding": "15px",
                          "borderRadius": "12px",
                          "boxShadow": "0 4px 12px rgba(0,0,0,0.08)"} , width=12
                )
            ])

        ], width=7)
     ])
],fluid=True, style={"padding": "20px", "backgroundColor": "#f5f5f5"})


# ===== Callbacks =====#
#*CA
@app.callback(
    Output("ca_mois", "figure"),
    Input("filtre", "value")
)
def update_ca_mois(selected_zone):
    dff = df if selected_zone == "All" else df[df["Location"] == selected_zone]
    return plot_chiffre_affaire_mois(dff)

#*vente
@app.callback(
    Output("vente_mois", "figure"),
    Input("filtre", "value")
)
def update_vente_mois(selected_zone):
    dff = df if selected_zone == "All" else df[df["Location"] == selected_zone]
    return plot_vente_mois(dff)

#*CA
@app.callback(
    Output("evol_ca", "figure"),
    Input("filtre", "value")
)
def update_evol_ca(selected_zone):
    dff = df if selected_zone == "All" else df[df["Location"] == selected_zone]
    return plot_evolution_chiffre_affaire(dff)


@app.callback(
    Output("plot_hf", "figure"),
    Input("filtre", "value")
)
def update_plot_hf(selected_zone):
    dff = df if selected_zone == "All" else df[df["Location"] == selected_zone]
    return barplot_top_10_ventes(dff)
    

@app.callback(
    Output("table_ventes", "data"),
    Output("table_ventes", "columns"),
    Input("filtre", "value")
)
def update_table(selected_zone):
    dff = df if selected_zone == "All" else df[df["Location"] == selected_zone]
    dff = table_dernieres_ventes(dff)
    return (
        dff.to_dict("records"),
        [{"name": col, "id": col} for col in dff.columns]
    )

if __name__ == '__main__':
    app.run_server(debug=True)
