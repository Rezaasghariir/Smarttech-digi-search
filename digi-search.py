# for dash =====================================================
from dash import Dash, Input, Output, dcc, html
import dash_bootstrap_components as dbc

# for plotting =================================================
import plotly.graph_objects as go
# for web scraping =============================================
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions as ex
from selenium.webdriver.chrome.options import Options
import time
# for image downloading=========================================
import shutil
import os
import requests
# number of item you want
item_requsted_cnt = 50
# load dash ====================================================

app = Dash(__name__, external_stylesheets=[
           dbc.themes.DARKLY, 'https://fonts.cdnfonts.com/css/iranian-sans'])

# Define layout ================================================
app.title = "Digi-Search"
app.layout = dbc.Container([
    html.H1('بررسی قیمت کالا در دی جی کالا', style={
            'color': "dark-blue", "font-size": "20px"}, className="mx-auto mt-4"),
    # html.H2('', style={'color': "dark-blue"}),
    dbc.Input(id='input', value='نام محصول را تایپ کنید', style={
              'text-align': 'right'}, className="mx-auto mt-2 mb-4"),
    dbc.Button('جستجو در دی جی کالا', id='search-button',
               color='primary', className="d-grid gap-2 mx-auto col-6 mb-4"),
    dcc.Loading(id='loading' , children=[html.Div(id='loadingDiv')], type='circle' ,className="mt-4"),
    html.Div(id='output')
], style={"direction": "rtl", "font-family": "Iranian Sans"},)

# Make Directory ====================================================
def reMakeDir(path):
    # removing images folder
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
        except OSError as e:
            print("Error: %s : %s" % (path, e.strerror))
            return
    os.mkdir(path)

# Make Plot ====================================================
def make_plot(results):
    # Create the plotly trace
    prices = [float(item['price'].replace(',', '')) for item in results]
    title = [item['title']  + '\nقیمت:' + item['price'] for item in results]
    trace = go.Scatter(
        x=list(range(1, len(results)+1)),
        y=prices,
        mode='lines',
        name='Data',
        hoverinfo='text',
    )
    trace.text = title
    # Create the layout
    layout = go.Layout(
        title='نمودار قیمت',
        template='plotly_dark'
    )
    # Create the figure object
    fig = go.Figure(data=[trace], layout=layout)
    return dcc.Graph(id='plot', figure=fig)


# Make Table ============================================
def make_table(results):

    global item_requsted_cnt
    
    table_header = [
        html.Thead(html.Tr([html.Th("شماره"), html.Th(
            "نام"), html.Th("قیمت"), html.Th("عکس")]), className="table-warning")
    ]
    
    rows = []
    for i, result in enumerate(results[:item_requsted_cnt]):
        row_class = ""
        if (i + 1) % 2 == 0:
            # if the row number is even, set the class to "table-success"
            row_class = "table-info"
        else:
            # if the row number is odd, set the class to "table-info"
            row_class = "table-secondary"
        row = html.Tr([html.Td(f"{i+1}"), html.Td(result['title']), html.Td(result['price']), html.Td(html.Div(
            [html.Img(src=result['img'], width='30px', height='30px', id=f"component-target-{i+1}"), dbc.Popover(
                [
                    dbc.PopoverBody(
                        html.Img(src=result['img'],
                                 alt=result['title'])
                    ),
                ],
                target=f"component-target-{i+1}",
                trigger="hover",
            )]))], className=row_class)

        rows.append(row)
    table_body = [html.Tbody(rows)]

    table = dbc.Table(table_header + table_body,
                      bordered=True,
                      hover=True,
                      responsive=True,
                      striped=True,)
    return table


