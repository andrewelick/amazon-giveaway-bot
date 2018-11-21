import os.path
import sys
from tkinter import *
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
from requests import get
import time
from random import randint
import asyncio
import concurrent.futures

thread_count = 5

async def async_get_page_url(amazon_url):
    print (amazon_url)
    return_items = []
    try:
        response = get(amazon_url)
        amazon_soup = BeautifulSoup(response.text, 'html.parser')
        type(amazon_soup)

        giveaway_container = amazon_soup.find("div", id='giveaway-grid')
        giveaway_list = giveaway_container.findChildren('div', class_='giveawayItemContainer')

        for items in giveaway_list:
            giveaway_items = items.find('a')['href']
            return_items.append(giveaway_items)

        print(len(return_items))
        return return_items
    except:
        print ("Could not retrieve prizes from "+amazon_url)
        return return_items

async def gather_page_urls(url_list):

    #All the URLS for each item
    item_urls_list = []

    for amazon_url in url_list:
        item_urls_list.append(async_get_page_url(amazon_url))

    l = await asyncio.gather(*item_urls_list)
    return [item for sublist in l for item in sublist]

def write_to_log(txt):
    print(txt)
    with open('run_log', 'a') as f:
        f.write(txt + '\n')

def run(item_number, link, user_email, user_password, first_name):
    #Print the item number
    output_string = "\n"
    output_string += "Item #"+str(item_number)+": "+link
    item_number += 1

    #Open Firefox with the current url for the item
    try:
        options = Options()
        options.headless = True
        browser = webdriver.Firefox(options=options, executable_path=os.path.join(os.path.dirname('/Users/mdobro/Code/amazon-giveaway-bot/'), 'geckodriver'))
        browser.get((link))
    except:
        output_string += "\n" + "Could not load page"
        browser.quit()
        write_to_log ( output_string )
        return

    #Wait some time
    random_time = randint(1,3)
    time.sleep(random_time)

    #Find Email and password boxes and log in to account and clicks the Sign in button
    try:
        login_email = browser.find_element_by_id('ap_email').send_keys(user_email)
        login_password = browser.find_element_by_id('ap_password').send_keys(user_password)
        #Wait some time
        random_time = randint(2,3)
        time.sleep(random_time)
        login_button = browser.find_element_by_id('signInSubmit').click()
    except:
        output_string += "\n" + "Contest has ended, continuing onward"
        browser.quit()
        write_to_log (output_string)
        return


    #Waits some time
    random_time = randint(1,3)
    time.sleep(random_time)

    #Looks for videos on page, waits time if videos, clicks prize box
    #Find Amazon video on page
    try:
        amazon_video = browser.find_element_by_id("enter-video-button-announce")
    except:
        amazon_video = False

    #Find Youtube video on page
    try:
        youtube_video = browser.find_element_by_id("videoSubmitForm")
    except:
        youtube_video = False

    #If video is on the page either click the video and wait or just wait, else, click the giveaway box
    if amazon_video != False:
        try:
            click_video = browser.find_element_by_id("airy-outer-container")
            click_video.click()
            output_string += "\n" + "Waiting 15 seconds for amazon video"
            #Wait some time
            random_time = randint(16, 18)
            time.sleep(random_time)
            continue_button = browser.find_element_by_name('continue').click()
        except:
            click_video = False
            output_string += "\n" + "Amazon video failed"
            browser.quit()
            write_to_log (output_string)
            return

    elif youtube_video != False:
        try:
            output_string += "\n" + "Waiting 15 seconds for youtube video"
            #Wait some time
            random_time = randint(16,18)
            time.sleep(random_time)
            continue_button = browser.find_element_by_name('continue').click()
        except:
            output_string += "\n" + "Youtube video script failed"
            browser.quit()
            write_to_log (output_string)
            return
    else:
        try:
            click_to_win = browser.find_element_by_id('box_click_target')
        except:
            click_to_win = False

        if click_to_win != False:
            output_string += "\n" + "Entering contest..."
            #Wait some time
            random_time = randint(2,4)
            time.sleep(random_time)
            click_to_win.click()
        else:
            output_string += "\n" + "Already Entered"
            browser.quit()
            write_to_log (output_string)
            return

    #Wait some time
    random_time = randint(14, 15)
    time.sleep(random_time)

    did_you_win = ""
    try:
        did_you_win = browser.find_element_by_id('title')
        did_you_win = did_you_win.text
        did_you_win = did_you_win.lower()
    except:
        output_string += "\n" + "Could not find winning status"

    #Check if you won the prize
    if did_you_win == first_name+", you won!":
        output_string += "\n" + "******** You've won! ********"
        try:
            claim_prize = browser.find_element_by_name('ShipMyPrize')
            claim_prize.click()
        except:
            console.log('Error finding ship button')

        random_time = randint(2,4)
        time.sleep(random_time)
    elif did_you_win == first_name+", your entry has been received":
        output_string += "\n" + 'This contest will select a winner later. If you won, you will notified via email.'
    else:
        output_string += "\n" + 'You did not win :/'
        #Close the firefox window

    browser.quit()
    write_to_log (output_string)

