# Flask Website about Lending 


https://github.com/kiyoticawry/CS50xFinalProject/assets/112307652/e27caf83-ff8c-40d4-9fb4-62366b45169b

# Full video Link

#### Video Demo:  https://youtu.be/GqGGEzSN2-U
#### Description:

I decided for the register page that it wont be a separate page to the login page and that when you want to register it will simply flip to the backside of the card. I decided this since i had done already some flipcard css effects in my homepage assignment and wanted to incorporate it there. Then I simply used ajax to communicate with flask that way there wont neccessarily be any loading of a page. Also if you have 2 Factor authentication enabled that flask will reply with an entire html page which will load up in a div on ajax. I liked this one since there is not any loading of any new pages, so registration and authentication dont have their own page but are simply in the login page.

It is a lending website That has basic features around lending such as transaction timeline to remember your transactions and Notfications to notify you of the next time you should pay it. Its main feature is its lend application where you can take on new lend which will then be shown in current debt by then that page is empty with a paragraph that explains what it does.I didnt use any kind of currency since I found it unnecessary for the project and simply decided to use decimal numbers for it. There in current debt there will be a progress bar and a percentage to show your progress along with your current debt remaining in red. the color of the progress is cyan which you can promptly change to redpink or lime in settings/other, I also styled the progress bar in 3D.

When you take a new lend there will be a 3% interest meaning 3% is added to your debt and you cannot take on a new lend if you are currently in one therefore you have to empty your current debt before you can take on a new lend. for transaction timeline for each debt you have taken it will be shown alonf with the month, amoutdue and status which will grow for each new lend you take.  The Status will either be pending or FullyPaid , when you click on one it will show all of the payments that you have made to that lend and their dates and how much. once your debt is fully paid the transactiontable will tag the payment that completed your debt as last payment. in sql the transactiontable consisting of all the payments to a lend are grouped together thats why there is id timeline which indexes users ID by producing a new IDtimeline for each new lend and Indexes payments to it. This allows me to have only to tables for it in SQLlite but that it pulls the neccessary table depending on the account and the lend that was taken.

In Notifications I have a toggle feature that shows whether you want to receive notifactions or not and if you want that you could decide on what intervals you could them. The basic is 1 day but you could change them to 3 or 5 days, what this means is that you will receive a notifcation reminding of the debt you havent paid once it passes the interval. The interval then restarts each time you the current debt and will only notify you once not every interval. If you dont have a any current debt that it will not notify you at all until you take on a new lend.

for Settings in basics, you can change your username which you will use to login anytime you want, the above bar shows your current username. for updating your password you are required to type your old password and then your new password and then confirm that password again. once succesful there will be a countdown till next week of which you cannot change your current password.for Settings 2 Factor Authentication, it generates a QR code of which you have to scan in a 3rd party authenticator app like google authenticator which will show the code where you will type it as to confirm that you have the authentication which promptly adds it to your accound, Now you will be required to type your authentication each time you log in.For Settings others,you can change the progress barcolor to cyan, redpink and lime with cyan being the default. you can also change the language even though it doesnt work By then I had already written a the entire route and a database for it thats why I still think its worth keeping for future use. The last feature is delete account which allows you to delete your account , prompting you only for your password and if you have authentication that it will also you prompt you for it before it deletes your account. When it deletes account it includes the entire transact table and transact timeline meaning your transactions and payments would be forgotten. I did this because I found unneccessary in the meantime to keep such data and simply opted for a full deletion of any data related to the user.



# Set up
 1. in command line: ```pip install -r requirments.txt```
 2. get an API key, for example in google cloud platform or IEX cloud
 3. make and copy the API key (this is to export it)
 4. in command line: ```export API_KEY={PUT API KEY HERE}```
 5. In command line: ```flask run```
   
# Certificate 
![image](https://github.com/kiyoticawry/CS50xFinalProject/assets/112307652/e23e8a4b-3bd4-4b32-960a-dd5a66db28ae)
