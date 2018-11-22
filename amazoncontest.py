import os.path
import sys
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
from requests import get
import time
from random import randint


#Script the opens amazon, enters user information, and enters in every contest
def enter_contest(email, password, name):

    #Amazon user login information
    user_email = email
    user_password = password
    first_name= name

    #Pages to index to retrieve items
    page_count = 1
    url_list = []

    #Retrieves each giveaway page URL and inputs it into a list
    while page_count < 60:
        page_number = str(page_count)
        amazon_url = "https://www.amazon.com/ga/giveaways?pageId="+page_number
        url_list.append(amazon_url)
        page_count += 1

        #Wait some time between each page
        random_time = randint(1, 3)
        time.sleep(random_time)

    #All the URLS for each item
    item_urls_list = []

    #Goes to each Page URL and gathers all the prize URLs and puts them into the list item_urls_list
    for amazon_url in url_list:

        try:
            response = get(amazon_url)
            amazon_soup = BeautifulSoup(response.text, 'html.parser')
            type(amazon_soup)

            giveaway_container = amazon_soup.find("div", id='giveaway-grid')
            giveaway_list = giveaway_container.findChildren('div', class_='giveawayItemContainer')

            for items in giveaway_list:
                giveaway_items = items.find('a')['href']
                item_urls_list.append(giveaway_items)
        except:
            print ("Could not retrieve prizes from "+amazon_url)

        #Wait some time
        random_time = randint(1,3)
        time.sleep(3)

    #Print message that Firefox will be opening now
    print ("")
    print ("100% of data loaded, running script")
    print ("")

    #Individual item number, used to select the next item in the list
    item_number = 1

    #Runs through each item in the list
    for link in item_urls_list:

        #Open Firefox with the current url for the item
        try:
            options = Options()
            options.headless = True
            browser = webdriver.Firefox(options=options, executable_path=os.path.join(os.path.dirname(sys.argv[0]), 'geckodriver.exe'))
            browser.get((link))
            item_page_loaded = True
        except:
            item_page_loaded = False

        if item_page_loaded is True:
            #Wait some time
            random_time = randint(1,2)
            time.sleep(random_time)

            #Print the item number
            print ("Item #"+str(item_number))
            item_number += 1

            #Find Email and password boxes and log in to account and clicks the Sign in button
            try:
                login_email = browser.find_element_by_id('ap_email').send_keys(user_email)
                login_password = browser.find_element_by_id('ap_password').send_keys(user_password)
                #Wait some time
                random_time = randint(2,3)
                time.sleep(random_time)
                login_button = browser.find_element_by_id('signInSubmit').click()
            except:
                print ("Contest has ended")

            #Waits some time
            random_time = randint(1,2)
            time.sleep(random_time)

            #Find item name and price
            try:
                giveaway_item_name = browser.find_element_by_id("prize-name")
                giveaway_item_price = browser.find_element_by_class_name("qa-prize-cost-value")
                print (giveaway_item_name.text+"-" +giveaway_item_price.text)
            except:
                print ("Could not find item name")

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

                #Did not enter in the contest
                enter_contest = False

                try:
                    click_video = browser.find_element_by_id("airy-outer-container")
                    click_video.click()
                    print ("Waiting 15 seconds for amazon video")
                    #Wait some time
                    random_time = randint(16, 18)
                    time.sleep(random_time)
                    continue_button = browser.find_element_by_name('continue').click()
                except:
                    click_video = False
                    print ("Amazon video failed")

            elif youtube_video != False:

                #Did not enter in the contest
                enter_contest = False

                try:
                    print ("Waiting 15 seconds for youtube video")
                    #Wait some time
                    random_time = randint(16,18)
                    time.sleep(random_time)
                    continue_button = browser.find_element_by_name('continue').click()
                except:
                    print ("Youtube video script failed")
            else:
                try:
                    #Find animated contest box to click on
                    click_to_win = browser.find_element_by_id('box_click_target')
                except:
                    #Could not find the animated box
                    click_to_win = False

                if click_to_win != False:
                    print ("Entered the contest")
                    enter_contest = False
                    #Wait some time
                    random_time = randint(2,4)
                    time.sleep(random_time)
                    try:
                        click_to_win.click()
                    except:
                        print ("Could not click bouncing box")
                else:
                    print ("Already Entered")
                    enter_contest = True

            #Wait some time if item has not been played yet
            if enter_contest is False:

                #Wait some time
                random_time = randint(12, 15)
                time.sleep(random_time)

            else:
                #Wait some time
                random_time = randint(2,3)
                time.sleep(random_time)

            try:
                #Look for heading text telling you if you have won the prize or not
                did_you_win = browser.find_element_by_id('title')
                did_you_win = did_you_win.text
                did_you_win = did_you_win.lower()
            except:
                print ("Could not find winning status")

            #Check if you won the prize
            if did_you_win != first_name+", you didn't win":

                #Check to see if placed an entry into raffle, if not try to enter into contest
                if did_you_win == first_name+", your entry has been received":
                    print ("Already entered into raffle giveaway")
                else:
                    print ("You've won!")

                    try:
                        #Look for claim item button and click it
                        claim_prize = browser.find_element_by_name('ShipMyPrize')
                        claim_prize.click()
                    except:
                        #Tell user they won the prize
                        print ("You have already won this prize!")

                    random_time = randint(2,4)
                    time.sleep(random_time)
            else:
                print ('You did not win :/')

            #Close the window
            browser.quit()
        else:
            #Print error and close the browser
            print ("Could not load page")
            browser.quit()

        print ("")

    #Starts the script over once it completes the last item
    repeat_script(email, password, name)



#Restarts the script after it finishes
def repeat_script(email, password, name):
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
def load_login_info():
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
