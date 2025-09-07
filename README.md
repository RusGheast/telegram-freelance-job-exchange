# telegram freelance job exchange

For the administration:

 1. /new_order - create a new order
 2. /confirm_<id>_<сумма> - confirm the order fulfillment and credit the currency
 3. /withdrawals - list of withdrawal requests
 4. /delete_order_<id> - delete order

# HOW IT WORK

 1. CREATE A SEPARATE FOLDER CALLED 'handlers'
 2. MOVE THE FILES admin.py and user.py THERE
 3. In the config.py file, paste the bot token and admin ID.
 4. pip install aiogram sqlalchemy aiosqlite
 5. python bot.py

That`s all)
