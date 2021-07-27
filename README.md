# SOCash Bot

This is the Telegram Bot that SOC FOW'21 used to keep track of the points for each OG. A PostgreSQL Database was used to store the data and Python was used for the bot. This was hosted on Heroku, a free hosting service and the usage was not high enough to require any paid upgrade.

# Commands/Functions

## Adding new admins (OComm only)

In order to prevent unauthorized usage of the bot, we need to register users into the database so that the bot recognize them as authorized users. There are 2 ways to add authorized users.

### Forwarding Method

Forward a message sent by the target user. However, this only works if the user has allowed everyone to add a link to their account when forwarding their messages. (Privacy & Security > Forwarded messages > Everybody)

### /addadmin (sm/ocomm) (chat_ids)

1. Get the target user(s) to send `/me` to the bot to obtain their `chat id`, then send you their `chat id`.
2. Send `/addadmin chat_ids` (you can add multiple at once, separated by a space) to the bot if they are OComm, otherwise `/addadmin sm chat_ids`

Probably a good idea to separate the function into 2 (`/addocomm` and `/addsm` for simplicity sake)

When adding admins, the bot will try to access the chat with the specified user to access their username. If for some reason the chat does not exist (idk like if you get the chat id from another bot so you have not talked to this bot yet), then the bot will be unable to access their username which will be stored in the database.

## Revoking admin rights (OComm only)

If we decide to remove anyone's access to the bot for whatever reasons, we can do so.

### Forwarding Method

Similar to adding authorized users, if we want to revoke someone's access to the bot, we can forward a message from them. Similarly, this may or may not work depending on their privacy settings.

### /revoke (chat_ids/usernames)

- We can either specify a list of chat ids or a list of usernames (or a mixture of both).
- The bot will get a list of chat ids and usernames of authorized users from the database and then if the input is an integer, will check against the list of chat ids
- If the input is not an integer, then the bot will check against the list of usernames (which might not be updated)
- Example:
  - `/revoke 231289734 thisismyusername 3123192412 therealadele`

## /refreshusername (OComm only)

This function updates the list of usernames in the database by letting the bot access the chat of each chat id in the database and then accessing the username of that user. This function is very inefficient and time consuming so try not to use it if you don't have to.

## /admins (OComm only)

Allows you to see who are registered OComm and who are registered Station Masters in the bot.

## Adding Points

### /add (OGs) (amount)

- For the OGs for this command, the format is as such: Barg 2 -> B2; Geolog 3 -> G3
- As such, it is important for the houses to start with different letters
- Adding points for multiple OGs and subtracting points are supported. The bot does not auto set points to 0 if you subtract more than what an OG has.
- Case insensitive
- For example:
  - Adding 20 SOCash to Barg 1 and Aikon 3: `/add B1 A3 20`
  - Removing 10 SOCash from Etlas 5: `/add E5 -10`

## Mass Adding

### /massadd (amount)

- Adds the specified amount to all OG. Probably unused.
- Example: Adding 100 SOCash to all OGs: `/massadd 100`

## /display

We can display the scores of each OG in 2 different ways

1. By House
   - The OGs will be arranged by house, then by OG number. A1 A2 A3 A4 A5 A6 B1 B2 B3 B4 B5 B6 so on and so forth.
   - The total amount of SOCash for each house will be shown as well.
2. In descending order
   - Self explanatory

## /reset

Resets SOCash amount to 0 for all OGs. Use with caution!
