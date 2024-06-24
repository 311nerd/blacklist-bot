import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import discord.ui
from discord.ui import View, select
import json
import string
import random
import datetime
import pytz
import requests
from fake_useragent import UserAgent, FakeUserAgent
from io import BytesIO
import math
import pycountry
import sys
import asyncio
from selenium import webdriver
from bs4 import BeautifulSoup

load_dotenv()

blacklist_file = 'blacklist.json'

intents = discord.Intents().all()
bot = commands.Bot(command_prefix=f"{os.getenv('BOT_PREFIX')}", intents=intents, help_command=None)

class DeleteButton(View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label='Supprimer', style=discord.ButtonStyle.red)
    async def delete_message(self, interaction, button):
        await interaction.message.delete()

@bot.event
async def on_ready():
    print(f'Le bot est en ligne: \n username: {bot.user.name} \n id: {bot.user.id}')
    activity = discord.Streaming(name="By 311", url="https://github.com/311nerd")
    await bot.change_presence(status=discord.Status.idle, activity=activity)

@bot.event
async def on_member_join(member):
    with open(blacklist_file, 'r') as f:
        blacklist_data = json.load(f)
    if str(member.id) in blacklist_data:
        await member.ban(reason=blacklist_data[str(member.id)]['reason'])

@bot.command(name='bl', help='Blacklister un utilisateur')
async def blacklist(ctx, user: discord.User, *, reason: str):
    if ctx.author.guild_permissions.administrator:
        with open(blacklist_file, 'r+') as f:
            blacklist_data = json.load(f)
            blacklist_data[str(user.id)] = {'username': str(user), 'reason': reason}
            f.seek(0)
            json.dump(blacklist_data, f, indent=4)
            f.truncate()
        await ctx.send(f'{user.mention} a été ajouté à la blacklist pour la raison suivante : {reason}')
        for guild in bot.guilds:
            member = guild.get_member(user.id)
            if member:
                await member.ban(reason=reason)
    else:
        await ctx.send('Vous n\'avez pas les permissions nécessaires pour utiliser cette commande.')

@bot.command(name='blacklist', help='Afficher la blacklist')
async def blacklist_list(ctx):
    with open(blacklist_file, 'r') as f:
        blacklist_data = json.load(f)
    if not blacklist_data:
        embed = discord.Embed(title='Blacklist', description=f'*Blacklist Vide*')
        await ctx.send(embed=embed)
        return

    embeds = []
    pages = []
    for i, (user_id, data) in enumerate(blacklist_data.items()):
        if i % 10 == 0:
            if embeds:
                pages.append(embeds)
                embeds = []
            embeds.append(discord.Embed(title='Blacklist', description=f'Liste des utilisateurs dans la blacklist du bot'))
        embed = discord.Embed(title='Blacklist', description=f'Liste des utilisateurs dans la blacklist du bot')
        embed.add_field(name=f'', value=f'Username: `{data["username"]}` Raison: `{data["reason"]}`  (<@{user_id}>)', inline=False)
        embed.set_footer(text=f"Page {len(pages)}/{-(len(blacklist_data)//-10)}")
        embeds[-1].add_field(name=f'', value=f'Username: `{data["username"]}` Raison: `{data["reason"]}`  (<@{user_id}>)', inline=False)

    if embeds:
        pages.append(embeds)

    class BlacklistUI(discord.ui.View):
        def __init__(self, pages):
            super().__init__()
            self.pages = pages
            self.current_page = 0

        @discord.ui.button(label='<', style=discord.ButtonStyle.grey)
        async def previous(self, interaction, button):
            self.current_page -= 1
            if self.current_page < 0:
                self.current_page = len(self.pages) - 1
            await interaction.response.edit_message(embed=self.pages[self.current_page][0])

        @discord.ui.button(label='>', style=discord.ButtonStyle.grey)
        async def next(self, interaction, button):
            self.current_page += 1
            if self.current_page >= len(self.pages):
                self.current_page = 0
            await interaction.response.edit_message(embed=self.pages[self.current_page][0])

    paginator = BlacklistUI(pages)
    msg = await ctx.send(embed=pages[0][0], view=paginator)

@bot.command(name='unbl', help='Déblacklister un utilisateur')
async def unblacklist(ctx, user_id: int):
    if ctx.author.guild_permissions.administrator:
        with open(blacklist_file, 'r+') as f:
            blacklist_data = json.load(f)
            if str(user_id) in blacklist_data:
                del blacklist_data[str(user_id)]
                f.seek(0)
                json.dump(blacklist_data, f, indent=4)
                f.truncate()
                await ctx.send(f'L\'utilisateur {user_id} a été retiré de la blacklist.')
                for guild in bot.guilds:
                    await guild.unban(discord.Object(user_id))
            else:
                await ctx.send('Cet utilisateur n\'est pas dans la blacklist.')
    else:
        await ctx.send('Vous n\'avez pas les permissions nécessaires pour utiliser cette commande.')

bot.run(os.getenv('BOT_TOKEN'))