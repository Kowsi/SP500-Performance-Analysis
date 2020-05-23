import pandas_datareader.data as web
import pandas as pd
import datetime 
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np

import dash
import dash_html_components as html
import dash_core_components as dcc

#Sector Performance details from ALPHA VANTAGE

SECTOR_PERFORMANCE_COLUMN = ['5D', '1M', '3M', 'YTD', '1Y']
SP500_STOCKS_FILE = 'SP_500.Characteristics.csv'


end = datetime.datetime.now()
start = datetime.datetime(end.year - 5, end.month , end.day)
master_df = None
sector_list = sp.Sector.dropna().unique().tolist()
ticker_list = sp.index.to_list()
#ticker_list.append('^GSPC')
githublink= 'https://github.com/Kowsi/SP500-Performance-Analysis'
pagetitle='S&P 500 Analysis'

button = list([
            dict(count=1, label="1m", step="month", stepmode="backward"),
            dict(count=6, label="6m", step="month", stepmode="backward"),
            dict(count=1, label="YTD", step="year", stepmode="todate"),
            dict(count=1, label="1y", step="year", stepmode="backward"),
            dict(step="all")
        ])

#Sector Performance detials 

def sector_performance_data():
    
    sector_df = web.get_sector_performance_av(api_key='ALPHAVANTAGE_API_KEY')

    for col in sector_df.columns:
        sector_df[col] = sector_df[col].str.rstrip('%').astype('float')/100
    sector_df.fillna(0, inplace=True)
    return sector_df

def get_stock_data():
    sp = pd.read_csv('SP_500/Characteristics.csv',index_col='Ticker')
    return sp


sp = get_stock_data()

def sector_performance_barchart(sector_df):
    
    sector_bar = []
    for col in SECTOR_PERFORMANCE_COLUMN:
        sector_bar.append(go.Bar(name=col, x=sector_df.index, y=sector_df[col]))
    return sector_bar

#Correlations
def correlation_heatmap(sector_df):
    
    corr_df= sector_df.T.corr()
    corr_df_heatmap = go.Heatmap(z=[corr_df[col].to_list() for col in corr_df.columns],type = 'heatmap',  x = corr_df.index, y=corr_df.columns, name='', showscale=False)
    #Greys,YlGnBu,Greens,YlOrRd,Bluered,RdBu,Reds,Blues,Picnic,Rainbow,Portland,Jet,Hot,Blackbody,Earth,Electric,Viridis,Cividis
    return corr_df_heatmap



    
def sector_count_barchart(sp):
    sector_count = sp.groupby(['Sector'])['Name'].count().to_frame('Count').sort_values('Count')
    sector_count_bar = go.Bar(x=sector_count.index, y=sector_count['Count'],text=sector_count['Count'],textposition='auto', marker_color='crimson', showlegend=False)
    return sector_count_bar




def get_sector_Performance_figure():
    global sp
    sector_df = sector_performance_data()
    sector_bar = sector_performance_barchart(sector_df)
    corr_df_heatmap = correlation_heatmap(sector_df)
    sector_count_bar = sector_count_barchart(sp)
    fig = make_subplots(
        rows=2, cols=2,
        column_widths=[0.4,0.3],
        row_heights=[0.6, 0.4],
        specs=[[{"colspan": 2}, None], [{}, {}]],
        subplot_titles=("Sector Performance","No. of Stocks in S&P 500", "Correlation Analysis"))

    for bar in sector_bar:
        fig.add_trace(bar, row=1, col=1)

    fig.add_trace(corr_df_heatmap, row=2, col=2)

    fig.add_trace(sector_count_bar, row=2, col=1)

    fig.update_layout(
        template="plotly_dark",
        height=1200, #width=1600,
        yaxis_title='Performance', xaxis_title='Sectors',xaxis_tickfont_size=11,
        yaxis2_title='No. of Stocks', xaxis2_title='Sectors'
        #showlegend=False
    )

    #fig.update_layout( title_text="specs examples")
    return fig


