from math import prod
import requests
from bs4 import BeautifulSoup

r = requests.get("http://books.toscrape.com/catalogue/eragon-the-inheritance-cycle-1_153/index.html")

# Fix the encoding 
r.encoding = r.apparent_encoding

# Check that we receive the 200 status code
if r.status_code == 200:
    soup = BeautifulSoup(r.text, 'html.parser')

    # Creating a book to store all the information
    book = {}
    
    # Getting the data from the webpage using beautiful soup and requests
    book["product_page_url"] = r.url

    # Getting the product main div
    product_main_info = soup.find("div", attrs={'class':'col-sm-6 product_main'})
    
    # Getting the title of the book
    title = product_main_info.find("h1").text.strip()
    book["title"] = title

    # Getting the review rating
    review_rating = product_main_info.find("p", attrs={'class':'star-rating'})
    book["review_rating"] = review_rating['class'][1]

    # Getting the image URL
    image_url = soup.find(class_="carousel").find("img")["src"]
    book["image_url"] = image_url
    
    # Getting the product description
    product_description = soup.find(class_="sub-header").find_next_sibling("p").text
    book["product_description"] = product_description

    # Getting the data from the table
    table = soup.find("table", attrs={'class':'table table-striped'})
    if table:
        rows = table.find_all("tr")
        for row in rows:
            field_of_table = row.find("th").text.strip()
            value_of_table = row.find("td").text.strip()
            

            if field_of_table == "UPC":
                book["universal_ product_code"] = value_of_table
            if field_of_table == "Price (excl. tax)":
                book["price_including_tax"] = value_of_table
            if field_of_table == "Price (incl. tax)":
                book["price_excluding_tax"] = value_of_table
            if field_of_table == "Availability":
                book["number_available"] = value_of_table

    print(book)

else:
    print("Request had an issue")