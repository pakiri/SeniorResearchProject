import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from PIL import Image, UnidentifiedImageError
from wand.image import Image as IMG
import os
import time
import random

CHROMEDRIVER_PATH = "C:\\Program Files\\chromedriver-win64\\chromedriver.exe"

BASE_OUTPUT_DIR = "weekly_grocery_ads"
os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)

def is_valid_image(file_path):
    """Validate if the downloaded file is a valid image (non-SVG)."""
    try:
        with Image.open(file_path) as img:
            img.verify()  # verify image's integrity
        return True
    except (UnidentifiedImageError, IOError):
        return False

def convert_svg_to_png(svg_path, output_dir, index):
    """Convert an SVG file to PNG format."""
    try:
        png_path = os.path.join(output_dir, f"ad_image_{index}.png")

        with IMG(filename=svg_path, format="svg") as img:
            img.format = "png"
            img.save(filename=png_path)
            print(f"Converted SVG to PNG: {png_path}")

        # print(f"Converted SVG to PNG: {png_path}")
        os.remove(svg_path)  # remove the original SVG if conversion is successful
    except Exception as e:
        print(f"Failed to convert SVG: {svg_path} -> PNG. Error: {e}")

def download_image(image_url, output_dir, index):
    """Download and validate an image."""
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()

        # extract the file extension
        file_extension = os.path.splitext(image_url.split("?")[0])[1]
        if file_extension.lower() not in [".jpg", ".jpeg", ".png", ".gif", ".svg"]:
            print(f"Skipping non-image URL: {image_url}")
            return

        # saving the image
        output_path = os.path.join(output_dir, f"ad_image_{index}{file_extension}")

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

        # filter out smaller images (that probably aren't weekly ads)
        if os.path.getsize(output_path) < 100 * 1024: # less than 100 KB
            print(f"Image too small, deleting: {output_path}")
            os.remove(output_path)
            return

        # handle SVG files
        if file_extension.lower() == ".svg":
            convert_svg_to_png(output_path, output_dir, index)
        # validate and retain other image types
        elif not is_valid_image(output_path):
            print(f"Invalid image file, deleting: {output_path}")
            os.remove(output_path)
        else:
            print(f"Downloaded: {output_path}")
            time.sleep(random.uniform(2, 5))  # random delay between downloads

    except requests.RequestException as e:
        print(f"Error downloading image {image_url}: {e}")

# takes in store information and saves weekly ads in a directory corresponding to store ID
def scrape(store_id, url, zipcode="22312"):
    # # set up Selenium WebDriver
    # service = Service(CHROMEDRIVER_PATH)
    # driver = webdriver.Chrome(service=service)

    # set up Selenium WebDriver without opening a new browser
    service = Service(CHROMEDRIVER_PATH)
    # driver = webdriver.Chrome(service=service)
    option = webdriver.ChromeOptions()
    option.add_argument("headless")
    driver = webdriver.Chrome(service=service, options=option)

    try:
        # navigate to the website
        # driver.get("https://flipp.com/en-us/alexandria-va/weekly_ad/6950467-giant-food-weekly-circular?postal_code=22312")
        driver.get(url)
        
        output_folder = f"{BASE_OUTPUT_DIR}\\{store_id}"

        # check if the output folder exists
        if os.path.exists(output_folder):
            # delete all existing image files in the output folder
            print("Removing all existing files")
            for file_name in os.listdir(output_folder):
                file_path = os.path.join(output_folder, file_name)
                os.remove(file_path)
        else:
            # create the output folder
            os.makedirs(output_folder)

        if store_id == 1: # ALDI
            time.sleep(random.uniform(2, 5))
        
            button1 = driver.find_element(By.ID, "onetrust-accept-btn-handler")
            button1.click()
            
            time.sleep(0.5)

            driver.switch_to.frame(0)

            # time.sleep(1)

            for num in zipcode:
                time.sleep(random.uniform(0.25, 0.5))
                driver.find_element(By.XPATH, "//input[@id='locationInput']").send_keys(num)    

            button2 = driver.find_element(By.CSS_SELECTOR, ".svg-inline--fa")
            button2.click()

            time.sleep(random.uniform(1, 3))

            button3 = driver.find_element(By.XPATH, "//div[@id='StoreListContainer']/div/div[3]/button")
            button3.click()

            time.sleep(random.uniform(2, 6))
        else:
            time.sleep(random.uniform(4, 7))  # random delay

        # locate image elements
        image_elements = driver.find_elements(By.TAG_NAME, "img")

        # download images
        url_list = []

        for idx, img in enumerate(image_elements, start=1):
            src = img.get_attribute("src")
            # check if image has already been processed
            if src and src not in url_list:
                url_list.append(src)
                download_image(src, output_folder, idx)
                # time.sleep(random.uniform(2, 5))  # random delay between downloads

        # resetting list of image urls for next pull
        del url_list

    finally:
        driver.quit()

    print("All images processed.")
    return output_folder

if __name__ == "__main__":
    scrape(1, "https://www.aldi.us/weekly-specials/our-weekly-ads/")
    # scrape(2, "https://www.shoppersfood.com/flyers/3791d4b7-567c-43db-bed5-9a75a7a0cd80?store=2358")
    # scrape(3, "https://freshworld.us/weekly_special.phtml#&gid=1&pid=1")
