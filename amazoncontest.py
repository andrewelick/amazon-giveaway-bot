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
import sqlite3
import datetime
from imagetester import captcha_tester
import urllib.request
import getpass

#Script the opens amazon, enters user information, and enters in every contest
def amazon_bot(email, password, name, want_follow):

    print ("Loading prizes")

    try:
        #Go to website with all items in one table
        response = get("https://www.giveawaylisting.com/index2.html")
        amazon_soup = BeautifulSoup(response.text, 'lxml')
        type(amazon_soup)
        #Find table, and then all rows
        all_giveaways_table = amazon_soup.find('table', id='giveaways')
        all_giveaways_row = all_giveaways_table.findChildren('tr')
    except:
        print("Could not load items")
        print ("")
        amazon_bot(email, password, name, want_follow)

    #Pages to index to retrieve items, add giveaways urls list
    item_urls_list = {}
    item_count = 1
    total_count = len(all_giveaways_row)

    #Loop through each row and add item URL to dictionary
    for row in all_giveaways_row:
        try:
            row_sections = row.findAll('td') #All columns of that row
            price = row_sections[4].text[1:] #Price of item excluding the dollar sign
            link = row.find('a')['href'] #Link data
            item_urls_list[link] = float(price) #Adding to dictionary
        except:
            pass
        loading_percentage(item_count, total_count)
        item_count += 1

    print ("Removing prizes that you have already entered into")

    #Load enteredurls database and grab all the previously entered urls, delete old ones, and load into list
    database = sqlite3.connect('testdatabase.db', detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = database.cursor()
    #Create enteredurls table if not there
    try:
        cursor.execute('CREATE TABLE enteredurls (id INTEGER PRIMARY KEY, url TEXT, day date)')
    except:
        pass

    entered_urls_database = cursor.execute("SELECT * FROM enteredurls") #Find all rows in enteredurls table
    entered_urls = []

    for row in entered_urls_database:
        time_since = datetime.date.today() - row[2] #Compare date of url
        if time_since.days >= 7: #If url is older than a week delete it
            cursor.execute("DELETE FROM enteredurls WHERE url=?", (row[1],))
        else:
            entered_urls.append(row[1])
    #Save changes and close database connection
    database.commit()
    database.close()

    #Used for loading percentage when removing old giveaways
    item_count = 1
    total_count = len(entered_urls)

    #Remove urls that are in entered_urls from item_urls_list
    for url in entered_urls:
        if url in item_urls_list:
            del item_urls_list[url]
        #Show loading percentage
        loading_percentage(item_count, total_count)
        item_count += 1

    #If no prizes left wait 6 hours and check again
    if len(item_urls_list) < 100:
        time_count = 0
        time_wait = 21600

        while time_count < time_wait:
            time_message = time_wait - time_count
            time_count += 1
            print ("Entered into all the giveaways, will check again in "+str(time_message), end="\r")
            time.sleep(1)
        print ("Restarting...")
        print ("")
        #Restart the program
        amazon_bot(email, password, name, want_follow)
    else:
        print ("Entering in "+str(len(item_urls_list))+" new giveaways!")
        print ("")

        #Sort items from highest price down
        item_urls_list = sorted(item_urls_list, key=item_urls_list.get, reverse=True)

    #Item number
    item_number = 1

    #Runs through each giveaway item in item_urls_list
    for link in item_urls_list:
        #Open Firefox with the current url for the item
        try:
            options = Options()
            options.headless = True #Currently on, turn off if you notice multiple prizes that are unreadable in a row, CAPTCHA could be enabled
            profile = webdriver.FirefoxProfile('/Users/andye/AppData/Roaming/Mozilla/Firefox/Profiles/5ym8ukdl.amazon') #Add your own path, google create firefox profile
            browser = webdriver.Firefox(firefox_profile=profile, executable_path=os.path.join(os.path.dirname(sys.argv[0]), 'geckodriver.exe'), options=options)
            browser.get((link))
            item_page_loaded = True
        except:
            item_page_loaded = False

        #Run through the prize cycle if browser loads
        if item_page_loaded is True:
            #Variable for sponsor follow giveaway and user does not want to enter
            is_follow_no_want = False

            #Find Email and password boxes and log in to account and clicks the Sign in button
            try:
                login_email = browser.find_element_by_id('ap_email').send_keys(email)
                login_password = browser.find_element_by_id('ap_password').send_keys(password)
                random_time = randint(2,3)
                time.sleep(random_time)
                login_button = browser.find_element_by_id('signInSubmit').click()
                print ("Logged in")
            except:
                already_logged = True

            #Check if their is a captcha, save image, check text, and input results
            try:
                find_captcha = browser.find_element_by_id('image_captcha')
                captcha_image = find_captcha.find_element_by_tag_name("img")
            except:
                captcha_image = False

            if captcha_image != False:
                print ("Found captcha, testing")
                random_time = randint(1, 4)
                time.sleep(random_time)
                try:
                    captcha_src = captcha_image.get_attribute('src')
                    urllib.request.urlretrieve(captcha_src, "captcha.png")
                    captcha_results = captcha_tester()
                    captcha_input = browser.find_element_by_id('image_captcha_input').send_keys(captcha_results)
                    random_time = randint(3,6)
                    time.sleep(random_time)
                    submit_captcha = browser.find_element_by_class_name('a-button-input').click()
                    time.sleep(2)
                    try:
                        captcha_alert = browser.find_element_by_class_name('a-alert-content')
                        print ("Couldn't input correct captcha")
                    except:
                        captcha_alert = False
                        print ("Captcha was accepted!")

                except:
                    print ("Captcha tester failed")

            #Print the item number
            print ("Item #"+str(item_number))

            #Find item name and price
            try:
                giveaway_item_name = browser.find_element_by_id("prize-name").text
                giveaway_item_price = browser.find_element_by_class_name("qa-prize-cost-value").text
                print (giveaway_item_name+"-" +giveaway_item_price)
            except:
                print ("Could not find item name")

            #Check if contest has already ended
            try:
                contest_ended = browser.find_element_by_id('giveaway-ended-header')
            except:
                contest_ended = False

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
                        click_video = browser.find_element_by_id("airy-outer-container").click()
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

                #If entering giveaway and need time, wait
                if skip_wait_time is False:
                    random_time = randint(12, 15)
                    time.sleep(random_time)

                #If not a sponsor follow and user does not want, look for giveaway text
                if is_follow_no_want is False:
                    try:
                        giveaway_results_text = browser.find_element_by_id('title').text.lower()
                    except:
                        giveaway_results_text = False

                    #Check giveaway results and see if they are a winner
                    if giveaway_results_text != False:

                        #Check if you already lost
                        if giveaway_results_text != name+", you didn't win":
                            #Check to see if placed an entry into raffle, if not try to claim prize
                            if giveaway_results_text != name+", your entry has been received":
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
                    else:
                        print ("Could not find winning status")
            else:
                print ("Contest has already ended")
        else:
            print ("Could not load page")

        #Add link to enteredurls database if page loaded and found giveaway results
        if item_page_loaded is True:
            if contest_ended is True or giveaway_results_text != False:
                database = sqlite3.connect('testdatabase.db', detect_types=sqlite3.PARSE_DECLTYPES)
                cursor = database.cursor()
                cursor.execute('INSERT INTO enteredurls(url, day) VALUES(?, ?)', (link, datetime.date.today(), ))
                database.commit()
                database.close()

        #Wait some time before closing window
        random_time = randint(1,3)
        time.sleep(random_time)
        browser.quit()
        item_number += 1
        print ("")

    print ("End of prizes, restarting...")
    print ("")
    #Starts the script over once it completes the last item
    amazon_bot(email, password, name, want_follow)

#Loading percentage function
def loading_percentage(item_count, total_count):
    count_percentage = 100 / total_count
    percentage_done_loading = int(item_count * count_percentage)

    if percentage_done_loading < 100:
        print (str(percentage_done_loading)+"% completed...", end='\r')
    else:
        print ("100% complete", end='\r')
        print ("")
        print ("")

#Loads the user input questions, email, password, follow, correct info
def load_login_info():
    print ("Please enter in your Amazon account information to begin")
    email = input("Email: ")
    password = getpass.getpass('Password:')
    name = input("First Name: ")
    want_follow = input("Do you want to enter follow sponsor contests? (Y/N): ")
    correct_info = input("Is this information correct? (Y/N): ")

    #Handle user inputs
    name = name.lower()
    want_follow = want_follow.lower()
    correct_info = correct_info.lower()

    #Check if user wants to follow to enter certain giveaways
    if want_follow == "yes" or want_follow == "y":
        want_follow = True
    else:
        want_follow = False

    #If user info is correct start script, else load questions again
    if correct_info == "yes" or correct_info == "y":
        print ("")
        #Run the script
        amazon_bot(email, password, name, want_follow)
    else:
        print ("")
        load_login_info()

#Greeting message when first opened
print ("Welcome to the Amazon Giveaways Bot!")
print("")

load_login_info()
