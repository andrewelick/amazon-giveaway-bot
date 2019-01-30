from myimports import os
from myimports import sys
from myimports import datetime
from myimports import string
from myimports import random
from myimports import time
from myimports import sqlite3
from myimports import hashlib
from myimports import pymysql
from myimports import get
from myimports import webdriver
from myimports import Select
from myimports import Options
from myimports import smtplib
from myimports import MIMEMultipart
from myimports import MIMEText
from myimports import Template
from myimports import getpass

#Connect to local storage database
def connect_to_local_database():
    try:
        conn = sqlite3.connect('localdatabase.db', detect_types=sqlite3.PARSE_DECLTYPES)
        return conn
    except:
        print ("Could not connect to local storage")
        conn = False
        return conn

#Create data on users computer for quick access
def create_local_account(email):
    #Connect to local database
    local_conn = connect_to_local_database()
    if local_conn is not False:
        c = local_conn.cursor()
        #Create tables: enteredurls, settings; Insert new settings data
        try:
            #Create enteredurls table
            c.execute("""CREATE TABLE IF NOT EXISTS enteredurls (id INTEGER PRIMARY KEY, url TEXT, day date)""")
            #Create settings table
            c.execute("""CREATE TABLE IF NOT EXISTS settings (name VARCHAR(255), want_follow INT, firefox_profile VARCHAR(255), amazon_pass VARCHAR(255))""")
            #Save data
            local_conn.commit()
        except:
            print ("Could not create local storage")
        finally:
            if local_conn:
                local_conn.close()

#Get local database settings
def find_local_account_settings():
    print ("Loading account settings...")
    #Connect to database
    local_conn = connect_to_local_database()
    if local_conn is not False:
        c = local_conn.cursor()

        try:
            c.execute("""SELECT * FROM settings""")
            account_settings = c.fetchone()
            if account_settings is not None:
                print ("Account settings loaded!")
                return account_settings
            else:
                print ("")
                if update_local_settings():
                    c.execute("""SELECT * FROM settings""")
                    account_settings = c.fetchone()
                    return account_settings
        except Exception as e:
            print ("Could not load local settings")
            return False
        finally:
            if local_conn:
                local_conn.close()

#Update local settings table
def update_local_settings():
    #Connect to database
    local_conn = connect_to_local_database()
    if local_conn is not False:
        c = local_conn.cursor()

        try:
            #Ask user for their settings preferences
            name = input("Please enter your name: ").lower()
            want_follow = input("Do you want to enter follow sponsor contests? (Y/N): ").lower()
            amazon_password = getpass.getpass("Enter you amazon account password: ")
            amazon_password_confirm = getpass.getpass("Confirm your amazon account password: ")
            #If passwords dont match try ask again
            while amazon_password != amazon_password_confirm:
                print ("")
                print ("Passwords didn't match! Try again.")
                amazon_password = getpass.getpass("Enter you amazon account password: ")
                amazon_password_confirm = getpass.getpass("Confirm your amazon account password: ")

            correct_info = input("Is this information correct? (Y/N): ").lower()
            #Check for valid input
            while (correct_info != "yes") and (correct_info != "y") and (correct_info != "no") and (correct_info != "n"):
                print ("")
                print ("Invalid input please try again")
                correct_info = input("Is this information correct? (Y/N): ").lower()

            if correct_info == "yes" or correct_info == "y":
                #Set the want follow variable
                if want_follow == "yes" or want_follow == "y":
                    want_follow = 1
                else:
                    want_follow = 0

                #Find Firefox profile PATH
                print ("Gathering profile path information...")
                firefox_profile = find_profile_path()

                try:
                    #Update user settings
                    c.execute("""UPDATE settings SET name=?, want_follow=?, firefox_profile, amazon_pass=?""", (name, want_follow,firefox_profile,amazon_password))
                except:
                    #Create settings row
                    c.execute("""INSERT INTO settings (name, want_follow, firefox_profile, amazon_pass) VALUES (?, ?, ?, ?)""", (name, 1, firefox_profile, amazon_password,))
                #Save the settings
                local_conn.commit()
                print ("Settings have been updated!")
                print ("")
                return True
            else:
                print("")
                update_settings(email)
        except:
            print ("Could not update settings")
            print ("")
            return False
        finally:
            if local_conn:
                local_conn.close()

