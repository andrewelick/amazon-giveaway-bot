from myimports import os
from myimports import sys
from myimports import time
from myimports import datetime
from myimports import random
from myimports import webdriver
from myimports import Keys
from myimports import Select
from myimports import Options
from myimports import get
from myimports import put
from myimports import post
from myimports import BeautifulSoup
from myimports import sqlite3
from myimports import getpass
import captchachecker
import localhandler


#Script the opens amazon, enters user information, and enters in every contest
def amazon_bot(email, password, name, want_follow, firefox_profile_path, amazon_pass):

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
        time.sleep(5)
        amazon_bot(email, password, name, want_follow, firefox_profile_path, amazon_pass)

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
    local_database = sqlite3.connect('localdatabase.db', detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = local_database.cursor()

    entered_urls_database = cursor.execute("SELECT * FROM enteredurls") #Find all rows in enteredurls table
    entered_urls_database_loop = cursor.fetchall()
    entered_urls = []

    for row in entered_urls_database_loop:
        time_since = datetime.date.today() - row[2] #Compare date of url
        if time_since.days >= 10: #If url is older than a week delete it
            cursor.execute("DELETE FROM enteredurls WHERE url=?", (row[1],))
        else:
            entered_urls.append(row[1])
    #Save changes and close database connection
    local_database.commit()
    local_database.close()

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
        amazon_bot(email, password, name, want_follow, firefox_profile_path, amazon_pass)
    else:
        print ("Entering in "+str(len(item_urls_list))+" new giveaways!")
        print ("")

        #Sort items from highest price down
        item_urls_list = sorted(item_urls_list, key=item_urls_list.get, reverse=True) #reverse=True makes it start from highest to lowest

    #Item number
    item_number = 1

    #Runs through each giveaway item in item_urls_list
    for link in item_urls_list:
        #Open Firefox with the current url for the item
        try:
            options = Options()
            options.headless = True #Currently on, turn off if you notice multiple prizes that are unreadable in a row, CAPTCHA could be enabled
            profile = webdriver.FirefoxProfile(firefox_profile_path) #Add your own path, google create firefox profile
            profile.set_preference("media.volume_scale", "0.0") #Mutes sound coming videos
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
                browser.find_element_by_id('ap_email').send_keys(email)
                browser.find_element_by_id('ap_password').send_keys(amazon_pass)
                time.sleep(random.randint(2,3))
                login_button = browser.find_element_by_id('signInSubmit').click()
                print ("Logged in")
            except:
                already_logged = True

            #Run captcha test, check for captcha and solve it
            captchachecker.check_for_captcha(browser)

            #Print the item number
            print ("Item #"+str(item_number))

            #Find item name and price
            try:
                giveaway_item_name = browser.find_element_by_id("prize-name").text
                giveaway_item_price = browser.find_element_by_class_name("qa-prize-cost-value").text
                print (giveaway_item_name+"-" +giveaway_item_price)
            except:
                print ("Could not find item name")

            time.sleep(random.randint(2,5))

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
                                try:
                                    claim_kindle_book = browser.find_element_by_name("ClaimMyPrize")
                                except:
                                    claim_kindle_book = False

                #Click video, follow button, or animated box if present
                if amazon_video != False:
                    #Did not enter in the contest yet
                    skip_wait_time = False

                    try:
                        click_video = browser.find_element_by_id("airy-outer-container").click()
                        print ("Waiting 15 seconds for amazon video")
                        time.sleep(random.randint(16,18))
                        browser.find_element_by_name('continue').click()
                        print ("Entered giveaway")
                    except:
                        print ("Amazon video failed")

                elif youtube_video != False:
                    #Did not enter in the contest yet
                    skip_wait_time = False

                    try:
                        print ("Waiting 15 seconds for youtube video")
                        time.sleep(random.randint(16,18))
                        browser.find_element_by_name('continue').click()
                        print ("Entered giveaway")
                    except:
                        print ("Youtube video script failed")

                elif follow_button != False:
                    #Check if want_follow is true
                    if want_follow == 1:
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
                elif claim_kindle_book != False:
                    try:
                        claim_kindle_book.click()
                        claim_kindle_book = True
                    except:
                        print ("Could not claim free kindle book")
                    skip_wait_time = True

                else:
                    print ("Previously entered")
                    skip_wait_time = True

                #If entering giveaway and need time, wait
                if skip_wait_time is False:
                    time.sleep(random.randint(12,15))

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
                                #Check if amazon changed the prize collection page
                                browser.get_screenshot_as_file('pics/'+str(item_number)+'.png')
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
                                        #Update the win column in stats table
                                        post("http://www.primegiveaway.com/add_winning_prize", data={'email':email,'giveaway_item_name':giveaway_item_name,'giveaway_item_price':giveaway_item_price,'link':link})
                                        #Update winning stats
                                        post("http://www.primegiveaway.com/update_wins_stats", data={'email':email})
                                    except:
                                        print ("Could not claim prize")
                                        return
                                else:
                                    #If free kindle book tell user
                                    if claim_kindle_book is True:
                                        print ("You claimed a kindle book!")
                                        #Update the win column in stats table
                                        post("http://www.primegiveaway.com/add_winning_prize", data={'email':email,'giveaway_item_name':giveaway_item_name,'giveaway_item_price':giveaway_item_price,'link':link})
                                        #Update winning stats
                                        post("http://www.primegiveaway.com/update_wins_stats", data={'email':email})
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
                database = sqlite3.connect('localdatabase.db', detect_types=sqlite3.PARSE_DECLTYPES)
                cursor = database.cursor()
                cursor.execute('INSERT INTO enteredurls(url, day) VALUES(?, ?)', (link, datetime.date.today(), ))
                database.commit()
                database.close()

        #Wait some time before closing window
        browser.quit()
        time.sleep(random.randint(1,3))
        item_number += 1
        print ("")

    print ("End of prizes, restarting...")
    print ("")

    #Update entries stats
    #Open and find last entry count in enteredurls table from local database
    local_database = sqlite3.connect('localdatabase.db', detect_types=sqlite3.PARSE_DECLTYPES)
    local_cursor = local_database.cursor()
    local_cursor.execute("""SELECT * FROM enteredurls ORDER BY id DESC LIMIT 1""")
    for x in local_cursor:
        entries = x[0]
    local_database.close()
    post("http://www.primegiveaway.com/update_entries_stats", data={'email':email,'entries':entries})

    #Starts the script over once it completes the last item
    amazon_bot(email, password, name, want_follow, firefox_profile_path, amazon_pass)

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
    print ("Please sign in to your FinessePrime Account:")
    email = input("Email: ")
    password = getpass.getpass("Password: ")

    #Run login_account function to check if user has account with FinessePrime
    if post("http://www.primegiveaway.com/programlogin", data={'email':email,'password':password}).text == 'True':

        #Create local storage if needed
        localhandler.create_local_account(email)

        #Open and find last entry count in enteredurls table from local database
        local_database = sqlite3.connect('localdatabase.db', detect_types=sqlite3.PARSE_DECLTYPES)
        local_cursor = local_database.cursor()
        #Get entry data
        local_cursor.execute("""SELECT * FROM enteredurls ORDER BY id DESC LIMIT 1""")
        entries = local_cursor.fetchone()
        local_database.close()
        if entries is None:
            entries = 0
        else:
            entries = entries[0]

        #Update user stats
        post("http://www.primegiveaway.com/update_entries_stats", data={'email':email,'entries':entries})

        #Gather account settings
        account_settings = localhandler.find_local_account_settings()
        #Continue if able to find settings for user
        if account_settings != False:
            print ("")
            #Prompt user for settings update, move past if not
            change_settings = input("Would you like to change your settings? (Y/N): ").lower()

            while (change_settings != "yes") and (change_settings != "y") and (change_settings != "no") and (change_settings != "n"):
                print ("")
                print ("Invalid input please try again")
                change_settings = input("Would you like to change your settings? (Y/N): ").lower()

            if change_settings == "yes" or change_settings == "y":
                localhandler.update_local_settings() #Update the settings
                account_settings = localhandler.find_local_account_settings() #Load the newly saved settings

            #Account settings
            name = account_settings[0]
            want_follow = account_settings[1]
            firefox_profile_path = account_settings[2]
            amazon_pass = account_settings[3]
            #Reset amazon cookies
            localhandler.reset_amazon_cookies(email,password,firefox_profile_path, amazon_pass) #Turned off for now, amazon login captcha issues

            print ("")
            amazon_bot(email, password, name, want_follow, firefox_profile_path, amazon_pass)
        else:
            print ("Failed to find settings, please close program and try again.")
    else:
        print ("Login failed")
        print ("")
        load_login_info()

#Greeting message when first opened
print ("Welcome to the Amazon Giveaways Bot!")
print ("")

load_login_info()
