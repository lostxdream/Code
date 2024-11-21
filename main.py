import discord
from discord.ext import commands, tasks
import nacl
import datetime
from asyncio import TimeoutError
import yt_dlp as youtube_dl
import asyncio
import ffmpeg
import logging
import pytz
import aiohttp
from dotenv import load_dotenv
import random
import requests
import time
from discord.utils import get
import os
import subprocess
import platform
import shutil

load_dotenv()
TOKEN = os.getenv('TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="*", intents=intents)


@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.dnd,
                              activity=discord.Game("made by dream.io"))
    print(f'Logged in as {bot.user}!')


#RECEIVE DM
msg_dump_channel = 1306322363599556668


@bot.event
async def on_message(message: discord.Message):
    channel = bot.get_channel(1306322363599556668)
    if message.guild is None and not message.author.bot:

        await channel.send(message.content + f" - {message.author}")
    await bot.process_commands(message)


#WELCOME MESSAGE
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(1058304187571650570)
    await channel.send(
        f"{member.mention}Welcome To The Server 😊. Have a gread day ahead! ")


#GENERAL COMMANDS
#hi
@bot.command()
async def hi(ctx):
    await ctx.send('Hi!')


#ping
@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)  # in milliseconds
    await ctx.send(f"Ping: {latency}ms")


#remind_me
@bot.command(name="remindme")
async def remindme(ctx, minutes: int, *, reminder: str):
    await ctx.send(f"Reminder set for {minutes} minutes.")
    await asyncio.sleep(minutes * 60)
    await ctx.send(f"Hey {ctx.author}, here is your reminder: {reminder}")


#join_voice_channel
@bot.command()
async def join(ctx):
    channel = ctx.author.voice.channel
    await channel.connect()
    if not channel:
        ctx.send("You are not in a voice channel ")
        return


#leave_voice_channel
@bot.command()
async def leave(ctx):
    await ctx.voice_client.disconnect()
    if not ctx.voice_client:
        ctx.send("I am not in a voice channel")
        return


#SPAM
@bot.command(name='spam')
async def spam(ctx, amount: int, *, message):
    for i in range(amount):
        await ctx.send(message)


#EMBED
@bot.command()
async def embed(ctx):
    # Get the guild (server) where the command was invoked
    guild = ctx.guild

    # Create an Embed object
    embed = discord.Embed(
        title="Welcome to the Server!",
        description=".",
        color=discord.Color.blue()  # Change color to green
    )

    # Add fields to the embed
    embed.add_field(name="None", value="None", inline=False)
    embed.add_field(name="None", value="None", inline=True)

    # Add a footer
    embed.set_footer(text="dream.io")

    # Set the thumbnail to the server banner (if available)
    if guild.banner:
        embed.set_thumbnail(url=ctx.guild.banner)
    else:
        # If the server does not have a banner, set the thumbnail to the server's icon
        embed.set_thumbnail(url=guild.banner)

    # Send the embed to the same channel where the command was issued
    await ctx.send(embed=embed)


#MODERATION COMMANDS
#purge
@bot.command(purge=True)
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)


#kick
@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f'{member} has been kicked for: {reason}')


#ban
@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f'{member} has been banned for: {reason}')


#mute
@bot.command(name="mute")
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, *, reason=None):
    mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not mute_role:
        mute_role = await ctx.guild.create_role(
            name="Muted",
            permissions=discord.Permissions(send_messages=False, speak=False))
        for channel in ctx.guild.text_channels:
            await channel.set_permissions(mute_role, send_messages=False)
        for channel in ctx.guild.voice_channels:
            await channel.set_permissions(mute_role, speak=False)
    await member.add_roles(mute_role, reason=reason)
    await ctx.send(f'{member} has been muted. Reason: {reason}')


#unmute
@bot.command(name="unmute")
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if mute_role in member.roles:
        await member.remove_roles(mute_role)
        await ctx.send(f'{member} has been unmuted.')
    else:
        await ctx.send(f'{member} is not muted.')


#addrole
@bot.command(pass_context=True)
@commands.has_permissions(manage_roles=True)
async def giverole(ctx, user: discord.Member, role: discord.Role):
    await user.add_roles(role)
    await ctx.send(f"{ctx.author.name} gave {user.mention} {role.id} role.")


#removerole
@bot.command(pass_context=True)
@commands.has_permissions(manage_roles=True)
async def removerole(ctx, user: discord.Member, role: discord.Role):
    await user.remove_roles(role)
    await ctx.send(f"{ctx.author.name} removed{user.mention} {role.name} role."
                   )


#warn
warnings = {}


@bot.command(name="warn")
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason=None):
    if member.id not in warnings:
        warnings[member.id] = 1
    else:
        warnings[member.id] += 1

    await ctx.send(
        f"{member} has been warned. Reason: {reason}. Total warnings: {warnings[member.id]}"
    )

    if warnings[member.id] >= 3:
        await member.kick(reason="Exceeded warning limit.")
        await ctx.send(
            f"{member} has been kicked for exceeding the warning limit.")
        warnings[member.id] = 0


