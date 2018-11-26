import os.path
import sys
import pickle
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
from requests import get
import time
from random import randint


#Script the opens amazon, enters user information, and enters in every contest
def skip_wait_time(email, password, name, want_follow):

    #Amazon user login information
    user_email = email
    user_password = password
    first_name= name

    #Pages to index to retrieve items, add giveaways urls list, loading percentage
    page_count = 1
    total_count = 1
    item_urls_list = []
    count_percentage = 100 / total_count

    #Goes to each Page URL and gathers all the prize URLs and puts them into the list item_urls_list
    while page_count <= total_count:
        #Page URL for giveaways
        amazon_url = "https://www.amazon.com/ga/giveaways?pageId="+str(page_count)

        #Load each prize url into the list to be used
        try:
            response = get(amazon_url)
            amazon_soup = BeautifulSoup(response.text, 'html.parser')
            type(amazon_soup)

            giveaway_container = amazon_soup.find("div", id='giveaway-grid')
            giveaway_list = giveaway_container.findChildren('div', class_='giveawayItemContainer')

            for items in giveaway_list:
                item_urls_list.append(items.find('a')['href'])
        except:
            print ("Could not retrieve prizes from "+amazon_url)

        #Show loading progress
        percentage_done_loading = int(round(page_count * count_percentage))

        if percentage_done_loading != 100:
            print (str(percentage_done_loading)+"% completed...", end='\r')
        else:
            print ("100% complete, now running script", end='\r')
            print ("")
            print ("")

        page_count += 1

        #Wait some time
        random_time = randint(1,3)
        time.sleep(random_time)

    #Check if user wants to follow to enter certain giveaways
    if want_follow == "yes" or want_follow == "y":
        want_follow = True
    else:
        want_follow = False

    #Individual item number, used to select the next item in the list
    item_number = 1

    #Runs through each giveaway item in item_urls_list
    for link in item_urls_list:

        #Open Firefox with the current url for the item
        try:
            options = Options()
            options.headless = False
            browser = webdriver.Firefox(executable_path=os.path.join(os.path.dirname(sys.argv[0]), 'geckodriver.exe'), options=options)
            browser.get((link))
            item_page_loaded = True
        except:
            item_page_loaded = False


        if item_page_loaded is True:
            #Wait some time
            random_time = randint(1,2)
            time.sleep(random_time)

            #Find Email and password boxes and log in to account and clicks the Sign in button
            try:
                login_email = browser.find_element_by_id('ap_email').send_keys(user_email)
                login_password = browser.find_element_by_id('ap_password').send_keys(user_password)
                #Wait some time
                random_time = randint(2,3)
                time.sleep(random_time)
                login_button = browser.find_element_by_id('signInSubmit').click()
                contest_ended = False
            except:
                contest_ended = True

            #Print the item number
            print ("Item #"+str(item_number))
            item_number += 1

            #Variable for sponsor follow giveaway and user does not want to enter
            is_follow_no_want = False

            #Find item name and price
            try:
                giveaway_item_name = browser.find_element_by_id("prize-name")
                giveaway_item_price = browser.find_element_by_class_name("qa-prize-cost-value")
                print (giveaway_item_name.text+"-" +giveaway_item_price.text)
            except:
                print ("Could not find item name")

            #Check if contest has ended, if not continue
            if contest_ended is False:
                #Looks for videos, follow sponsor button, or regualar giveaway box
                #Amazon video
                try:
                    amazon_video = browser.find_element_by_id("enter-video-button-announce")
                except:
                    amazon_video = False

                #Youtube video
                try:
                    youtube_video = browser.find_element_by_id("videoSubmitForm")
                except:
                    youtube_video = False

                #Sponsor follow button
                try:
                    follow_button = browser.find_element_by_name('follow')
                except:
                    follow_button = False

                #Standard animated giveaway box
                try:
                    #Find animated contest box to click on
                    click_to_win = browser.find_element_by_id('box_click_target')
                except:
                    #Could not find the animated box
                    click_to_win = False

                #Click video, follow button, or animated box if present
                if amazon_video != False:
                    #Did not enter in the contest yet
                    skip_wait_time = False

                    try:
                        click_video = browser.find_element_by_id("airy-outer-container")
                        click_video.click()
                        print ("Waiting 15 seconds for amazon video")
                        random_time = randint(16, 18)
                        time.sleep(random_time)
                        continue_button = browser.find_element_by_name('continue').click()
                        print ("Entered giveaway")
                    except:
                        print ("Amazon video failed")

                elif youtube_video != False:
                    #Did not enter in the contest yet
                    skip_wait_time = False

                    try:
                        print ("Waiting 15 seconds for youtube video")
                        #Wait some time
                        random_time = randint(16,18)
                        time.sleep(random_time)
                        continue_button = browser.find_element_by_name('continue').click()
                        print ("Entered giveaway")
                    except:
                        print ("Youtube video script failed")

                elif follow_button != False:
                    #Check if want_follow is true
                    if want_follow is True:
                        skip_wait_time = False
                        try:
                            follow_button.click()
                            print ("Followed the sponsor, Entered giveaway")
                        except:
                            print ("Could not follow sponsor")
                    else:
                        is_follow_no_want = True
                        skip_wait_time = True
                        print ("Is a sponsor follow giveaway, skipping")

                elif click_to_win != False:
                    time.sleep(2)
                    #Did not enter the contest yet
                    skip_wait_time = False
                    try:
                        click_to_win.click()
                        print ("Entered giveaway")
                    except:
                        print ("Could not click bouncing box")
                else:
                    print ("Previously entered")
                    skip_wait_time = True
                    random_time = randint(1,3)
                    time.sleep(random_time)

                #If entering giveaway and need time, wait
                if skip_wait_time is False:
                    #Wait some time
                    random_time = randint(12, 15)
                    time.sleep(random_time)

                #If not a sponsor follow and user does not want, look for giveaway text
                if is_follow_no_want is False:
                    try:
                        giveaway_results_text = browser.find_element_by_id('title')
                    except:
                        giveaway_results_text = False

                    #Check giveaway results and see if they are a winner
                    if giveaway_results_text != False:
                        #Convert to text and lowercase it
                        giveaway_results_text = giveaway_results_text.text
                        giveaway_results_text = giveaway_results_text.lower()

                        #Check if you already lost
                        if giveaway_results_text != first_name+", you didn't win":
                            #Check to see if placed an entry into raffle, if not try to claim prize
                            if giveaway_results_text != first_name+", your entry has been received":
                                try:
                                    #Look for claim item button and click it
                                    claim_prize = browser.find_element_by_name('ShipMyPrize')
                                except:
                                    claim_prize = False

                                #If not already claimed prize
                                if claim_prize != False:
                                    try:
                                        claim_prize.click()
                                        print ("***WINNER!***")
                                    except:
                                        print ("Could not claim prize")
                                        return
                                else:
                                    print ("You have already won this prize!")
                            else:
                                print ("Entered into raffle giveaway")
                        else:
                            print ('-Not a winner-')
                            random_time = randint(1,2)
                            time.sleep(random_time)
                    else:
                        print ("Could not find winning status")
                        time.sleep(1)
                browser.quit()
            else:
                print ("Contest has already ended")
                time.sleep(1)
            browser.quit()
        else:
            print ("Could not load page")
            time.sleep(1)
            browser.quit()

        print ("")

    #Starts the script over once it completes the last item
    repeat_script(email, password, name, want_follow)



#Restarts the script after it finishes
def repeat_script(email, password, name, want_follow):
    skip_wait_time(email, password, name, want_follow)


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
    want_follow = input("Do you want to enter follow sponsor contests? (Y/N): ")
    want_follow = want_follow.lower()

    #Asks user if information is correct
    correct_info = input("Is this information correct? (Y/N): ")
    correct_info = correct_info.lower()

    if correct_info == "yes" or correct_info == "y":

        print ("")
        print ("Loading prizes")

        #Run the script
        skip_wait_time(email, password, name, want_follow)
    else:
        print ("")
        load_login_info()


#Greeting message when first opened
print ("Welcome to the Amazon Giveaways Bot!")
print("")


#Checks if internet connection is avaliable
while check_connection() is False:
    #Tell user they need to have an internet connection before continuing
    print ("Failed to retrive internet connection, attempting to connect to network in 5 seconds", end='\r')
    time.sleep(5)
    check_connection()
else:
    print ("Connected!")
    print ("")
    load_login_info()
