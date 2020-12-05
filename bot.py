import discord
from discord.ext import commands
from suggestions import *
from config import *
import datetime
import asyncio
import tenorpy
import random
import json





# Errors
class SuggestionContentLengthError(Exception):
    pass

class SuggestionContentExplicitError(Exception):
    pass





# Used to block explicit words from being sent using the suggestions system
def checkExplicit(suggestion: str):
    # Check if suggestion is too long or too short
    if len(suggestion) > 1200:
        raise SuggestionContentLengthError()
    
    elif len(suggestion) < 10:
        raise SuggestionContentLengthError()

    # Check if suggestion contains explicit language
    ### NOTE - Will add soon ###





# Used to simplify embeds and create cleaner code
def simplifyEmbed(ctx, embed : discord.Embed, success : bool):
    ### NOTE - This might be modified or fully removed sooner or later ###
    # Define discord colours
    success_colour = discord.Colour(config["success-colour-decimal"])
    error_colour = discord.Colour(config["error-colour-decimal"])

    # Set colour of embed
    if success == True:
        embed.colour = success_colour
    elif success == False:
        embed.colour = error_colour

    embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
    embed.set_footer(text=f"Today at {datetime.datetime.now().strftime('%H:%M:%S')} [GB]")

    return embed





bot = commands.Bot(command_prefix=config["prefix"])
bot.remove_command("help") # Probably better ways to do this





# Error handler
@bot.event
async def on_command_error(ctx, error):
    # Check if the error is a specific type and tell the user accordingly
    if isinstance(error.original, SuggestionContentLengthError):
        embed = discord.Embed(description="Suggestion too short/long.\nYour suggestion must be <10 characters and >1200 characters.")
        embed = simplifyEmbed(ctx, embed, False)
        return await ctx.send(embed=embed)

    elif isinstance(error.original, SuggestionContentExplicitError):
        embed = discord.Embed(description="Your suggestion contains explicit language!")
        embed = simplifyEmbed(ctx, embed, False)
        return await ctx.send(embed=embed)

    elif isinstance(error.original, SuggestionIdInvalid):
        embed = discord.Embed(description="That suggestion id is invalid!")
        embed = simplifyEmbed(ctx, embed, False)
        return await ctx.send(embed=embed)

    elif isinstance(error.original, SuggestionNotFoundError):
        embed = discord.Embed(description="That suggestion does not exist!")
        embed = simplifyEmbed(ctx, embed, False)
        return await ctx.send(embed=embed)

    elif isinstance(error.original, commands.MissingAnyRole):
        embed = discord.Embed(description="You do not have sufficient permissions to run that command!")
        embed = simplifyEmbed(ctx, embed, False)
        return await ctx.send(embed=embed)

    else:
        print(error)
        embed = discord.Embed(description="Unknown error! Make sure the bot has the correct permissions!")
        embed = simplifyEmbed(ctx, embed, False)
        return await ctx.send(embed=embed)





# When bot connects print it in the command line
@bot.event
async def on_connect():
    print("Connected to the Discord servers!")





# Loop through statuses
@bot.event
async def on_ready():
    print("Ready to recieve commands!")

    while True:
        for status in config['statuses']:
            await bot.change_presence(activity=discord.Game(name=f"{config['prefix']}help | {status}"), status=discord.Status.dnd)
            await asyncio.sleep(30)
    




# When a message is deleted check if it is a suggestion and delete it
@bot.event
async def on_message_delete(message):
    if messageIsSuggestion(message.id):
        deleteSuggestion(messageToSuggestionId(message.id))
        





# Returns help page in an embed
@bot.command()
async def help(ctx):
    # The default helppage
    helppage = """
    **CoC Utilities**
    `{0}suggest <suggestion>` - Creates a suggestion, places it in <#{1}>.
    `{0}delsuggest <suggestion-id>` - Deletes a suggestion via ID, mods can delete any.
    `{0}ping` - Returns the bot's ping.
    `{0}source` - The source for the bot.

    **CoC Fun**
    `{0}explode <@user>` - User go boom.
    `{0}kiss <@user>` - Kiss a user, uwu owo rawr- I think someone heard me..
    `{0}8ball <question>` - Let the magic 8ball decide.
    
    """.format(config["prefix"], config["suggestions-channel-id"])
    
    # Send in embed
    embed = discord.Embed(title="RoboCoC", description=helppage)
    embed = simplifyEmbed(ctx, embed, True)
    
    await ctx.send(embed=embed)





