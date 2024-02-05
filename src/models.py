#

class User():
    
    def __init__(self, cas_username, cas_email, discord_id):
        self.cas_username = cas_username
        self.cas_email = cas_email
        self.discord_id = discord_id

    def link_accounts(self):
        pass # TODO: add to database

    def give_role(self):
        pass # TODO: add to discord

    def __str__(self):
        return f"User: {self.cas_username}, Discord ID: {self.discord_id}"
