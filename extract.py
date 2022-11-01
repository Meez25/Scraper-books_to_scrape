import requests
from bs4 import BeautifulSoup

r = requests.get("http://books.toscrape.com/catalogue/eragon-the-inheritance-cycle-1_153/index.html")

# Fix the encoding 
r.encoding = r.apparent_encoding

# Check that we receive the 200 status code
if r.status_code == 200:
    soup = BeautifulSoup(r.text, 'html.parser')

    book = {}
    
    # Get the data from the webpage using beautiful soup and requests
    product_page_url = r.url

    table = soup.find("table", attrs={'class':'table table-striped'})
    if table:
        rows = table.find_all("tr")
        for row in rows:
            field = row.find("th").text.strip()
            print(field)
            value = row.find("td").text.strip()
            print(value)

            if field == "UPC":
                book["universal_ product_code"] = value
            if field == "Price (excl. tax)":
                book["price_including_tax"] = value
            if field == "Price (incl. tax)":
                book["price_excluding_tax"] = value
            if field == "Availability":
                book["number_available"] = value

    print(book)

else:
    print("Request had an issue")