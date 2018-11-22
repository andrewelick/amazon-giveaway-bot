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
import concurrent.futures
import pickle

USED_URL_FILE_NAME='entered_giveaways'

loading_thread_count = 5
thread_count = 5
max_page_count = 1
current_page_number = 0
rescan_same_pages_on_completion = False

def get_intersection(first_list, second_list):
    in_first = set(first_list)
    in_second = set(second_list)

    in_second_but_not_in_first = in_second - in_first

    return first_list + list(in_second_but_not_in_first)

def remove_second_list_from_first(first_list, second_list):
    in_first = set(first_list)
    in_second = set(second_list)

    return in_first - in_second

def async_get_page_url(amazon_url):
    #Waits some time
    random_time = randint(0, 1)
    time.sleep(random_time)
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
        print ("Successful retrieved items from "+amazon_url)
        return return_items
    except Exception as e:
        print ( e )
        print (response.value)
        print ("Could not retrieve prizes from "+amazon_url)
        return return_items

def gather_page_urls(url_list):
    #All the URLS for each item
    item_urls_list = []

    print ("\nLoading script data...")

    executor = concurrent.futures.ThreadPoolExecutor(loading_thread_count)
    
    futures = []
    for amazon_url in url_list:
        future = executor.submit(async_get_page_url, amazon_url)
        futures.append(future)
    concurrent.futures.wait(futures)
    item_urls_list = [future.result() for future in futures]
    # future.result() returns an array, list needs to be flattened
    flat_item_urls_list = [item for sublist in item_urls_list for item in sublist]
    # remove saved used_urls and return list
    filtered_list = []
    with open(USED_URL_FILE_NAME, 'rb') as used_urls_file:
        all_used_urls = pickle.load(used_urls_file)
        print(all_used_urls)
        filtered_list = remove_second_list_from_first(flat_item_urls_list, all_used_urls)
        used_urls_file.close()
    return filtered_list

def write_to_log(txt):
    print(txt)
    with open('run_log', 'a') as f:
        f.write(txt + '\n')

def write_to_entered_giveaways(url):
    #Write all used urls to disk
    print("writing to entered_giveaways")
    all_used_urls = []
    all_used_urls = get_intersection([url], pickle.load(open(USED_URL_FILE_NAME, 'rb')))
    pickle.dump(all_used_urls, open(USED_URL_FILE_NAME, 'wb'))
    print(pickle.load(open(USED_URL_FILE_NAME, 'rb')))

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
        write_to_entered_giveaways(link)
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
        write_to_entered_giveaways(link)
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
            write_to_entered_giveaways(link)
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
            write_to_entered_giveaways(link)
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
            write_to_entered_giveaways(link)
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
    write_to_entered_giveaways(link)

#Script the opens amazon, enters user information, and enters in every contest
def enter_contest(email, password, name):

    #Amazon user login information
    user_email = email
    user_password = password
    first_name= name

    #Pages to index to retrieve items
    page_count = 1
    url_list = []

    global current_page_number
    if (rescan_same_pages_on_completion):
        current_page_number = 0

    #Retrieves each page URL up to the page_count
    while page_count <= max_page_count:
        page_number = str(current_page_number+page_count)
        amazon_url = "https://www.amazon.com/ga/giveaways?pageId="+page_number
        url_list.append(amazon_url)
        page_count += 1
    current_page_number += page_count

    #Goes to each Page URL and gathers all the prize URLs and puts them into the list item_urls_list
    item_urls_list = gather_page_urls(url_list)
    print ("Items to check: "+str(len(item_urls_list)))

    print("Done! Sit back and enjoy the prizes!")

    if item_urls_list == "":
        enter_contest(email, password, name)

    executor = concurrent.futures.ProcessPoolExecutor(thread_count)
    
    futures = []
    used_urls = []
    for index, link in enumerate(item_urls_list):
        #Wait some time
        random_time = randint(2,3) #TODO: make sleep into a function
        time.sleep(random_time) 
        runFuture = executor.submit(run, index, link, user_email, user_password, first_name)
        futures.append(runFuture)
        used_urls.append(runFuture.result())
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



#Loads the email and password questionsdef load_login_info():
    print ("Please enter in your Amazon account information to begin")
    email = input("Email: ")
    password = input("Password: ")
    name = input("First Name: ")
    name = name.lower()

    #Asks user if information is correct
    correct_info = input("Is this information correct? Yes or No: ")
    correct_info = correct_info.lower()

    if correct_info == "yes":
            #Run the script
            enter_contest(email, password, name)
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
    load_login_info()
