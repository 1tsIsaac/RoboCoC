import discord
from discord.ext import commands
import datetime
import colorama
import asyncio
import tenorpy
import random
import json

# Configure modules
colorama.init(convert=True)

# Create variables for console text, make it look fancy, but still clean in code
debugprof = f"{colorama.Fore.LIGHTRED_EX}[DEBUG]{colorama.Fore.RESET}"
successprof = f"{colorama.Fore.LIGHTCYAN_EX}[BOT]{colorama.Fore.RESET}"
errorprof = f"{colorama.Fore.RED}[BOT]{colorama.Fore.RESET}"

# Discord colours
success_colour = discord.Colour(8978339)
error_colour = discord.Colour(16746632)

# Dumb down some things which take up space in code

class Suggestion:
    def __init__(self, suggestion_id):
        self.json_data = json.load(open("suggestions.json", "r"))
        self.suggestions = self.json_data["suggestions"]
        self.suggestion_id = suggestion_id
        self.suggestions_channel = bot.get_channel(suggestionschannelid)

        pos = 0
        for suggestion in self.suggestions:
            if suggestion["id"] == self.suggestion_id:
                self.suggestion_pos = pos
                self.suggestion_data = suggestion
                self.exists = True
                return
            pos += 1
        
        self.exists = False
    
    async def delete(self):
        self.suggestions.pop(self.suggestion_pos)
        message = await self.suggestions_channel.fetch_message(self.get_message())
        await message.delete()
        json.dump(self.json_data, open("suggestions.json", "w"), indent=4)

    def get_author(self):
        return self.suggestion_data["author-id"]

    def get_message(self):
        return self.suggestion_data["message-id"]
        

    
async def createSuggestion(ctx, suggestion):
    data = json.load(open("suggestions.json", "r"))
    suggestion_id = random.randint(1000, 9999)
    suggestionschannel = bot.get_channel(suggestionschannelid)

    embed = discord.Embed(title="New suggestion!", description=f'**"{suggestion}"**\nID: {suggestion_id}')
    embed = simplifyEmbed(ctx, embed, True)
    embed.set_footer(text="React to vote:")
    message = await suggestionschannel.send(embed=embed)

    await message.add_reaction("👍")
    await message.add_reaction("👎")

    data["suggestions"].append({"id": suggestion_id, "author-id": ctx.author.id, "message-id": message.id})

    json.dump(data, open("suggestions.json", "w"), indent=4)

    return Suggestion(suggestion_id)

    
def simplifyEmbed(ctx, embed : discord.Embed, success : bool):
    if success == True:
        embed.colour = success_colour
    elif success == False:
        embed.colour = error_colour

    embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
    embed.set_footer(text=f"Today at {datetime.datetime.now().strftime('%H:%M')} [GB]")

    return embed
    
def getGif(tag):
    search = tenor.search(tag=tag, safesearch=False, limit=50)
    return search["results"][random.randint(0, 30)]["media"][0]["tinygif"]["url"]

async def statusLoop(statuslist):
    for status in BOT_STATUSES:
        await bot.change_presence(activity=discord.Game(name=f"{BOT_PREFIX}help | {status}"), status=discord.Status.dnd)
        await asyncio.sleep(30)

    await statusLoop(statuslist)


# Get config into variables
bot_settings = json.load(open("config.json", "r"))["bot-settings"]
disabled_commands = json.load(open("config.json", "r"))["disabled-commands"]
BOT_PREFIX = bot_settings["prefix"]
BOT_STATUSES = bot_settings["statuses"]
BOT_TOKEN = bot_settings["token"]
suggestionschannelid = bot_settings["suggestions-channel-id"]
moderatorroleid = bot_settings["moderator-role-id"]
tenor_token = bot_settings["tenor-token"]


tenor = tenorpy.Tenor()
tenor.api_key = tenor_token

bot = commands.Bot(command_prefix=BOT_PREFIX)

bot.remove_command("help")


