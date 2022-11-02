import requests
import re
from bs4 import BeautifulSoup
import csv
import time
from os.path import exists
import os
from threading import Thread


def main():
    timestamp = time.strftime("%Y%m%d-%H%M%S")

    r = requests.get("http://books.toscrape.com/")

    # Check that we receive the 200 status code
    if r.status_code == 200:
        # Fix the encoding
        r.encoding = r.apparent_encoding

        soup = BeautifulSoup(r.text, "html.parser")

        # Get all the links to all categories
        nav_list = soup.find_all(class_="nav nav-list")
        for html_category in nav_list:
            list_category_html = html_category.find_all("a", href=True)

            # Ignore the Book category
            list_category_html.pop(0)

            # Threading
            threads = []

            # Find the list of url and parse each of those
            for category in list_category_html:
                name_of_category = category.text.strip()

                # Replace the space by a "_" in the
                name_of_category = name_of_category.replace(" ", "_")
                url = r.url + category["href"]

                # Create threads
                t = Thread(
                    target=get_csv_from_category,
                    args=(url, timestamp, name_of_category),
                )
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

    else:
        print(f"{r.status_code} on URL {r.url}")


def get_csv_from_category(url, timestamp, name_of_category):

    # Get the time for the filename

    r = requests.get(url)

    # Check that we receive the 200 status code
    if r.status_code == 200:
        # Fix the encoding
        r.encoding = r.apparent_encoding

        soup = BeautifulSoup(r.text, "html.parser")

        # Getting all the link to books of the page
        image_containers = soup.find_all(
            "div", attrs={"class": "image_container"}
        )

        for image in image_containers:
            list_of_a = image.find_all("a", href=True)
            for url in list_of_a:

                # Reformate the URL to an absolute URL
                relative_path = re.search(
                    r"[0-9a-zA-Z].*", url["href"]
                ).group()
                absolute_url = (
                    "http://books.toscrape.com/catalogue/" + relative_path
                )

                get_csv_from_book_url(
                    absolute_url, timestamp, name_of_category
                )

        # Check if there are other pages
        if soup.find(class_="next"):
            next_url = soup.find(class_="next").find("a", href=True)["href"]
            first_part_of_url = re.search(r".*/", r.url).group()
            next_url = first_part_of_url + next_url

            get_csv_from_category(next_url, timestamp, name_of_category)

    else:
        print(f"{r.status_code} on URL {r.url}")


def get_csv_from_book_url(url, timestamp, name_of_category):

    r = requests.get(url)

    # Check that we receive the 200 status code
    if r.status_code == 200:

        # Fix the encoding
        r.encoding = r.apparent_encoding

        soup = BeautifulSoup(r.text, "html.parser")

        # Creating a book to store all the information
        book = {}

        # Getting the data from the webpage using beautiful soup and requests
        product_page_url = r.url

        # Getting the product main div
        product_main_info = soup.find(
            "div", attrs={"class": "col-sm-6 product_main"}
        )

        # Getting the title of the book
        title = product_main_info.find("h1").text.strip()

        # Getting the review rating and convert it to a real number
        review_rating_field = product_main_info.find(
            "p", attrs={"class": "star-rating"}
        )
        review_rating = convert_numeric_words_to_number(
            review_rating_field["class"][1].lower()
        )

        # Getting the image URL
        image_url = soup.find(class_="carousel").find("img")["src"]

        # Getting the product description
        if soup.find(class_="sub-header").find_next_sibling("p"):
            product_description = (
                soup.find(class_="sub-header")
                .find_next_sibling("p")
                .text.strip()
            )
        else:
            product_description = ""

        """Getting the category (should be the link before the name title)
        and removing the \n"""
        category = (
            soup.find(class_="breadcrumb")
            .find_all("li")[-2]
            .text.replace("\n", "")
        )

        # Getting the data from the table
        table = soup.find("table", attrs={"class": "table table-striped"})
        if table:
            rows = table.find_all("tr")
            for row in rows:
                field_of_table = row.find("th").text.strip()
                value_of_table = row.find("td").text.strip()

                if field_of_table == "UPC":
                    universal_product_code = value_of_table

                if field_of_table == "Price (excl. tax)":
                    price_including_tax = value_of_table

                if field_of_table == "Price (incl. tax)":
                    price_excluding_tax = value_of_table

                if field_of_table == "Availability":
                    """
                    Search for number in the string value_of_table
                    and assign it in the dic
                    """
                    if "In stock" in value_of_table:
                        number_available = re.search(
                            r"\d+", value_of_table
                        ).group()
                    else:
                        number_available = 0

        # Fill in the dict
        book["product_page_url"] = product_page_url
        book["universal_product_code"] = universal_product_code
        book["title"] = title
        book["price_including_tax"] = price_including_tax
        book["price_excluding_tax"] = price_excluding_tax
        book["number_available"] = number_available
        book["product_description"] = product_description
        book["category"] = category
        book["review_rating"] = review_rating
        book["image_url"] = image_url

        write_dict_to_csv(book, timestamp, name_of_category)
        download_image_from_url(
            image_url, name_of_category, universal_product_code, title
        )
        print(f'{book["title"]} from {book["category"]} category')

    else:
        print(f"{r.status_code} on URL {r.url}")


# Download image from Url and save it in /img
def download_image_from_url(
    image_url, name_of_category, universal_product_code, title
):

    name_of_category = name_of_category.replace(" ", "_")
    absolute_url = (
        "http://books.toscrape.com/"
        + re.search(r"[a-zA-Z].*", image_url).group()
    )
    print(absolute_url)
    img_data = requests.get(absolute_url).content
    path = "img/" + name_of_category + "/"
    isExist = exists(path)
    if not isExist:
        os.makedirs(path)
    with open(path + universal_product_code + ".jpg", "wb") as handler:
        # name_of_category + "/" + title[:10].strip() + "_"
        handler.write(img_data)


# Function to convert numeric words to number
def convert_numeric_words_to_number(star):
    help_dict = {
        "zero": "0",
        "one": "1",
        "two": "2",
        "three": "3",
        "four": "4",
        "five": "5",
    }
    return help_dict[star]


def write_dict_to_csv(book, timestamp, name_of_category):

    csv_header = [
        "product_page_url",
        "universal_product_code",
        "title",
        "price_including_tax",
        "price_excluding_tax",
        "number_available",
        "product_description",
        "category",
        "review_rating",
        "image_url",
    ]

    path = "output/"
    isExist = exists(path)
    if not isExist:
        os.makedirs(path)

    csv_file = (
        "output/Books_category_" + name_of_category + "_" + timestamp + ".csv"
    )

    # Write to file
    try:
        if not exists(csv_file):
            f_output = open(csv_file, "w")
            writer = csv.DictWriter(f_output, fieldnames=csv_header)
            writer.writeheader()
        else:
            f_output = open(csv_file, "a")
            writer = csv.DictWriter(f_output, fieldnames=csv_header)

        writer.writerow(book)
        f_output.close()
    except IOError:
        print("I/O error")


if __name__ == "__main__":
    main()