# Define web scraping function ==========================
def scrape_website(search_term):

    global img_folder_path,item_requsted_cnt
    
    url = f'https://www.digikala.com/search/?q={search_term}'

    
    #for when you dont want  open chrome browser 
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(options=chrome_options)
    
    # uncomment for open chrome and show whats happend
    # driver = webdriver.Chrome()
    
    driver.get(url)
    time.sleep(3)

    # Wait for the product list to become visible
    product_list = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located(
            (By.CLASS_NAME, "product-list_ProductList__pagesContainer__zAhrX"))
    )

    product_list = driver.find_element(
        By.XPATH, '//*[@id="ProductListPagesWrapper"]/section/div[2]')
    products = product_list.find_elements(
        By.CSS_SELECTOR, '.product-list_ProductList__item__LiiNI')
    
    scroll_count = 1
    # Get the height of the entire page
    screen_height = driver.execute_script("return window.screen.height;")

    #need for load complatly page after scroll end
    loop_numebr = 0
    befor_product_len = 0
    if len(products) < item_requsted_cnt:
        while True:
            # Scroll down the page to load more products
            driver.execute_script(f"window.scrollTo(0,{scroll_count*screen_height});")

            scroll_count += 1
            
            product_list = driver.find_element(
                By.XPATH, '//*[@id="ProductListPagesWrapper"]/section/div[2]')
            products = product_list.find_elements(
                By.CSS_SELECTOR, '.product-list_ProductList__item__LiiNI')
            
            time.sleep(1)
            if len(products) > item_requsted_cnt or len(products) == befor_product_len:
                if (loop_numebr <= 20 and len(products) < item_requsted_cnt):
                    loop_numebr += 1
                else:
                    break
            befor_product_len = len(products)

    time.sleep(2)
    results = []
    # declaring index for image counter
    image_counter = 0
    # making directory needed
    image_path = "search_file/"+ search_term
    reMakeDir("search_file")
    reMakeDir(image_path)
    # add for saving data
    file_data = ""
    for product in products[:item_requsted_cnt]:
        product = product.find_element(
            By.CSS_SELECTOR, 'div.d-flex.grow-1.pos-relative.flex-column')
        img = product.find_element(By.XPATH, './/img').get_attribute('src')

        h3 = product.find_element(By.XPATH, './/h3').text
        try:
            price = product.find_element(
                By.CSS_SELECTOR, '.d-flex.ai-center.jc-end.gap-1.color-700.color-400.text-h5.grow-1').text
            results.append({'img': img, 'title': h3, 'price': price})
#Saving Data ================================================================
            img_data = requests.get(img).content
            image_counter += 1
            with open(f'{image_path}/{search_term}-{image_counter}.jpg', 'wb') as handler:
                handler.write(img_data)
            line_length = 150
            tempLen = "قیمت : "+ price +  h3 +"\n"
            tempLen.encode("utf-8")
            file_data +=  h3 +"  "+"-"*(line_length-len(tempLen))+ ">  قیمت : "+price+"\n"
        except ex.NoSuchElementException:
            # Ignore products without a price element
            continue
    # check product avilable
    if len(file_data)>5:
        with open(f'{image_path}/{search_term}.txt', 'w',encoding='utf-8') as handler:
            handler.write(file_data)

    driver.quit()
    return results

# Define callbacks


@ app.callback(
    Output('output', 'children'),
    # for showing loading
    Output('loading', 'children')
    ,[
    Input('search-button', 'n_clicks'),
    Input('input', 'value')
    ]
)
def on_search_button_click(n_clicks, search_term):
    if not n_clicks:
        return "",""
    
    results = scrape_website(search_term)
    if not results:
        return html.Div('No results found.'),""
    
    print(f"Length of resualt is {len(results)}")
    
    table = make_table(results)
    
    plot = make_plot(results)
    
    hit = dbc.Label('برای دیدن عکس ها در سایز بزرگ نشانگر را بر روی آنها قرار دهید.')
    tabs = dbc.Tabs(
        [
            dbc.Tab(html.Div([hit,table]), label="جدول"),
            dbc.Tab(plot, label="نمودار قیمت"),
        ]
    )

    # print("end of callback")
    n_clicks = None
    return html.Div([tabs]),""


if __name__ == "__main__":
    app.run_server(port="8000")
