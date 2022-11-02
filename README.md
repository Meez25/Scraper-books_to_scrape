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

Clone the repository on your system, for example in ~/scrapper

You then go in the folder using the command line

To download all the library, you can do this command :
```shell
pip install -r requirements.txt
```

This will install all the dependancies necessary to run this script.

Then type 
```shell
python3 extract.py
```

You may need to use python instead of python3 depending on your system.

Et voila ! Now you should have 2 directory, one "img" and one "csv_files".

"csv_files" contains 50 csv files. One per category. In each of those, you will find a list of the books.
"img" contains all 50 categories and inside you will find the files named such as "universal_product_code.jpg"
