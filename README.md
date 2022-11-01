# Scrapper-books_to_scrape

## Summary

This script will extract data from the website http://books.toscrape.com/ and generate several csv files containing information about those books.

- product_page_url  
- universal_product_code (upc)  
- title  
- price_including_tax  
- price_excluding_tax  
- number_available  
- product_description  
- category  
- review_rating 
- image_url

One csv file per category will be created, inside a folder named "output".

Images will also be saved in a folder named "img" and in the sub folder "category".

## Usage

To download all the library, you can do this command :
```shell
pip install -r requirements.txt
```

This will install all the dependancies necessary to run this script.