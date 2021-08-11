import requests, discord, os
from discord.ext import commands
from io import StringIO
import json
from discord.utils import get

# API Credentials
baseURL = "https://dashboard.iproyal.com/api/residential/reseller"
Auth = {"X-Access-Token" : "", "Content-type" : "application/json"}
# Discord Bot Token
TOKEN = ""

bot = commands.Bot(command_prefix=".")

@bot.command()
async def discounts(ctx, mode="", code="", value=""):
    list_mode = ("ls","list","l")
    rm_mode = ("remove", "rm", "del")
    add_mode = ("add", "new")
    with open("discount_codes.json", "r") as f:
        discount_codes = json.load(f)
    if mode != "":
        if mode in list_mode:
            embedVar = discord.Embed(title="Current Discount Codes")
            for x in discount_codes:
                embedVar.add_field(name=f"Discount code '{x}'", value=discount_codes[x], inline=False)
        elif mode in rm_mode:
            if code in discount_codes:
                discount_codes.pop(code)
                embedVar = discord.Embed(title="Success",description=f"{code} have been deleted", color=0x32a840)
            elif code == "":
                embedVar = discord.Embed(title="Error",description="Do you think I'm a genie? I don't know which discount code you want to kill \n Usage: .discounts rm 'discount code'", color=0xcf1313)        
            elif code not in discount_codes:
                embedVar = discord.Embed(title="Error",description=f"{code} is not in the database \n Check .discounts ls", color=0xcf1313)        
        elif mode in add_mode:
            if code != "" and value != "":
                try:
                    value = int(value)
                    if value in range(1,101):
                        discount_codes[code] = value
                        embedVar = discord.Embed(title="Success",description=f"{code} is now added with value {value}", color=0x32a840)
                    else:
                        embedVar = discord.Embed(title="What are you doing? xd",description="The discount code value needs to be in range from 1 to 100", color=0xcf1313)
                except Exception:
                    embedVar = discord.Embed(title="Error",description="Use only an integer for value", color=0xcf1313)        
            else:
                embedVar = discord.Embed(title="Why?",description="Why would you like to add a discount code that doesn't have name or value?", color=0xcf1313)
    

        with open("discount_codes.json", "w") as f:
            json.dump(discount_codes, f, indent=4)

        
    else:
        embedVar = discord.Embed(title= "Help", description="This command is used to manage the discount codes database \n Usage: .discounts <mode> <code> <value> \n Fill Value only if your mode is add_mode")
        embedVar.add_field(name="List mode keywords", value=list_mode)
        embedVar.add_field(name="Add mode keywords", value=add_mode)
        embedVar.add_field(name="Remove mode keywords", value=rm_mode)
        
    await ctx.send(embed=embedVar)


@bot.command()
async def dcounter(ctx, opt="show"):
    with open("counters.json", "r") as jsonf:
        counters = json.load(jsonf)
    if opt == "show":
        embedVar = discord.Embed(title="Discount Code Counter")
        for code in counters:
            embedVar.add_field(name=code, value=counters[code], inline=False)
        await ctx.send(embed=embedVar)
    elif opt == "clear":
        for code in list(counters):
            counters.pop(code)
        with open("counters.json","w") as jsonf:
            json.dump(counters, jsonf, indent=4)
        await ctx.send("Cleared")

@bot.command()
async def account_info(ctx):
    info = requests.get(baseURL + "/my-info", headers=Auth).json()["data"]
    
    embedVar = discord.Embed(title="Reseller Account Information", description=info["username"])
    embedVar.add_field(name="Available Balance", value=info["balance"], inline=False)
    embedVar.add_field(name="Proxy Auth Key", value=info["proxy_authkey"])

    await ctx.send(embed=embedVar)
      

@bot.command()
async def adduser(ctx, username):
    user_adding = requests.post(baseURL + "/sub-users/create", headers=Auth, json={"username" : username}).json()
    if user_adding["status"] != 500:
        embedVar = discord.Embed(title="Success!", description="The user {} has been added successfully".format(username), color=0x00FF00)
    elif len(username) < 4:
        embedVar = discord.Embed(title="Error", description="The username should have at least 4 characters!!", color=0xFF0000)
    else:
        embedVar = discord.Embed(title="Error", description="Looks like the user {} already exists".format(username), color=0xFF0000)
    await ctx.send(embed=embedVar)

@bot.command()
async def listusers(ctx):
    await ctx.send("Listing... (Might take some time)", delete_after=0)
    listing = requests.get(baseURL + "/sub-users/view-all", headers=Auth).json()

    f = StringIO()
    for x in listing["data"]:
        f.write(str(x) + os.linesep)
    f.seek(0)

    await ctx.send(file=discord.File(f, filename="Users.txt"))

@bot.command()
async def addbalance(ctx, username, quantity):
    try:
        response = requests.post(baseURL + "/sub-users/give-balance", headers=Auth, json={"username" : username, "amount_usd_cents" : int(quantity)}).json()
        if response["status"] == 200:
            await ctx.send("Done")
        else:
            await ctx.send("Error: " + response["message"])
    except Exception:
        await ctx.send("Error, please check that the username inputted exists and that the quantity to send is a number")

@bot.command()
async def purchase(ctx, value):
    embedVar = discord.Embed(title=f"Total {value}$", description="**Payment is most preferred from top to bottom**")
    stripe = get(ctx.message.guild.emojis, name="stripe")
    zelle = get(ctx.message.guild.emojis, name="zelle")
    revoult = get(ctx.message.guild.emojis, name="revolut")
    venmo = get(ctx.message.guild.emojis, name="venmo")
    cashapp = get(ctx.message.guild.emojis, name="cashapp")

   
    await ctx.send(embed=embedVar)
    

@bot.command()
async def delbalance(ctx, username, quantity):
    try:
        response = requests.post(baseURL + "/sub-users/take-balance", headers=Auth, json={"username" : username, "amount_usd_cents" : int(quantity)}).json()
        if response["status"] == 200:
            await ctx.send("Done")
        else:
            await ctx.send("Error: " + response["message"])
    except Exception:
       await ctx.send("Error, please check that the username inputted exists and that the quantity to send is a number")

@bot.event
async def on_message(message):
    adminIDs = (771839360785973269,  257009761571176458, 420777488269049856, 257631037843046402)
    channelIDs = (796476232152776744,798937040464642088)
    if message.author.id in adminIDs:
        await bot.process_commands(message) 

@bot.event
async def on_ready():
    print("Ready")

bot.run(TOKEN)