#clear_warns
@bot.command(name="clearwarns")
@commands.has_permissions(manage_messages=True)
async def clearwarns(ctx, member: discord.Member):
    if member.id in warnings:
        del warnings[member.id]
        await ctx.send(f"Warnings cleared for {member}.")
    else:
        await ctx.send(f"{member} has no warnings.")


#slowmode
@bot.command(name="slowmode")
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int):
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(f"Slowmode has been set to {seconds} seconds.")


#clear
@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1
                            )  # +1 to delete the command message itself
    await ctx.send(f"Deleted {amount} messages.", delete_after=3)


@bot.command()
async def announce(ctx, channel: discord.TextChannel, *, message: str):
    """
    Command to announce a message in a specific channel.
    Usage: !announce #channel Your announcement message
    """
    # Send the message to the specified channel
    await channel.send(message)
    await ctx.send(f'Announcement made in {channel.mention}.')


#ADMINISTRATION
#dm_members
@bot.command()
@commands.has_permissions(administrator=True)
async def dm(ctx, user: discord.User, *, message):
    try:
        await user.send(message)
        await ctx.send(f'DM sent to {user.id}')
    except discord.Forbidden:
        await ctx.send(f'Could not send DM to {user}')


#eval - ⚠️
@bot.command(name="eval")
@commands.is_owner()
async def _eval(ctx, *, code: str):
    try:
        result = eval(code)
        await ctx.send(f"Result: {result}")
    except Exception as e:
        await ctx.send(f"Error: {e}")


#restart
@bot.command(name="restart")
@commands.is_owner()
async def restart(ctx):
    await ctx.send("Restarting bot...")
    os.execv(sys.executable, ['python'] + sys.argv)


