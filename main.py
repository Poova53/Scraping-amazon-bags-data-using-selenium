import os
import csv
import time
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class ScrapeAmazon:
    def __init__(self) -> None:
        self.open_chrome_driver()
        self.data = {}
    
    
    def open_chrome_driver(self):
        options = Options()
        service = Service(ChromeDriverManager().install())

        self.driver = webdriver.Chrome(options=options, service=service)
        self.driver.implicitly_wait(10)
        
        self.driver.get(r'https://www.amazon.in/s?k=bags&crid=2M096C61O4MLT&qid=1653308124&sprefix=ba%2Caps%2C283&ref=sr_pg_1')
        time.sleep(2)
        
    def scrape_pages(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        product_list = self.driver.find_elements(by=By.CSS_SELECTOR, value='div[data-component-type="s-search-result"]')

        for product in product_list:
            
            first_soup = BeautifulSoup(product.get_attribute("outerHTML").encode('cp850','replace').decode('cp850'), 'html.parser')
            self.part1_data(first_soup)
            
            self.navigate_to_product(product)
            second_soup = BeautifulSoup(self.driver.page_source, 'lxml')
            self.part2_data(second_soup)
            
            self.add_to_csv()
            
            self.close_product_tab()
            
        current_page = int(self.driver.find_element(By.CSS_SELECTOR, 'span[class="s-pagination-item s-pagination-selected"]').text.strip())
        
        if current_page < 20:
            self.driver.find_element(By.CSS_SELECTOR, 'a[class="s-pagination-item s-pagination-next s-pagination-button s-pagination-separator"]').click()
            time.sleep(2)
            
            print(f"moved to page no {current_page + 1}")
            self.scrape_pages()
        
            
    
    def part1_data(self, product):
        product_link_element = product.find('h2').find('a')
        self.data['product_url'] = "https://www.amazon.in" + product_link_element.get("href")
        self.data['product_name'] = product_link_element.text
        
        try:
            self.data['price'] = "Rs." +  product.find('span', {'class' : "a-offscreen"}).text.replace('?', '')
        except AttributeError:
            self.data['price'] = None
        
        try:
            self.data['rating'] = product.find('span', {'class' : "a-icon-alt"}).text
            self.data['no_of_reviews'] = product.find('span', {'class' : "a-size-base s-underline-text"}).text
        
        except AttributeError:
            self.data['rating'] = None
            self.data['no_of_reviews'] = None
            
    
    def part2_data(self, product):
        if product.find('div', {'class': 'brand-snapshot-card-container'}):
            self.data['manufacturer'] = product.find('div', {'class': 'brand-snapshot-card-container'}).find('span').text
            
        elif product.find('a', {'id': 'bylineInfo'}):
            self.data['manufacturer'] = product.find('a', {'id': 'bylineInfo'}).text.strip()
            
            if 'Visit' in self.data['manufacturer']:
                self.data['manufacturer'] = self.data['manufacturer'].replace('Visit the', '').replace('Store', '').strip()
                
            elif 'Brand' in self.data['manufacturer']:
                self.data['manufacturer'] = self.data['manufacturer'].replace('Brand:', '').strip()
                
        
        else:
            self.data['manufacturer'] = None
            
        self.data['description'] = product.find('span', {'id': 'productTitle'}).text.strip()
            
        self.data["ASIN"] = product.find('input', {'id': 'twister-plus-asin'}).get('value')
        
        try:
            self.data['product description'] = []
            bullet_list = product.find('div', {'id': 'feature-bullets'}).find('ul').find_all('li')
            
            for bullet in bullet_list:
                description = bullet.find('span').text.strip()
                self.data['product description'].append(description)
        
        except AttributeError:
            self.data['product description'] = None
            
        
        
    def navigate_to_product(self, product):
        product.find_element(By.TAG_NAME, 'h2').find_element(By.TAG_NAME, 'a').click()
        
        self.driver.switch_to.window(self.driver.window_handles[1]) # Switching the web driver to the new tab
        time.sleep(5)
        
    def close_product_tab(self):
        self.driver.close() # Closing the tab
        self.driver.switch_to.window(self.driver.window_handles[0]) # Switching to main tab
        time.sleep(2)
        
        
    def add_to_csv(self):
        file_name = 'Bags_data.csv'
        files = os.listdir() # Getting list of files in the directory

        # Setting field names for csv to add the data
        fieldnames = ['product_url', 'product_name', 'price', 'rating', 'no_of_reviews', 'manufacturer', 'ASIN', 'description', 'product description']

        # checking if file exist or not
        if file_name in files:
            with open(file_name, 'a', newline='', encoding='utf-8') as f:
                csv_dict_writer = csv.DictWriter(f, fieldnames=fieldnames)

                csv_dict_writer.writerow(self.data) # writing the data

        else:
            with open(file_name, 'w', newline='', encoding='utf-8') as f:
                csv_dict_writer = csv.DictWriter(f, fieldnames=fieldnames)

                csv_dict_writer.writeheader() # writing header
                csv_dict_writer.writerow(self.data)

        print("data successfully added to csv\n")
        self.data = {}      
            
            

if __name__ == "__main__":
    AmazonScraper = ScrapeAmazon()
    AmazonScraper.scrape_pages()
    with open("Bags_data.csv","r", encoding='utf-8') as f:
        reader = csv.reader(f,delimiter = ",")
        data = list(reader)
        print(len(data) - 1, 'bags product added')