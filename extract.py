import requests
import re
from bs4 import BeautifulSoup
import csv
import time
from os.path import exists
import os
from threading import Thread


def main():
    """Create threads to parse each category faster"""

    # Create a timestamp for the csv filename
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

                # Create and start threads
                t = Thread(
                    target=get_book_url_from_category,
                    args=(url, timestamp, name_of_category),
                )
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

    else:
        print(f"{r.status_code} on URL {r.url}")


def get_book_url_from_category(url, timestamp, name_of_category):
    """Get all the book url by visiting the category URL"""
    r = requests.get(url)

    # Check that we receive the 200 status code
    if r.status_code == 200:

        # Fix the encoding
        r.encoding = r.apparent_encoding

        soup = BeautifulSoup(r.text, "html.parser")

        # Getting all the link to the books of the page
        image_containers = soup.find_all(
            "div", attrs={"class": "image_container"}
        )

        for image in image_containers:
            list_of_a = image.find_all("a", href=True)
            for url in list_of_a:

                # Reformat the URL using regex
                relative_path = re.search(
                    r"[0-9a-zA-Z].*", url["href"]
                ).group()
                absolute_url = (
                    "http://books.toscrape.com/catalogue/" + relative_path
                )

                get_csv_from_book_url(
                    absolute_url, timestamp, name_of_category
                )

        # Check if there are other pages (next button)
        if soup.find(class_="next"):
            next_url = soup.find(class_="next").find("a", href=True)["href"]

            # Reformat URL
            first_part_of_url = re.search(r".*/", r.url).group()
            next_url = first_part_of_url + next_url

            # Recursive
            get_book_url_from_category(next_url, timestamp, name_of_category)

    else:
        print(f"{r.status_code} on URL {r.url}")


def get_csv_from_book_url(url, timestamp, name_of_category):
    """Create a dict by visiting an URL and extracting html data"""
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

        # Reformat the url
        absolute_url = (
            "http://books.toscrape.com/"
            + re.search(r"[a-zA-Z].*", image_url).group()
        )

        # Getting the product description otherwise empty string
        if soup.find(class_="sub-header").find_next_sibling("p"):
            product_description = (
                soup.find(class_="sub-header")
                .find_next_sibling("p")
                .text.strip()
            )
        else:
            product_description = ""

        """
        Getting the category (should be the link before the name title)
        and removing the \n
        """
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
                    and assign it in the dict
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
        book["image_url"] = absolute_url

        # Send the dict to the csv writer function
        write_dict_to_csv(book, timestamp, name_of_category)

        # Download the image from the url stored in the dict
        download_image_from_url(
            absolute_url, name_of_category, universal_product_code
        )

        print(f'{book["title"]} from the {book["category"]} category')

    else:
        print(f"{r.status_code} on URL {r.url}")


# Download image from Url and save it in /img
def download_image_from_url(
    absolute_url, name_of_category, universal_product_code
):
    """Download an image by using the requests module and save it"""

    # Reformat the name of category by replacing the space by "_"
    name_of_category = name_of_category.replace(" ", "_")

    # Get the bytes of the image
    img_data = requests.get(absolute_url).content

    # Check if the path exists, otherwise create it
    path = "img/" + name_of_category + "/"
    isExist = exists(path)
    if not isExist:
        os.makedirs(path)

    # Formatting of image filename
    filename = universal_product_code + ".jpg"

    try:
        with open(path + filename, "wb") as handler:
            handler.write(img_data)
    except Exception as err:
        print(
            f"Exception trying to write {filename} in {path}. Exception : "
            + err
        )


def convert_numeric_words_to_number(star):
    """Function to convert numeric words to number"""
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
    """From the received dict, write a CSV file"""

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

    # Check if path exists, otherwise create it
    path = "csv_files/"
    isExist = exists(path)
    if not isExist:
        os.makedirs(path)

    # Formatting of csv filename
    csv_file = (
        "csv_files/Books_category_"
        + name_of_category
        + "_"
        + timestamp
        + ".csv"
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
    except Exception as err:
        print(f"Exception happened trying to write {csv_file}" + err)


if __name__ == "__main__":
    main()
