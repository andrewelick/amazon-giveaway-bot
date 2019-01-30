from myimports1 import os
from myimports1 import sys
from myimports1 import datetime
from myimports1 import string
from myimports1 import random
from myimports1 import time
from myimports1 import hashlib
from myimports1 import pymysql
from myimports1 import get
from myimports1 import smtplib
from myimports1 import MIMEMultipart
from myimports1 import MIMEText
from myimports1 import Template
from myimports1 import getpass

#Connect to Prime Giveaway database
def connect_to_database():
    try:
        conn = pymysql.connect(
        host='192.168.1.128', #External IP 99.114.66.154 Local IP 192.168.1.111
        db='amazon',
        user='jeffbezos', #jeffbezos
        password='alexa', #alexa
        )
        return conn
    except Exception as e:
        print (e)
        print ("Could not connect to Prime Giveaway database")
        conn = False
        return conn

#Create new Prime Giveaway account data
def create_account(email, password, name):
    #Connect to Prime Giveaway database
    conn = connect_to_database()
    if conn is not False:
        c = conn.cursor()

        try:
            #Look to see if email account is already being used
            find_email = c.execute("""SELECT * FROM accounts WHERE email=%s""", (email,))

            #If the email has not been used yet
            if find_email == 0:
                #Create random UID key, hash password, and get date
                uid = ''.join([random.choice(string.ascii_uppercase + string.digits) for x in range(12)]) #Combine letters and numbers, in a 12 digit string
                hashed_password = hashlib.sha256(password.encode()).hexdigest() #Hash the password
                date_joined = datetime.date.today() #Get the current date
                #Tuples used to create rows in each table, accounts, stats, settings
                accounts_details = (uid, email, hashed_password, date_joined, 0)
                stats_details = (uid, 0, 0, '0000-00-00', date_joined)
                settings_details = (uid, name, 1)

                #Create user in accounts table
                c.execute("""INSERT INTO accounts (uid, email, password, joined, active) VALUES (%s, %s, %s, %s, %s)""", accounts_details)
                #Create user in stats table
                c.execute("""INSERT INTO stats (uid, entries, wins, last_won, last_used) VALUES (%s, %s, %s, %s, %s)""", stats_details)
                #Create user in settings table
                c.execute("""INSERT INTO settings (uid, name, want_follow) VALUES (%s, %s, %s)""", settings_details)
                #Save the data
                conn.commit()
                #Send user authentication code via email
                send_auth_code(email,name)
                return True
            elif find_email > 0:
                return "Taken"
        except Exception as e:
            print (e)
        finally:
            if conn:
                conn.close()

#Check to see if user has an account
def login_account(email, password):
    #Connect to database
    conn = connect_to_database()
    if conn is not False:
        c = conn.cursor()

        try:
            #Check for email in accounts table
            find_email = c.execute("""SELECT * FROM accounts WHERE email=%s""", (email,))
            account_details = c.fetchone()
            account_status = account_details[4]

            if find_email == 1:
                #Hash the password
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                #Search accounts table for
                user_logged_in = c.execute("""SELECT * FROM accounts WHERE email=%s AND password=%s""", (email, hashed_password,))

                if user_logged_in == 1:
                    return {'result':'True','message':'Logged in!', 'account_status':account_status}
                else:
                    return {'result':'False','message':'Incorrect email/password combination, please try again'}
            else:
                return {'result':'False','message':'No account associated with that email address'}
        except Exception as e:
            return {'result':'False','message':'Could not connect to Prime Giveaway user database'}
        finally:
            if conn:
                conn.close()

#Login account for client program
def program_login_account(email,password):
    #Connect to database
    conn = connect_to_database()
    if conn is not False:
        c = conn.cursor()

        try:
            find_account = c.execute("""SELECT * FROM accounts WHERE email=%s AND password=%s AND payment=%s""",(email,password,1,))
            if find_account == 1:
                return True
            else:
                return False
        except:
            return False

#Check user account and see if activated
def check_auth_status(email):
    #Connect to database
    conn = connect_to_database()
    if conn is not False:
        c = conn.cursor()
        try:
            #Check for email in accounts table
            find_email = c.execute("""SELECT * FROM accounts WHERE email=%s""", (email,))
            account_details = c.fetchone()
            account_status = account_details[4]
            return account_status
        except:
            pass
        finally:
            if conn:
                conn.close()

#Confirm account email
def auth_account(email,auth_code):
    #Connect to database
    conn = connect_to_database()
    if conn is not False:
        c = conn.cursor()
        try:
            auth_code_results = c.execute("""SELECT * FROM temp_codes WHERE email=%s AND auth_code=%s""", (email,auth_code,))
            #If authentication code is correct update account to active
            if auth_code_results == 1:
                c.execute("""UPDATE accounts SET active=%s WHERE email=%s""", (1,email,))
                c.execute("""DELETE FROM temp_codes WHERE email=%s""", (email,))
                conn.commit()
                return True
            else:
                return "Invalid"
        except Exception as e:
            print (e)
            return False
        finally:
            if conn:
                conn.close()