#Finds user profile path for Firefox browser
def find_profile_path():
    options = Options()
    options.headless = True
    browser = webdriver.Firefox(options=options,executable_path=os.path.join(os.path.dirname(sys.argv[0]), 'geckodriver.exe')) #Initalize browser
    browser.get(('about:profiles')) #Open profiles settings inside firefox browser
    find_table = browser.find_element_by_tag_name('table')
    find_root_directory_container = find_table.find_elements_by_tag_name('tr')[1]
    find_root_directory = find_root_directory_container.find_element_by_tag_name('td')
    button_text = find_root_directory.find_element_by_tag_name('button')
    profile_path = find_root_directory.text.replace(button_text.text,'') #Remove row header
    return profile_path.rstrip()

#Changes amazon account to one associated with Finesse Prime account, keeping nonpaying accounts from using
def reset_amazon_cookies(email,password,firefox_profile_path, amazon_pass):
    print ("Cleaning old data...")
    #Open Firefox browser, headless, and go to amazon.com login page
    options = Options()
    options.headless = True
    browser = webdriver.Firefox(options=options,executable_path=os.path.join(os.path.dirname(sys.argv[0]), 'geckodriver.exe')) #Initalize browser
    browser.get(('https://www.amazon.com/gp/css/homepage.html/ref=nav_youraccount_ya'))
    time.sleep(2.32)
    browser.find_element_by_id('nav-your-amazon').click()
    #Log into amazon account
    try:
        browser.find_element_by_id('ap_email').send_keys(email)
        time.sleep(1.32)
        browser.find_element_by_id('ap_password').send_keys(amazon_pass)
        time.sleep(1.48)
        browser.find_element_by_name('rememberMe').click()
        time.sleep(1.84)
        browser.find_element_by_id('signInSubmit').click()
        new_cookies = browser.get_cookies() #Get new cookies
    except Exception as e:
        print (e)
    finally:
        browser.close()

    #Connect to Firefox cookies database
    firefox_cookies_path = firefox_profile_path+"\cookies.sqlite"
    database = sqlite3.connect(firefox_cookies_path, detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = database.cursor()
    try:
        #Delete old amazon cookies
        cursor.execute("""DELETE FROM moz_cookies WHERE baseDomain='amazon.com'""")
        cursor.execute("""DELETE FROM moz_cookies WHERE baseDomain='amazonpay.com'""")
        cursor.execute("""DELETE FROM moz_cookies WHERE baseDomain='amazon-adsystem.com'""")
    except:
        print ("Error cleaning old data")
    #Add each cookie into Firefox cookies table
    for x in new_cookies:
        new_cookie_name = x['name']
        new_cookie_value = x['value']
        new_cookie_path = x['path']
        new_cookie_baseDomain = "amazon.com"
        new_cookie_host = x['domain']
        new_cookie_expiry = x['expiry']
        new_cookie_secure = x['secure']
        new_cookie_httpOnly = x['httpOnly']

        whole_new_cookie = (new_cookie_baseDomain, new_cookie_name, new_cookie_value, new_cookie_host, new_cookie_path, new_cookie_expiry, new_cookie_secure, new_cookie_httpOnly)
        cursor.execute("""INSERT OR IGNORE INTO moz_cookies (baseDomain, name, value, host, path, expiry, isSecure, isHttpOnly) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", whole_new_cookie)
    #Save new cookies and close connection
    database.commit()
    database.close()
    print ("Old data cleaned!")
