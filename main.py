import discord
from discord.ext import commands
import requests
import json
import asyncio
from io import StringIO
import os

#Stripe Core Info
stripe_auth = {"Authorization" : ""}
stripeURL = "https://api.stripe.com"

#Discord Core Info
TOKEN = ""
bot = commands.Bot(command_prefix=".", help_command=None)


async def clients_check():
    while True:
        with open("customersids.json","r") as customers_file:
            customers = json.load(customers_file)
        for customer in list(customers): 

            invoicecheck = requests.get(stripeURL + "/v1/invoices/" + customers[customer][0], headers=stripe_auth)
            #print(invoicecheck.json())
            #print(invoicecheck.json()["paid"])
            #print(invoicecheck.json()["lines"]["data"][0]["price"])
            if invoicecheck.json()["paid"] == True:
                #await ctx.send("Confirmed, processing order...")
               
                # IPRoyal API
                baseurl = "https://dashboard.iproyal.com/api/residential/reseller/sub-users/"
                AuthToken = {"X-Access-Token" : "", "Content-type" : "application/json"}
                # Check if sub-user exists
                sub_usr_check = requests.post(baseurl + "view-single", headers=AuthToken, json={"username":customer})
                print(sub_usr_check.json())
                print(sub_usr_check.json()["status"])
                print(sub_usr_check.json())
                customerid = customer
                if sub_usr_check.json()["status"] == 200:
                    # Add balance
                    a = requests.post(baseurl + "give-balance", headers=AuthToken, json={"username": customerid, "amount_usd_cents":customers[customer][1]})
                    print(a.json())
                else:
                    print(customer)
                    print(requests.post(baseurl + "create", headers=AuthToken, json={"username":customerid}).json())

                    print("b part")
                    #print(b.json())
                    c = requests.post(baseurl + "give-balance", headers=AuthToken, json={"username":customerid, "amount_usd_cents":customers[customer][1]})
                    
                    print(c.json())

                print("A purchase has been verified from: " + customer)
                customers.pop(customer)

        with open("customersids.json", "w") as CIDs:
            json.dump(customers,CIDs,indent=4)
        
        await asyncio.sleep(5)
        


@bot.command()
async def help(ctx):
    embedVar = discord.Embed(title="Fable Commands", color=0xD4485C)
    embedVar.add_field(name=".buy", value="Purchase more data \n .buy (amount)", inline=False)
    embedVar.add_field(name=".generate", value="Generates proxies \n .generate (country) (10/100/1000)", inline=False)
    embedVar.add_field(name=".list", value="Lists all the available countries \n .list", inline=False)
    embedVar.add_field(name=".data", value="View your current data usage \n .data", inline=False)
    embedVar.set_image(url="https://cdn.discordapp.com/attachments/806315231919210556/812540257307197470/1500x500.png")
    await ctx.send(embed=embedVar)



@bot.command(name="data")
async def data_view(ctx):
    userid = "fableproxies" + str(ctx.author.id)
    baseurl = "https://dashboard.iproyal.com/api/residential/reseller/sub-users/"
    AuthToken = {"X-Access-Token" : "", "Content-type" : "application/json"}

    data = requests.post(baseurl + "view-single", headers=AuthToken, json={"username":userid}).json()

    if data["status"] == 200:
        embedVar = discord.Embed(title="Available data", description="Your available data is: {:.2f} GB".format(float(data["data"]["balance"]/200)))
        await ctx.send(embed=embedVar)
    


