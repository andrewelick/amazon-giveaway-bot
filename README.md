# Amazon Giveaway Bot

### This bot is used to automatically enter you into thousands of giveaways at Amazon's giveaway section.

#### What you will need:
1. **Geckodriver.exe** which is included repository (OSX or Linux find variant)
2. **Firefox**
3. **Selenium**
4. **BeautifulSoup**
5. **Requests**
6. **entered_urls.txt** file (this should be automatically created but if not you will have to do so)

You can pip install Selenium, BeautifulSoup, and Requests using the command:
**python pip install Selenium BeautifulSoup4 Requests**

#### Set up instructions:
1. Once you have everything installed make sure to place the geckodriver in the same folder as the amazoncontest.py file
2. Make sure Selenium, BeautifulSoup, and requests are installed into your python environment.
3. Create a Firefox profile
4. Open Firefox using that profile and log into your Amazon account. Make sure to check the *remember me* box to keep you logged in.
5. Change the `PATH` of the variable profile to the path of the Firefox profile the you just created. `profile = webdriver.FirefoxProfile('')`. This will allow you stay logged in to your Amazon account and run the program in _headless mode_. If you do not do this you will need to change the line `options.headless = True` to `options.headless = False`
6. Make sure your Amazon account has the correct address assigned as you will not be able to change it once the prize has already been won. Add a phone number to your account to ensure all prizes can be entered into.

#### To Run:
Simply run the script in and input the information requested. Then sit back and enjoy the winnings.

#### The way it works:
It will at first ask you some basic information regarding your amazon login information including your: email, password, and name. As well as some giveaway preferences such as entering into giveaways in which you must follow the sponsor to enter. **None of your Amazon login information is saved anywhere and is used strictly to help the script log into your account**

Next the script will parse through a list of thousands of current giveaways and compile them into a list to then be sorted.  It will remove all previously entered giveaways using the entered_urls.txt list and then sort them by price in a descending order. *If python fails to create the entered_urls.txt file then please create one in the same folder as everything else.*

Then all the giveaways are collected and sorted the script will then use Selenium to open a Firefox browser window in headless mode (*invisible browser*) and log into your account if you did not create a Firefox profile or if it failed to locate it. From there it will identify what steps it must do to enter the giveaway, such as watching a video or clicking on the animated entry box.

Once the entry process is completed, it will check to see if you have won and if so will confirm your winnings. You should receive an email confirming your win within the same day.

When the individual prize process is complete the browser window will close, the giveaway url will be logged into entered_urls.txt and the browser window will be closed.

After all the current giveaways have been cycled through the script will automatically check again and if the minimum threshold number is met then it will start again, if not it will wait a set amount of time and check again later.