#Generate validation code and send in email thne create temp_codes entry
def send_auth_code(email,name):
    #Connect to Prime Giveaway database
    conn = connect_to_database()
    if conn is not False:
        c = conn.cursor()
        try:
            #Check if authentication code is already in and delete it
            reset_code = c.execute("""SELECT * FROM temp_codes WHERE email=%s""", email)
            if reset_code != 0:
                c.execute("""DELETE FROM temp_codes WHERE email=%s""", email)

            #Generate authentication code
            auth_code = ''.join([random.choice(string.ascii_uppercase + string.digits) for x in range(6)])
            #Insert row into auth_code table
            c.execute("""INSERT INTO temp_codes (email, auth_code) VALUES (%s, %s)""", (email,auth_code,))
            #Save data
            conn.commit()
            auth_code_created = True
        except Exception as e:
            print (e)
            auth_code_created = False
        finally:
            if conn:
                conn.close()

    if auth_code_created is True:
        #---Send the email -----------
        #Read email file
        with open('email_files/emailauth.txt', 'r', encoding='utf-8') as email_template_file:
            template_content = Template(email_template_file.read())
            email_template_file.close()

        #Set up SMTP server, SSL connection
        #ssl_context = pyOpenSSL.SSLv3_METHOD(SSLv3_METHOD)
        smtp_server = smtplib.SMTP_SSL('smtp.zoho.com',465)
        smtp_server.login('root@primegiveaway.com', 'LittleBlives!321') #Sender andy.elick@gmail.com, ggixchywavjqvilp

        msg = MIMEMultipart() #Creates the message
        message = template_content.substitute(PERSON_NAME=name, AUTH_CODE=auth_code) #Change emailauth.txt variables
        #Set up email parameters
        msg['From']= 'Finesse Prime'
        msg['To']= email
        msg['subject']='Finesse Prime authentication code'
        msg.attach(MIMEText(message, 'plain')) #Add emailauth.txt to email
        #Send the message
        smtp_server.send_message(msg)
        #Close SMTP connection
        smtp_server.quit()

#Resend account conformation code again if user requests
def resend_auth_code(email):
    #Connect to database
    conn = connect_to_database()
    if conn is not False:
        c = conn.cursor()
        try:
            c.execute("""SELECT name FROM settings WHERE uid IN (SELECT uid FROM accounts WHERE email=%s)""", (email,))
            name = c.fetchone()[0]
            send_auth_code(email,name)
            return True
        except Exception as e:
            print (e)
            return False
        finally:
            if conn:
                conn.close()

#Reset passcode and send new password
def send_reset_password(email):
    #connect to finesse prime database
    conn = connect_to_database()
    if conn is not False:
        c = conn.cursor()
        #Find account associated with email
        find_email = c.execute("""SELECT * FROM accounts WHERE email=%s""", (email,))
        if find_email != 0:
            account_data = c.fetchone()
            uid = account_data[0]

            # #Find if account already has a reset code
            # c.execute("""DELETE FROM reset_password_codes WHERE uid=%s""", (uid,))

            #Generate random passcode
            reset_code = ''.join([random.choice(string.ascii_uppercase + string.digits) for x in range(8)])
            try:
                #Change accounts password to newly generate password
                c.execute("""INSERT INTO reset_password_codes (uid,reset_code) VALUES (%s, %s) ON DUPLICATE KEY UPDATE reset_code=%s""", (uid,reset_code,reset_code,))
                conn.commit()
                password_reset = True
            except Exception as e:
                print (e)
                print ("Could not reset password for the account")
                password_reset = False

            #Send reset code to user's email address
            if password_reset is True:
                #Reset link that is sent to the user
                reset_link = "http://localhost/resetpassword?uid="+uid+"&auth_code="+reset_code

                #Get the reset email file
                with open('email_files/resetpassword.txt', 'r', encoding='utf-8') as email_template_file:
                    template_content = Template(email_template_file.read())
                    email_template_file.close()

                #Set up SMTP server, SSL connection
                #ssl_context = pyOpenSSL.SSLv3_METHOD(SSLv3_METHOD)
                smtp_server = smtplib.SMTP_SSL('smtp.zoho.com',465)
                smtp_server.login('Prime Giveawaymessages@gmail.com', 'JeffBezos$69') #Sender andy.elick@gmail.com, ggixchywavjqvilp

                msg = MIMEMultipart() #Creates the message
                message = template_content.substitute(RESET_LINK=reset_link) #Change emailauth.txt variables
                #Set up email parameters
                msg['From']= 'Finesse Prime'
                msg['To']= email
                msg['subject']='Finesse Prime password reset request'
                msg.attach(MIMEText(message, 'plain')) #Add emailauth.txt to email
                #Send the message
                smtp_server.send_message(msg)
                #Close SMTP connection
                smtp_server.quit()
                return True
        else:
            print ("Unable to find account with that address")