#Script the opens amazon, enters user information, and enters in every contest
async def enter_contest(email, password, name):

    #Amazon user login information
    user_email = email
    user_password = password
    first_name= name

    #Pages to index to retrieve items
    page_count = 1
    url_list = []

    #Retrieves each page URL up to the page_count
    while page_count < 30:
        page_number = str(page_count)
        amazon_url = "https://www.amazon.com/ga/giveaways?pageId="+page_number
        url_list.append(amazon_url)
        page_count += 1

    #Goes to each Page URL and gathers all the prize URLs and puts them into the list item_urls_list
    item_urls_list = await gather_page_urls(url_list)
    print (len(item_urls_list))

    #Print message that Firefox will be opening now
    print ("")
    print ("100% of data loaded, running script")

    if item_urls_list == "":
        enter_contest(email, password, name)

    executor = concurrent.futures.ProcessPoolExecutor(thread_count)
    
    futures = []
    for index, link in enumerate(item_urls_list):
        #Wait some time
        random_time = randint(2,3)
        time.sleep(random_time)
        futures.append(executor.submit(run, index, link, user_email, user_password, first_name))
    concurrent.futures.wait(futures)

    #Starts the script over once it completes the last item
    repeat_script(user_email, user_password, first_name)


#Restarts the script after it finishes
def repeat_script(user_email, user_password, first_name):
    email = user_email
    password = user_password
    name = first_name

    enter_contest(email, password, name)



#Check for internet connection
def check_connection():
    print ("Checking connection...")

    test_url = "http://www.google.com"
    timeout = 5
    try:
        #Ping the URL and tell user connected
        response = get(test_url, timeout=timeout)

    except:
        return False



#Loads the email and password questions
async def load_login_info():
    print ("Please enter in your Amazon account information to begin")
    email = input("Email: ")
    password = input("Password: ")
    name = input("First Name: ")
    name = name.lower()

    #Asks user if information is correct
    correct_info = input("Is this information correct? Yes or No: ")
    correct_info = correct_info.lower()

    if correct_info == "yes":
            #Running text
            print ("Loading script data, may take up to 10 minutes. Sit back and enjoy the prizes!")
            #Run the script
            await enter_contest(email, password, name)
    else:
        print ("")
        load_login_info()


#Greeting message when first opened
print ("Welcome to the Amazon Giveaways Bot!")
print("")


#Checks if internet connection is avaliable
while check_connection() is False:
    #Tell user they need to have an internet connection before continuing
    print ("Failed to retrive internet connection, attempting to connect to network in 5 seconds")
    time.sleep(5)
    check_connection()
else:
    print ("Connected!")
    print ("")
    asyncio.run(load_login_info())
