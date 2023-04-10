# for dash =============================================
from dash import Dash, Input, Output, dcc, html
import dash_bootstrap_components as dbc

# for web scraping =============================================
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions as ex
import time

# load dash =============================================
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define layout
app.layout = dbc.Container([
    html.H1('', style={'color': "dark-blue"}),
    html.H2('', style={'color': "dark-blue"}),
    dbc.Input(id='input', value='تایپ کنید', style={'text-align': 'right'}),
    dbc.Button('Search', id='search-button',
               color='primary', className='me-1'),
    html.Div(id='output')
])

# Define web scraping function
def scrape_website(search_term):
    url = f'https://www.digikala.com/search/?q={search_term}'
    driver = webdriver.Chrome()
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
    i = 1
    # Get the height of the entire page
    page_height = driver.execute_script("return document.body.scrollHeight;")
    screen_height = driver.execute_script("return window.screen.height;")
    if len(products) < 50:
        while True:
            # Scroll down the page to load more products
            driver.execute_script(f"window.scrollTo(0,{i*screen_height});")
            i += 1
            time.sleep(2)
            # Get the current position of the scrollbar
            current_position = driver.execute_script("return window.pageYOffset;")
    
            product_list = driver.find_element(
                By.XPATH, '//*[@id="ProductListPagesWrapper"]/section/div[2]')
            products = product_list.find_elements(
                By.CSS_SELECTOR, '.product-list_ProductList__item__LiiNI')
            if len(products) > 50 or current_position >= page_height - screen_height:
                time.sleep(2)
                break
    time.sleep(5)
    results = []
    i = 0
    for product in products:
        product = product.find_element(By.CSS_SELECTOR, 'div.d-flex.grow-1.pos-relative.flex-column')
        img = product.find_element(By.XPATH, './/img').get_attribute('src')
        h3 = product.find_element(By.XPATH, './/h3').text
        print(h3)
        try:
            price = product.find_element(By.CSS_SELECTOR, '.d-flex.ai-center.jc-end.gap-1.color-700.color-400.text-h5.grow-1').text
            results.append({'img': img,'title': h3, 'price': price})
        except ex.NoSuchElementException:
            # Ignore products without a price element
            continue
    driver.quit()
    return results

# Define callbacks


@app.callback(
    Output('output', 'children'),
    Input('search-button', 'n_clicks'),
    Input('input', 'value')
)
def on_search_button_click(n_clicks, search_term):
    if not n_clicks:
        return
    results = scrape_website(search_term)
    if not results:
        return html.Div('No results found.')
    products_html = []
    i = 1 
    for result in results[:50]:
        product_html = html.Div([
            html.H2(f"Number {i}"),
            html.Img(src=result['img']),
            html.H3(result['title']),
            html.Span(result['price'])
        ])
        i+=1
        products_html.append(product_html)
    return html.Div(products_html)


if __name__ == "__main__":
    app.run_server(port="8000")