#Confirm temp code and change password
def change_password(uid,password,auth_code):
    #Connect to database
    conn = connect_to_database()
    if conn is not False:
        c = conn.cursor()
        try:
            find_account = c.execute("""SELECT * FROM accounts WHERE uid=%s""",(uid,))

            if find_account == 1:
                #Check if came from valid reset link
                auth_code_true = c.execute("""SELECT * FROM reset_password_codes WHERE uid=%s AND reset_code=%s""", (uid,auth_code))
                if auth_code_true == 1:
                    #Hash password
                    hashed_password = hashlib.sha256(password.encode()).hexdigest()
                    c.execute("""UPDATE accounts SET password=%s WHERE uid=%s""", (hashed_password,uid,))
                    c.execute("""DELETE FROM reset_password_codes WHERE uid=%s""", (uid,))
                    conn.commit()
                    return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            print (e)
            return e
        finally:
            if conn:
                conn.close()

#Gather account settings for user profile page
def gather_account_settings(email):
    #Connect to Finesse Prime database
    conn = connect_to_database()
    if conn is not False:
        c = conn.cursor()
        try:
            c.execute("""SELECT joined, active, payment FROM accounts WHERE email=%s""",(email,))
            account_data = c.fetchone()
            return account_data
        except Exception as e:
            print (e)
        finally:
            if conn:
                conn.close()

#Gather winning stats for user account table
def gather_winning_stats(email):
    #Connect to Finesse Prime database
    conn = connect_to_database()
    if conn is not False:
        c = conn.cursor()
        try:
            #Find UID for email
            c.execute("""SELECT uid FROM accounts WHERE email=%s""", (email,))
            uid = c.fetchone()
            #Find all wins that have the UID
            if c.execute("""SELECT * FROM prizes WHERE winner_uid=%s ORDER BY win_date DESC""", (uid,)) != 0:
                prizes = c.fetchall()
            else:
                prizes = 0
            return prizes
        except Exception as e:
            print (e)
        finally:
            if conn:
                conn.close()

#Update entries in stats table
def update_entries_stats(email, entries):
    #Connect to database
    conn = connect_to_database()
    if conn is not False:
        c = conn.cursor()

        try:
            #Update entries and last_used
            c.execute("""UPDATE stats SET entries=%s, last_used=%s WHERE uid IN (SELECT uid FROM accounts WHERE email=%s)""", (entries, datetime.date.today(), email,))
            conn.commit()
            return "True"
        except Exception as e:
            return "False"
        finally:
            if conn:
                conn.close()

#Update wins and last_won in stats table
def update_wins_stats(email):
    #Connect to database
    conn = connect_to_database()
    if conn is not False:
        c = conn.cursor()

        current_time = datetime.date.today()
        try:
            #Find user winning stats
            c.execute("""SELECT wins FROM stats WHERE uid IN (SELECT uid FROM accounts WHERE email=%s)""", email)
            wins = c.fetchone()
            wins = int(wins[0]) + 1
            #Update winning stats
            c.execute("""UPDATE stats SET wins=%s, last_won=%s WHERE uid IN (SELECT uid FROM accounts WHERE email=%s)""", (wins, current_time, email))
            conn.commit()
        except Exception as e:
            print (e)
            print ("Could not update stats")
        finally:
            if conn:
                conn.close()

#Update wins and last_won in stats table
def add_winning_prize(email, giveaway_item_name, giveaway_item_price, link):
    #Connect to database
    conn = connect_to_database()
    if conn is not False:
        c = conn.cursor()
        try:
            c.execute("""SELECT uid FROM accounts WHERE email=%s""", email)
            winner_uid = c.fetchone()
            winner_uid = winner_uid[0]
        except:
            winner_uid = "NULL"

        price = float(giveaway_item_price[1:])
        win_date = datetime.date.today()
        prize_stats = (giveaway_item_name, price, link, winner_uid, win_date)

        try:
            #Add prize info into prize table
            c.execute("""INSERT INTO prizes (name, price, url, winner_uid, win_date) VALUES (%s, %s, %s, %s, %s)""", (prize_stats))
            conn.commit()
        except Exception as e:
            print (e)
            print ("Error saving win")
        finally:
            if conn:
                conn.close()

#Paypal payment was accepted, add to payments column
def payment_accepted(payer_email,payment_gross):
    #connect to database
    conn = connect_to_database()
    if conn is not False:
        c = conn.cursor()
        try:
            #Find uid associated with email address
            c.execute("""SELECT uid FROM accounts WHERE email=%s""", (payer_email,))
            uid = c.fetchone()
            if uid:
                #Format date for mysql
                payment_date = datetime.datetime.now().replace(microsecond=0)

                c.execute("""INSERT INTO payments (uid,payment_gross,date) VALUES (%s, %s, %s)""", (uid,payment_gross,payment_date))
                conn.commit()
                return True
            else:
                return "No account with that email address"
        except Exception as e:
            return e
        finally:
            if conn:
                conn.close()

#Activate user account when payment is logged
def activate_paid_account(session_email):
    #Connect to database
    conn = connect_to_database()
    if conn is not False:
        c = conn.cursor()
        try:
            c.execute("""UPDATE accounts SET payment=1 WHERE email=%s""", (session_email,))
            conn.commit()
            return True
        except Exception as e:
            return e
        finally:
            if conn:
                conn.cursor()