#uptime - ⚠️
@bot.command(name="uptime")
async def uptime(ctx):
    elapsed_time = datetime.time() - start_time
    seconds = int(elapsed_time % 60)
    minutes = int((elapsed_time // 60) % 60)
    hours = int((elapsed_time // 3600) % 24)
    days = int(elapsed_time // 86400)
    await ctx.send(
        f"Bot has been up for {days} days, {hours} hours, {minutes} minutes, {seconds} seconds."
    )


#shutdown
@bot.command(name="shutdown")
@commands.is_owner()
async def shutdown(ctx):
    await ctx.send("Shutting down...")
    await bot.close()


#set_prefix
@bot.command(name="setprefix")
@commands.is_owner()
async def setprefix(ctx, prefix: str):
    bot.command_prefix = prefix
    await ctx.send(f"Prefix has been changed to `{prefix}`")


#FUN COMMANDS
#weather
@bot.command(name="weather")
async def weather(ctx, *, city: str):
    api_key = "YOUR_OPENWEATHER_API_KEY"  # Replace with your own OpenWeather API key
    base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    response = requests.get(base_url)
    data = response.json()

    if data["cod"] == 200:
        city_name = data["name"]
        temp = data["main"]["temp"]
        weather_desc = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]

        await ctx.send(
            f"Weather in {city_name}:\nTemperature: {temp}°C\nDescription: {weather_desc}\nHumidity: {humidity}%\nWind Speed: {wind_speed} m/s"
        )
    else:
        await ctx.send("City not found. Please try again.")


#poll
@bot.command(name="poll")
async def poll(ctx, question: str, option1: str, option2: str):
    embed = discord.Embed(title=question,
                          description=f"1️⃣ {option1}\n2️⃣ {option2}",
                          color=discord.Color.green())
    message = await ctx.send(embed=embed)
    await message.add_reaction("1️⃣")
    await message.add_reaction("2️⃣")


#rock_paper_scissors
@bot.command(name="rps")
async def rps(ctx, choice):
    choices = ['rock', 'paper', 'scissors']
    if choice not in choices:
        await ctx.send(
            "Invalid choice! Please choose either rock, paper, or scissors.")
        return

    bot_choice = random.choice(choices)
    if choice == bot_choice:
        await ctx.send(f"Both chose {choice}. It's a tie!")
    elif (choice == 'rock' and bot_choice == 'scissors') or \
         (choice == 'scissors' and bot_choice == 'paper') or \
         (choice == 'paper' and bot_choice == 'rock'):
        await ctx.send(f"You win! I chose {bot_choice}.")
    else:
        await ctx.send(f"You lose! I chose {bot_choice}.")


#8_ball
@bot.command(name="8ball")
async def eight_ball(ctx, *, question):
    responses = [
        "Yes", "No", "Maybe", "Definitely", "I don't know", "Ask again later",
        "Absolutely", "Not likely", "Without a doubt"
    ]
    answer = random.choice(responses)
    await ctx.send(f'Question: {question}\nAnswer: {answer}')


#flip
@bot.command(name="flip")
async def flip(ctx):
    result = random.choice(["Heads", "Tails"])
    await ctx.send(f"The coin landed on: {result}")


#trivia - ⚠️
@bot.command(name="trivia")
async def trivia(ctx):
    questions = [{
        "question": "What is the capital of France?",
        "answer": "Paris"
    }, {
        "question": "Who developed the theory of relativity?",
        "answer": "Einstein"
    }, {
        "question": "What is the largest planet in our solar system?",
        "answer": "Jupiter"
    }]
    question = random.choice(questions)
    await ctx.send(f"Trivia Question: {question['question']}")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        answer = await bot.wait_for('message', timeout=30.0, check=check)
        if answer.content.lower() == question["answer"].lower():
            await ctx.send("Correct! 🎉")
        else:
            await ctx.send(
                f"Wrong answer! The correct answer was {question['answer']}.")
    except TimeoutError:
        await ctx.send(
            f"Time's up! The correct answer was {question['answer']}.")


#UTILITY COMMANDS
#invite
@bot.command(name="invite")
async def invite(ctx):
    invite_link = discord.utils.oauth_url(bot.user.id)
    await ctx.send(f"Click [here]({invite_link}) to invite me to your server!")


#bot_info
@bot.command(name="botinfo")
async def botinfo(ctx):
    embed = discord.Embed(title="Bot Information", color=discord.Color.green())
    embed.add_field(name="Bot Name", value=bot.user.name)
    embed.add_field(name="Bot ID", value=bot.user.id)
    embed.add_field(name="Created On",
                    value=bot.user.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    await ctx.send(embed=embed)


#server_info - ⚠️
@bot.command(name="serverinfo")
async def serverinfo(ctx):
    guild = ctx.guild
    owner = guild.owner
    member_count = guild.member_count
    server_name = guild.name
    creation_date = guild.created_at.strftime("%Y-%m-%d %H:%M:%S")
    await ctx.send(
        f"Server Name: {server_name}\nOwner: {owner}\nMembers: {member_count}\nCreated on: {creation_date}"
    )
    (embed == embed)


#user_info
@bot.command(name="userinfo")
async def userinfo(ctx, member: discord.Member = None):
    if not member:
        member = ctx.author

    embed = discord.Embed(title=f"{member}'s Info", color=discord.Color.blue())
    embed.add_field(name="Username", value=member.name)
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Joined",
                    value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"))
    embed.add_field(name="Account Created",
                    value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    await ctx.send(embed=embed)


#view pfp
@bot.command()
async def avatar(ctx, member: discord.Member = None):
    """Displays the avatar of a user."""
    if member is None:
        member = ctx.author  # Use the author's avatar if no member is mentioned

    avatar_url = member.avatar.url  # Get the avatar URL
    await ctx.send(f"{member.avatar.url}")


# Command to send DM to a user
@bot.command()
async def send_dm(ctx, user: discord.User, *, message: str):
    try:
        # Send a DM to the specified user
        await user.send(message)
        await ctx.send(f"Sent DM to {user.name}")
    except discord.Forbidden:
        await ctx.send(
            f"Could not send a DM to {user.name}. They might have DMs disabled."
        )
    except discord.HTTPException as e:
        await ctx.send(f"An error occurred while trying to send the DM: {e}")


# Configure yt-dlp options
ydl_opts = {
    'format': 'bestaudio/best',
    'extractaudio': True,  # Extract audio only
    'audioquality': 1,  # Best audio quality
    'outtmpl': 'downloads/%(id)s.%(ext)s',  # Save the audio file
    'restrictfilenames': True,
    'noplaylist': True,  # Don't download playlists
}


@bot.command()
async def play(ctx, url: str):
    """Play music from a YouTube URL"""
    # Ensure the user is in a voice channel
    if not ctx.author.voice:
        await ctx.send("You need to join a voice channel first!")
        return

    # Connect to the user's voice channel if not already connected
    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()
    elif ctx.voice_client.channel != ctx.author.voice.channel:
        await ctx.voice_client.move_to(ctx.author.voice.channel)

    voice_client = ctx.voice_client

    # Extract audio source URL from YouTube
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info['formats'][0]['url']

    # Play the audio using FFmpeg
    if not voice_client.is_playing():
        voice_client.play(discord.FFmpegPCMAudio(audio_url),
                          after=lambda e: print(f"Finished playing: {e}"))
        await ctx.send(f"Now playing audio from: {url}")
    else:
        await ctx.send(
            "Already playing something! Stop it first using `!stop`.")


@bot.command()
async def stop(ctx):
    """Stop the music and disconnect"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
    await ctx.voice_client.disconnect()
    await ctx.send("Stopped the music and left the voice channel.")


# Error Handling for Commands
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "You do not have the required permissions to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            "Please provide all the required arguments for this command.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(
            "Command not found. Type `*help` to get a list of available commands."
        )
    else:
        await ctx.send(f"An error occurred: {str(error)}")


#BOT RUN
bot.run(os.getenv("TOKEN"))
