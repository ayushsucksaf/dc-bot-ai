import discord
from discord.ext import commands
from discord import app_commands
import google.generativeai as genai
import json, re

dc_key='ur dc key'
api_key='ur gemini api'
ur_guild_id = 0000 #ur guild id in int format

class MyClient(commands.Bot):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

        try:
            guild = discord.Object(id=ur_guild_id)
            synced = await self.tree.sync(guild=guild) 
            print(f'Synced {len(synced)} commands to guild {guild.id}') #use your specific guild id
            
        except Exception as e:
            print(f'Error syncing commands: {e}')  

    async def on_message(self, message):
        if message.author == self.user:
            return
        
        if message.content.startswith('hello'):
            await message.channel.send(f'hi there {message.author}')

        if message.content.startswith('welcome'):
            await message.channel.send(f'welcome new members')     

intents = discord.Intents.all()
intents.message_content = True
client = MyClient(command_prefix="!", intents=intents)
genai.configure(api_key)
model=genai.GenerativeModel("gemini-2.5-flash") #use whichever model like(gemini-2.5-pro, gemini-2.5-flash-lite)

GUILD_ID = discord.Object(id=ur_guild_id)

@client.tree.command(name="help", description="Guide for using the bot", guild=GUILD_ID)
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message('This will be available soon')

@client.tree.command(name="serverinfo", description="Information about the server", guild=GUILD_ID)
async def svrinfo(interaction: discord.Interaction):
    guild = interaction.guild
    role_count = len(interaction.guild.roles)
    embed = discord.Embed(title="Server Info", color=discord.Color.dark_purple())
    if interaction.guild.icon:
        embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
    else:
        embed.set_author(name=interaction.guild.name)
    embed.add_field(name="Owner", value=interaction.guild.owner.mention)
    embed.add_field(name="Members", value=interaction.guild.member_count)
    embed.add_field(name="Roles", value=role_count)
    embed.add_field(name="Age", value=interaction.guild.created_at.strftime("%A, %B %dth %Y %I:%M %p"), inline=False)
    embed.add_field(name=" ", value=" ", inline=False)
    await interaction.response.send_message(embed=embed)

@client.tree.command(name="ai", description="Ask ai", guild=GUILD_ID)
async def generate(interaction: discord.Interaction,* , prompt: str):
    await interaction.response.defer()

    try:
        response = model.generate_content('you are a discord bot which is desinged as an agentic ai to help people, your name is Kami, answer like a human, dont answer too long, be precise, deny if request is out of your permissions and avoid technical stuff'+prompt)
        await interaction.followup.send(response.text)
    except Exception as e:
        await interaction.followup.send(f"Error {e}")

SAFE_METHODS={
    'create_text_channel',
    'create_voice_channel',
    'create_category_channel',
    'create_category',
    'get_member',
    "kick", "ban", "unban",
    "purge",
}


@client.tree.command(name="agent", description="Ask AI to do something", guild=GUILD_ID)
async def ai_command(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer()
    try:
        response = model.generate_content(f"""
        You are a Discord automation bot.
        Return a JSON object with:
        - "method": Discord method to call on the guild
        - "args": dictionary of arguments
        Example:
        {{"method": "create_text_channel", "args": {{"name": "study"}}}}
        Only use safe actions like creating channels, renaming, or listing members.
        User request: {prompt}
        """)

        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        data = json.loads(match.group(0))

        method = data.get("method")
        args = data.get("args", {})

        if method not in SAFE_METHODS:
            await interaction.followup.send(f"❌ Not allowed to call '{method}'")
            return

        func = getattr(interaction.guild, method)
        result = await func(**args)
        await interaction.followup.send(f"✅ Successfully ran {method} with {args}")

    except Exception as e:
        await interaction.followup.send(f"Error: {e}")

client.run(dc_key)