def get_stock_figure(value):
    global sp
    fig = go.Figure() 
    data = sp.groupby(['Sector']).get_group(value)
    
    trace_bar = go.Bar(x=data.index, y=data['Beta'], name='Beta')

    trace_line = go.Scatter(x=[data.index[0], data.index[-1]], y=[1,1], name='S&P 500')
    
    fig.add_traces(data=[trace_bar, trace_line])
    fig.layout.template='plotly_dark'
    fig.update_layout(title=value+' Sector', yaxis_title='Beta Value', xaxis_title='Stocks')
    return fig



def get_stock_data(ticker):
    #return ((1 + web.DataReader(ticker, 'yahoo', start, end)['Close'].pct_change().dropna().sort_index()).cumprod()-1).reset_index().rename({'Close':ticker},axis=1)
    return web.DataReader(ticker, 'yahoo', start, end)['Close'].reset_index().rename({'Close':ticker},axis=1)

def get_master_df(ticker):
    global master_df
    if master_df is None:
        master_df = get_stock_data(ticker)
        #master_df.set_index('Date', inplace=True)
    else:
        if ticker not in master_df:
            df = get_stock_data(ticker)
            master_df = pd.merge(master_df, df, on='Date')
    return master_df

def get_time_series_figure(value):
    global master_df, button
    plot = []
    if value==None or len(value)==0:
        return go.Figure(layout={'template':'plotly_dark'})
    
    for ticker in value:
        master_df = get_master_df(ticker)
        plot.append(go.Scatter(x=master_df['Date'], y=master_df[ticker], name=ticker))
                    
    fig = go.Figure(plot) 
    fig.update_xaxes(rangeslider=dict(visible=True, bgcolor='white'),rangeselector=dict(buttons=button, bgcolor='blue'))
    fig.layout.template='plotly_dark'
    fig.update_layout(yaxis_title='Price', xaxis_title='Time')
    return fig


#app = JupyterDash('SimpleExample')
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title=pagetitle

page_style = {'background-color':'black', 'color':'white', 'padding':'15px'}
tabs_colors={
        "border": "white",
        "primary": "black",
        "background": "black",
        'color':'black'
    }

sector_performance_div = html.Div([html.H2('Sector Performance Analysis'), dcc.Graph(figure=get_sector_Performance_figure())])

sector_div = html.Div([
    html.H2('Sector Report'),
    html.Div([
        dcc.Dropdown(
        id='sector-dropdown',
        options=[{'label': i,'value': i} for i in sector_list],
        value='Health Care', style={'color':'black'})], 
        style={'width': '45%','display': 'inline-block'}),
    html.Div(id='sector-analysis-container'),

])

#app = dash.Dash(__name__, )
stock_div = html.Div([
    html.H2('Time Series Chart'),
    html.Div([dcc.Dropdown(
        id='stock-dropdown',
        options=[{'label': i,'value': i} for i in ticker_list],
        #value='^GSPC', 
        multi=True,
        style={'color':'black'})],
    style={'width': '45%','display': 'inline-block'}),
    html.Div(id='close-stock-container'),
    html.Div(id='pct-stock-container')
])


app.layout = html.Div([
    html.H1('S&P 500'),
    dcc.Tabs(
        id="tabs-with-classes",
        value='tab-1',
        parent_className='custom-tabs',
        className='custom-tabs-container',
        children=[
            dcc.Tab(
                label='Sector',
                value='tab-1',
                className='custom-tab',
                selected_className='custom-tab--selected',
                children=sector_performance_div
            ),
            dcc.Tab(
                label='Stock',
                value='tab-2',
                className='custom-tab',
                selected_className='custom-tab--selected',
                children=[sector_div, stock_div]
            )
        ], style=tabs_colors),
    html.Div(id='tabs-content-classes'),
    html.A('Code on Github', href=githublink)], 
    style=page_style)


@app.callback(
    dash.dependencies.Output('sector-analysis-container', 'children'),
    [dash.dependencies.Input('sector-dropdown', 'value')])
def update_output(value):
    
    return [dcc.Graph(figure=get_stock_figure(value))]



@app.callback(
    dash.dependencies.Output('close-stock-container', 'children'),
    [dash.dependencies.Input('stock-dropdown', 'value')])
def update_output(value):
    
    return [dcc.Graph(figure=get_time_series_figure(value))]


if __name__ == '__main__':
    app.run_server()