@bot.command()
async def buy(ctx, quantity, discount_code = ""):
    #try:
    quantity = int(quantity)
    price_number = int(quantity * 600)
    with open("discount_codes.json", "r") as jsonf:
        codes = json.load(jsonf)
    #print(price)
    if discount_code != 0 and discount_code in codes:
        price_number = price_number - ((codes[discount_code] * price_number) // 100)
        embed_info = discord.Embed(title="Mythical Invoice Generated !", color=0xD4485C)
        embed_info.add_field(name=f"Discount code: {discount_code}", value=f"{codes[discount_code]}%")
    else:
        embed_info = discord.Embed(title="Invoice Created", color=0xD4485C)
    await ctx.send("Processing order...",delete_after=0)
    userid = "fableproxies" + str(ctx.author.id)
    # Creating Customer Object
    r = requests.post(stripeURL + "/v1/customers", headers=stripe_auth, data={"name":userid, "email":"test@testtt.com"})
    print(r.text)
    customerid = r.json()["id"]
    # Create a new product
    product = requests.post(stripeURL + "/v1/products", headers=stripe_auth, data={"name":str(userid)})
    print(product.json())
    # Create a price item
    # product_data = {"name" : "random"}
    price = requests.post(stripeURL + "/v1/prices", headers=stripe_auth, data={"unit_amount" : price_number, "currency" : "usd", "product" : product.json()["id"]})
    print(price.json())
    # Create an invoice item and set the price item
    requests.post(stripeURL + "/v1/invoiceitems", headers=stripe_auth, data={"customer" : customerid, "price" : price.json()["id"]})
    # Create an invoice
    invoice = requests.post(stripeURL + "/v1/invoices", headers=stripe_auth,data={"customer":customerid, "collection_method":"send_invoice", "days_until_due":1})
    print(invoice.text)
    # Send the Invoice
    info = requests.post(stripeURL + "/v1/invoices/" + invoice.json()["id"] + "/send", headers=stripe_auth)
    # Get the invoice link in the response and sending it
    print(info.text)
    
    embed_info.add_field(name="Data", value=str(quantity) + "GBs", inline=False)

    embed_info.add_field(name="Cost Of Data", value="$" + str(int(price_number) / 100), inline=False)
    #embed_info.add_field(name="How to Pay", value="Click the link below to pay for your proxies", inline=False)
    embedVar = discord.Embed(title="Pay Here", url=info.json()["hosted_invoice_url"], color=0xD4485C)
    #embedVar.set_thumbnail(url="https://i.ibb.co/wzvQ62C/mythical-small-remake.png")
    embedVar.set_footer(text="Mythical Proxies", icon_url="https://i.ibb.co/wzvQ62C/mythical-small-remake.png")
    
    await ctx.send(embed=embed_info)
    await ctx.send(embed=embedVar)
    # Store the info to check it after
    with open("customersids.json", "r") as CIDs:
        Customers = json.load(CIDs)
    if str(userid) in Customers:
        Customers.pop(str(userid))
    Customers[userid] = [invoice.json()["id"], int(200 * quantity)]
    with open("customersids.json", "w") as CIDs:
        json.dump(Customers,CIDs,indent=4)

    #except Exception:
    #    await ctx.send("Please use only whole numbers")
    #await ctx.send(info.json()["paid"])
    #await ctx.send(invoice.json()["hosted_invoice_url"])


    

@bot.command()
async def generate(ctx, city, quantity):
    # Code : 500 = Sub-user doesn't exist
    with open("countries.json","r") as countriesobj:
        countries = json.load(countriesobj) 

    baseurl = "https://dashboard.iproyal.com/api/residential/reseller/sub-users/"
    AuthToken = {"X-Access-Token" : "", "Content-type" : "application/json"}
    userid = "fableproxies" + str(ctx.author.id)
    if city in countries:
        try: 
            quantity = int(quantity)
            if quantity in [10,100,1000]:
                generate = requests.post(baseurl + "proxies-list", headers=AuthToken, json={"username":userid, "proxy_country":countries[city], "proxy_hostname":"dns", "proxy_ssl":"http", "proxy_sticky": "sticky", "list_format": "hostname:port:username:password", "proxies_list_quantity": quantity})
                print(generate.json())
                if generate.json()["status"] == 200:
                    f = StringIO(newline="\n")
                    #f.write(str(generate.json()["data"]["formatted_proxy_list"]))
                    data = generate.json()["data"]["formatted_proxy_list"]

                    for index,value in enumerate(data):
                        data[index] = value + os.linesep

                        f.write(data[index])
                    f.seek(0)



                    embedVar = discord.Embed(title="Success!", description="The following file will contain all your proxies information", color=0x00FF00)
                    await ctx.send(embed=embedVar)
                    await ctx.send(file=discord.File(f, filename="Proxies.txt"))
                elif generate.json()["status"] == 500:
                    embedVar = discord.Embed(title="Error!", description="Looks like your input for city is invalid or you aren't registered in our system, please make a purchase before generating proxies!", color=0xFF0000)
                    await ctx.send(embed=embedVar)
            else:
                embedVar = discord.Embed(title="Error!", description="Please use 10, 100 or 1000 for quantity", color=0xFF0000)
                await ctx.send(embed=embedVar)
        except Exception:
            embedVar = discord.Embed(title="Error!", description="Please use whole numbers instead of characters", color=0xFF0000)
            await ctx.send(embed=embedVar)
    else:
        await ctx.send("Please use a correct country")

@bot.command(name="list")
async def country_list(ctx):
    countries = "Random, United States, Canada Afghanistan, Albania, Algeria, Argentina, Armenia, Aruba, Australia, Austria, Azerbaijan, Bahamas, Bahrain, Bangladesh, Belarus, Belgium, Bosnia and Herzegovina, Brazil, British Virgin Islands, Brunei, Bulgaria, Cambodia, Cameroon, Canada, Chile, China, Colombia, Costa Rica, Croatia, Cuba, Cyprus, Czechia, Denmark, Dominican Republic, Ecuador, Egypt, El Salvador, Estonia, Ethiopia, Finland, France, Georgia, Germany, Ghana, Greece, Guatemala, Guyana, Hashemite Kingdom of Jordan, Hong Kong, Hungary, India, Indonesia, Iran, Iraq, Ireland, Israel, Italy, Jamaica, Japan, Kazakhstan, Kenya, Kosovo, Kuwait, Latvia, Liechtenstein, Luxembourg, Macedonia, Madagascar, Malaysia, Mauritius, Mexico, Mongolia, Montenegro, Morocco, Mozambique, Myanmar, Nepal, Netherlands, New Zealand, Nigeria, Norway, Oman, Pakistan, Palestine, Panama, Papua New Guinea, Paraguay, Peru, Philippines, Poland, Portugal, Puerto Rico, Qatar, Republic of Lithuania, Republic of Moldova, Romania, Russia, Saudi Arabia, Senegal, Serbia, Seychelles, Singapore, Slovakia, Slovenia, Somalia, South Africa, South Korea, Spain, Sri Lanka, Sudan, Suriname, Sweden, Switzerland, Syria, Taiwan, Tajikistan, Thailand, Trinidad and Tobago, Tunisia, Turkey, Uganda, Ukraine, United Arab Emirates, United Kingdom, United States, Uzbekistan, Venezuela, Vietnam, Zambia"
    embedVar = discord.Embed(title="Available countries", description=countries)
    embedVar.add_field(name="Note", value="Please keep in mind you should use (\"country_name\") around the country in order to work")
    await ctx.send(embed=embedVar)

@bot.event
async def on_message(message):
    if not message.guild:
        await bot.process_commands(message)

@bot.event
async def on_ready():
    bot.loop.create_task(clients_check())
    print("Ready")


bot.run(TOKEN)