# Send messages to console to say that bot is ready, connected, etc
# + set bot status
@bot.event
async def on_connect():
    print(f"{successprof} Connected to the Discord servers!")

@bot.event
async def on_ready():
    print(f"{successprof} Ready to recieve commands!")

    await statusLoop(BOT_STATUSES)
    

# When a message is deleted check if it is a suggestion
@bot.event
async def on_message_delete(message):
    data = json.load(open("suggestions.json", "r"))

    place = 0
    for suggestion in data["suggestions"]:
        if suggestion["message-id"] == message.id:
            data["suggestions"].pop(place)
            return json.dump(data, open("suggestions.json", "w"), indent=4)
        place += 1


# Returns help page in an embed, data in config
@bot.command()
async def help(ctx):
    helppage = """
    **CoC Utilities**
    `{0}suggest <suggestion>` - Creates a suggestion, places it in <#{1}>.
    `{0}delsuggest <suggestion-id>` - Deletes a suggestion via ID, mods can delete any.
    `{0}ping` - Returns the bot's ping.

    **CoC Fun**
    `{0}explode <@user>` - User go boom.
    `{0}kiss <@user>` - Kiss a user, uwu owo rawr- I think someone heard me..
    """.format(BOT_PREFIX, suggestionschannelid)
    
    embed = discord.Embed(title="RoboCoC", description=helppage)
    embed = simplifyEmbed(ctx, embed, True)
    
    await ctx.send(embed=embed)


# Returns the bots ping in an embed
@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)

    embed = discord.Embed(description=f"**The bot's current ping:**\n**`{latency}`**")
    embed = simplifyEmbed(ctx, embed, True)

    await ctx.send(embed=embed)


# Suggests something
@bot.command()
async def suggest(ctx, *, suggestion):
    if len(suggestion) > 1000:
        embed = discord.Embed(description="Error!: Your description cannot be over 1000 characters!")
        embed = simplifyEmbed(ctx, embed, False)
        return await ctx.send(embed=embed)

    embed = discord.Embed(description="Your suggestion has been posted!")
    embed = simplifyEmbed(ctx, embed, True)
    await ctx.send(embed=embed)

    suggestion = await createSuggestion(ctx, suggestion)

# Deletes a suggestion, moderator only
@bot.command()
async def delsuggest(ctx, suggestion_id : int):
    suggestion = Suggestion(suggestion_id)
    modrole = discord.utils.get(ctx.guild.roles, id=moderatorroleid)

    if not suggestion.exists:
        embed = discord.Embed(description="Error!: That suggestion does not exist!")
        embed = simplifyEmbed(ctx, embed, False)
        return await ctx.send(embed=embed)

    if suggestion.get_author() == ctx.author.id:
        await suggestion.delete()
    
    elif modrole in ctx.author.roles:
        await suggestion.delete()

    else:
        embed = discord.Embed(description="Error!: You did not make that suggestion!")
        embed = simplifyEmbed(ctx, embed, False)
        return await ctx.send(embed=embed)

    embed = discord.Embed(description="Deleted that suggestion!")
    embed = simplifyEmbed(ctx, embed, True)
    await ctx.send(embed=embed)

# Explode / kill command
@bot.command()
async def explode(ctx, user : discord.Member):
    embed = discord.Embed(title=f"{user} got caught in an explosion!")
    embed = simplifyEmbed(ctx, embed, True)
    embed.set_image(url=getGif("explosion death"))
    await ctx.send(embed=embed)

# Kiss command
@bot.command(aliases=["kiss"])
async def smooch(ctx, user : discord.Member):
    embed = discord.Embed(title=f"{ctx.author} gave {user} a smooch!")
    embed = simplifyEmbed(ctx, embed, True)
    embed.set_image(url=getGif("mocho kiss"))
    await ctx.send(embed=embed)

# Run bot, remove any commands in disabled commands
if disabled_commands != []:
    for command in disabled_commands:
        bot.remove_command(command)

bot.run(BOT_TOKEN)