import datetime
import json
import random
import discord
from config import *



# Global stuffs
json_path = "suggestions.json"



# Errors
class SuggestionNotFoundError(Exception):
    pass

class SuggestionIdInvalid(Exception):
    pass



# JSON code-cleaners
def getJson():
    return json.load(open(json_path, "r"))

def writeJson(data):
    json.dump(data, open(json_path, "w"), indent=4)



# Functions for creating, deleting and grabbing suggestions
# Used in almost all functions, checks if ID exists and is valid
def checkSuggestionID(suggestion_id: int):
    # If the suggestion id is not 1000 - 9999, raise an error
    if suggestion_id < 1000:
        raise SuggestionIdInvalid(f"The suggestion ID '{suggestion_id}' is invalid.")

    elif suggestion_id > 9999:
        raise SuggestionIdInvalid(f"The suggestion ID '{suggestion_id}' is invalid.")

    # If the suggestion does not exist, raise an error
    if not suggestionExists(suggestion_id):
        raise SuggestionNotFoundError(f"The suggestion with ID of '{suggestion_id}' could not be found.")



async def createSuggestion(suggestion: str, ctx, embed):
    ### NOTE - Line below generates the ID, may add a failsafe in the future (check for duplicate IDs) ###
    suggestion_id = random.randint(1000, 9999)

    # Get the suggestions channel, this is a temporary, will be changed in the future
    suggestions_channel = discord.utils.get(ctx.guild.channels, id=config["suggestions-channel-id"])
    
    # Also add suggestion id to embed and send it
    embed.description += str(suggestion_id)
    message = await suggestions_channel.send(embed=embed)
    
    # Get the json, append the new suggestion, and write out
    data = getJson()
    data["data"].append(
        {
            "suggestion-id": suggestion_id,
            "author-id": ctx.author.id,
            "message-id": message.id
        }
    )
    writeJson(data)


    # Return the suggestion
    return Suggestion(suggestion_id)



def suggestionExists(suggestion_id: int):
    # Loop through suggestions, returns true if suggestion exists, false otherwise
    data = getJson()
    for ii in data["data"]:
        if ii["suggestion-id"] == suggestion_id:
            return True

    return False



def suggestionPosition(suggestion_id: int):
    checkSuggestionID(suggestion_id)
    # Loop through suggestions and return the suggestion position in the list
    data = getJson()

    position = 0

    for ii in data["data"]:
        if ii["suggestion-id"] == suggestion_id:
            return position

        position += 1



def messageIsSuggestion(message_id: int):
    # Loop through suggestions, returns true if message is a suggestion, false otherwise
    data = getJson()
    for ii in data["data"]:
        if ii["message-id"] == message_id:
            return True

    return False



def messageToSuggestionId(message_id: int):
    # Loops through suggestions, returns the suggestion id if the message id is in the same object
    data = getJson()
    for ii in data["data"]:
        if ii["message-id"] == message_id:
            return ii["suggestion-id"]



def deleteSuggestion(suggestion_id: int):
    checkSuggestionID(suggestion_id)
    # Find the suggestion and delete it
    data = getJson()
    data["data"].pop(suggestionPosition(suggestion_id))
    writeJson(data)



# Suggestion class
class Suggestion:
    def __init__(self, suggestion_id: int):
        checkSuggestionID(suggestion_id)
        # Self variables
        self.id = suggestion_id
        self.json_position = suggestionPosition(suggestion_id)
        self.data = getJson()["data"][self.json_position]

    def delete(self):
        deleteSuggestion(self.id)