# Returns the bots ping in an embed
@bot.command()
async def ping(ctx):
    # Get bot ping and round it to a whole number
    latency = round(bot.latency * 1000)

    # Send in embed
    embed = discord.Embed(description=f"**The bot's current ping:**\n**`{latency}`**")
    embed = simplifyEmbed(ctx, embed, True)

    await ctx.send(embed=embed)





# Suggests something
@bot.command()
async def suggest(ctx, *, suggestion):
    checkExplicit(suggestion)

    # Send to suggestions channel
    # Create suggestion and add it to the json file
    embed = discord.Embed(description=f"**New suggestion!**\n'{suggestion}'\nID: ")
    embed = simplifyEmbed(ctx, embed, True)
    suggestion = await createSuggestion(suggestion, ctx, embed)

    # Send to ctx channel
    embed = discord.Embed(description=f"Your suggestion has been submitted!\nID: {suggestion.id}")
    embed = simplifyEmbed(ctx, embed, True)

    await ctx.send(embed=embed)





# Deletes a suggestion, moderator only
@bot.command()
async def delsuggest(ctx, suggestion_id : int):
    # Fetch suggestion and check if author matches or has moderator role
    suggestion = Suggestion(suggestion_id)
    moderator_role = discord.utils.get(
        ctx.guild.roles,
        id=config["moderator-role-id"]
    )
    if suggestion.data["author-id"] != ctx.author.id:
        if moderator_role not in ctx.author.roles:
            raise commands.errors.MissingAnyRole(moderator_role)

    # Delete suggestion and its message
    suggestion.delete()
    suggestions_channel = discord.utils.get(
        ctx.guild.channels,
        id=config["suggestions-channel-id"]
    )
    message = await suggestions_channel.fetch_message(suggestion.data["message-id"])
    await message.delete()

    # Send embed to tell the user that the suggestion has been deleted
    embed = discord.Embed(description="Deleted that suggestion!")
    embed = simplifyEmbed(ctx, embed, True)

    await ctx.send(embed=embed)

    



# Explode / kill command
@bot.command()
async def explode(ctx, user : discord.Member):
    ### NOTE - Had to resort to just searching up gifs and putting them in manually, most likely to change in the future ###
    explosionGifs = []

    # Pick random gif
    gif = random.choice(explosionGifs)

    # Send gif in embed
    embed = discord.Embed(title=f"{user} got caught in an explosion!")
    embed = simplifyEmbed(ctx, embed, True)
    embed.set_image(url=gif)

    await ctx.send(embed=embed)


# ^ v These two are pretty much the same command, copy and paste if you want to create a similar command


# Kiss command
@bot.command(aliases=["kiss"])
async def smooch(ctx, user : discord.Member):
    ### NOTE - Had to resort to just searching up gifs and putting them in manually, most likely to change in the future ###
    smoochGifs = []

    # Pick random gif
    gif = random.choice(smoochGifs)

    # Send gif in embed
    embed = discord.Embed(title=f"{ctx.author} gave {user} a smooch!")
    embed = simplifyEmbed(ctx, embed, True)
    embed.set_image(url=gif)

    await ctx.send(embed=embed)





# 8ball command
@bot.command(aliases=["8ball"])
async def eightball(ctx, *, question):
    ### NOTE - Make sure to keep an even amount of yes and no responses ###
    ballResponses = ["Yes.", "No.", "Undecided.", "In the future, perhaps.", "Without a doubt.", "No, lol.", "Pie says yes so it must be yes.", "Pie says no so it must be no."]

    # Pick random response
    response = random.choice(ballResponses)

    # Send response in embed
    embed = discord.Embed(title=f"Answer: {response}", description=f"Original question: '{question}'")
    embed = simplifyEmbed(ctx, embed, True)

    await ctx.send(embed=embed)





# Source command
@bot.command(aliases=["details"])
async def source(ctx):
    # Send link to github in embed
    embed = discord.Embed(title="https://github.com/1tsIsaac/RoboCoC", description="Other cool peoples:\n[ItsIsaac's Github](https://github.com/1tsIsaac)\n[Laith's Github](https://github.com/LaithDevelopment)")
    embed = simplifyEmbed(ctx, embed, True)

    await ctx.send(embed=embed)





# Run bot, remove any commands in disabled commands
if disabled_commands != []:
    for command in disabled_commands:
        bot.remove_command(command)





bot.run(config["token"])
