import discord
from discord.ext import commands
import asyncio
import requests
import json
import os
import sys

from keep_alive import keep_alive
keep_alive()

# Channel and message ID where the items list is stored
CHANNEL_ID = 1201165202465505334
MESSAGE_ID = 1323386764722704506

# Bot setup with intents
intents = discord.Intents.default()
intents.message_content = True  # Required for reading message content
bot = commands.Bot(command_prefix='/', intents=intents)

# Blacklisted user
BLACKLISTED_USER = 'trolo2014'

# T-shirt ID to check
TSHIRT_ID = '17495400349'  # Replace with your T-shirt ID
TSHIRT_URL = f'https://www.roblox.com/catalog/{TSHIRT_ID}'

# Variable to track if the command is being used
is_command_in_use = False

# Get User ID from Username
def get_user_id(username):
    url = "https://users.roblox.com/v1/usernames/users"
    params = {"usernames": [username]}
    try:
        response = requests.post(url, json=params)
        response.raise_for_status()
        data = response.json()
        if data and 'data' in data and len(data['data']) > 0:
            user_id = data['data'][0]['id']
            return user_id
        return None
    except requests.RequestException as e:
        print(f"Error getting user ID: {e}")
        return None

# Check ownership function using User ID
def check_ownership(user_id):
    url = f"https://inventory.roblox.com/v1/users/{user_id}/items/Asset/{TSHIRT_ID}/is-owned"
    try:
        response = requests.get(url)
        response.raise_for_status()
        output = response.json()
        return output == True  # Return True if the entire output is True, else False
    except requests.RequestException:
        return False

# Slash command: account_seller
@bot.tree.command(name="account_purchase", description="Start's the account selling process.")
async def account_seller(interaction: discord.Interaction, username: str):
    global is_command_in_use

    # Prevent the command from being used if it's already in use
    if is_command_in_use:
        await interaction.response.send_message("❌ Somebody Already Uses Command Wait Until It Finishes", ephemeral=True)
        return

    # Set the flag to indicate the command is in use
    is_command_in_use = True

    if username == BLACKLISTED_USER:
        await interaction.response.send_message("❌ nice try cunt", ephemeral=True)
        is_command_in_use = False
        return

    user_id = get_user_id(username)
    if not user_id:
        await interaction.response.send_message("❌ Invalid Roblox username!", ephemeral=True)
        is_command_in_use = False
        return

    embed = discord.Embed(
        title="🛒 Account Seller",
        color=discord.Color.red()
    ).add_field(
        name="Waiting for purchase...",
        value=f"[Click here to buy T-shirt]({TSHIRT_URL})"
    ).add_field(
        name="Time Left:",
        value="5:00"
    ).set_image(url='https://i.imgur.com/n4J7GTC.png')
    await interaction.response.send_message(embed=embed)
    message = await interaction.original_response()

    # Countdown for purchase (5 minutes)
    purchase_detected = False
    for remaining_time in range(300, 0, -1):  # Countdown from 300 seconds (5 minutes)
        await asyncio.sleep(1)
        if check_ownership(user_id):
            # Update embed for purchase detected
            embed.set_field_at(0, name="✅ Purchase Detected!", value="Now Please Remove T-Shirt Which You Purchased , **Below Is (Example) How To Do It**")
            embed.set_image(url='https://i.imgur.com/II8LWKj.gif')
            embed.remove_field(1)  # Remove "Time Left" field after purchase is detected
            await message.edit(embed=embed)
            purchase_detected = True
            break  # Stop countdown immediately

        # Update countdown timer
        minutes, seconds = divmod(remaining_time, 60)
        embed.set_field_at(1, name="Time Left:", value=f"{minutes:02}:{seconds:02}")
        await message.edit(embed=embed)

    if not purchase_detected:
        await interaction.followup.send("❌ Time's up! Purchase was not detected.")
        is_command_in_use = False
        return

    # Wait for user to remove the T-shirt
    while check_ownership(user_id):  # Wait until the user removes the T-shirt
        await asyncio.sleep(1)

    # T-shirt was removed, now check message for items to send
    channel = bot.get_channel(CHANNEL_ID)
    message_to_check = await channel.fetch_message(MESSAGE_ID)
    if message_to_check:
        items_str = message_to_check.content
        try:
            items = json.loads(items_str)["items"]  # Assuming message content is JSON-formatted
        except json.JSONDecodeError:
            items = []

        if items:
            item = items.pop(0)  # Remove the first item from the list
            updated_items = {"items": items}
            await message_to_check.edit(content=json.dumps(updated_items))  # Update the message content with the new list

            await interaction.user.send(f"✅ Here's your item: {item}")
            await interaction.followup.send("✅ T-Shirt removed, item sent via DM!")

        else:
            await interaction.followup.send("❌ No items left to send.")

    # Reset the flag to allow the next person to use the command
    is_command_in_use = False

# Bot Ready Event
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands.")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
        
    # Ensure proper indentation
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        try:
            message = await channel.fetch_message(MESSAGE_ID)
            print(f"Message content: {message.content}")
        except discord.NotFound:
            print("❌ Message not found!")
        except Exception as e:
            print(f"❌ Error fetching message: {e}")


        
bot.run(os.environ.get('DISCORD_BOT_TOKEN'))
