import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging with proper formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Ensures output goes to stdout
    ]
)
logger = logging.getLogger(__name__)

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True  # Für Online/Offline-Status

# Create bot instance (without default help command)
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.event
async def on_ready():
    """Event that runs when the bot is ready"""
    logger.info(f'✅ {bot.user} has connected to Discord!')
    logger.info(f'📊 Bot is in {len(bot.guilds)} guilds')
    logger.info(f'👥 Serving {len(bot.users)} users')
    
    # Set bot status
    activity = discord.Game(name="Pokemon Trading | !help | !bieten")
    await bot.change_presence(activity=activity)
    
    # Log loaded cogs
    logger.info(f'🔧 Loaded cogs: {list(bot.cogs.keys())}')
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        logger.info(f'✅ Synced {len(synced)} slash command(s)')
    except Exception as e:
        logger.error(f'❌ Failed to sync slash commands: {e}')

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found! Use `!help` to see available commands.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required argument! Check `!help` for usage.")
    else:
        logger.error(f"An error occurred: {error}")

@bot.command(name='ping')
async def ping(ctx):
    """Check bot latency"""
    latency = round(bot.latency * 1000)
    await ctx.send(f'Pong! Latency: {latency}ms')
    await ctx.message.delete()

@bot.command(name='help')
async def help_command(ctx):
    """Zeige alle verfügbaren Befehle"""
    embed = discord.Embed(
        title="🎮 Pokemon Trade Bot - Hilfe",
        description="Willkommen beim Pokemon Trading Bot! Hier sind alle verfügbaren Befehle:",
        color=0x3498db
    )
    
    # Pokemon Trading Befehle
    embed.add_field(
        name="🔥 Pokemon-Trading",
        value=(
            "`!bieten` - Biete ein Pokemon zum Tausch an\n"
            "`!angebote` - Zeige alle verfügbaren Angebote\n"
            "`!wünschen` - Erstelle einen Pokemon-Wunsch\n"
            "`!wünsche` - Zeige alle Pokemon-Wünsche"
        ),
        inline=False
    )
    
    # TCG Trading Befehle (Slash Commands)
    embed.add_field(
        name="🎴 TCG-Karten Trading (Slash Commands)",
        value=(
            "`/anbieten-tcg` - Biete eine Pokemon TCG-Karte zum Tausch an\n"
            "`/wünschen-tcg` - Erstelle einen Wunsch für eine Pokemon TCG-Karte\n"
            "\n*TCG-Commands nutzen echte Kartendaten aus der TCGdx API*"
        ),
        inline=False
    )
    
    # Hilfe & Feedback
    embed.add_field(
        name="💬 Hilfe & Feedback",
        value=(
            "`!pokemon_help` - Detaillierte Pokemon-System Hilfe\n"
            "`!fehler` - Melde einen Fehler im Bot\n"
            "`!ideen` - Schlage eine neue Idee vor\n"
            "`!help` - Zeige diese Hilfe"
        ),
        inline=False
    )
    
    embed.set_footer(
        text=f"Bot erstellt für Pokemon-Trading | Prefix: ! | Latenz: {round(bot.latency * 1000)}ms",
        icon_url=bot.user.avatar.url if bot.user.avatar else None
    )
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass  # Ignoriere Fehler beim Löschen der Nachricht

@bot.command(name='admin_help')
@commands.has_permissions(administrator=True)
async def admin_help_command(ctx):
    """Zeige Admin-Befehle und erweiterte Informationen"""
    embed = discord.Embed(
        title="🔧 Admin-Hilfe",
        description="Erweiterte Befehle und Informationen für Administratoren",
        color=0xe74c3c
    )
    
    # Bot Information
    embed.add_field(
        name="ℹ️ Bot Information",
        value=(
            "`!info` - Zeige Bot-Statistiken\n"
            "`!ping` - Prüfe Bot-Latenz\n"
            "`!admin_help` - Zeige diese Admin-Hilfe"
        ),
        inline=False
    )
    
    # Admin Befehle
    embed.add_field(
        name="🔧 Admin-Befehle",
        value=(
            "`!test_fehler_kanal` - Teste Fehler-Kanal Konfiguration\n"
            "`!user` - Zeige alle User auf dem Server"
        ),
        inline=False
    )
    
    # Nützliche Links & Tipps
    embed.add_field(
        name="🔗 Nützliche Informationen",
        value=(
            "• Fehler-Meldungen gehen an den konfigurierten Kanal\n"
            "• Ideen-Vorschläge werden ebenfalls weitergeleitet\n"
            "• Bot-Status kann in der Konsole überwacht werden"
        ),
        inline=False
    )
    
    # Statistiken
    embed.add_field(
        name="📊 Live-Statistiken",
        value=(
            f"**Server:** {len(bot.guilds)}\n"
            f"**Benutzer:** {len(bot.users)}\n"
            f"**Latenz:** {round(bot.latency * 1000)}ms"
        ),
        inline=False
    )
    
    embed.set_footer(
        text=f"Nur für Administratoren | Bot ID: {bot.user.id}",
        icon_url=bot.user.avatar.url if bot.user.avatar else None
    )
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass

@bot.command(name='user')
@commands.has_permissions(administrator=True)
async def list_users(ctx):
    """Zeige alle User auf dem Server (nur für Admins)"""
    guild = ctx.guild
    
    if not guild:
        await ctx.send("Dieser Befehl kann nur auf einem Server verwendet werden!")
        return
    
    # Sortiere User nach Namen
    members = sorted(guild.members, key=lambda m: m.name.lower())
    
    # Filtere Bots aus (nur Menschen zeigen)
    humans = [m for m in members if not m.bot]
    bots = [m for m in members if m.bot]
    
    embed = discord.Embed(
        title=f"👥 User-Liste - {guild.name}",
        description=f"Insgesamt **{len(humans)}** Menschen auf diesem Server",
        color=0x3498db
    )
    
    # Statistiken über Menschen
    online_humans = [m for m in humans if m.status != discord.Status.offline]
    offline_humans = [m for m in humans if m.status == discord.Status.offline]
    
    # Statistiken
    embed.add_field(
        name="📊 Statistiken",
        value=(
            f"👤 Menschen: **{len(humans)}**\n"
            f"🤖 Bots: **{len(bots)}** (versteckt)\n"
            f"🟢 Online: **{len(online_humans)}**\n"
            f"⚫ Offline: **{len(offline_humans)}**"
        ),
        inline=False
    )
    
    # Zeige nur Menschen in der User-Liste (maximal 15 pro Nachricht)
    user_list = []
    for i, member in enumerate(humans[:15], 1):
        status_emoji = "🟢" if member.status != discord.Status.offline else "⚫"
        user_list.append(f"{status_emoji} {member.name} ({member.mention})")
    
    if user_list:
        embed.add_field(
            name=f"👥 Echte User (Zeige {min(15, len(humans))} von {len(humans)})",
            value="\n".join(user_list),
            inline=False
        )
    
    if len(humans) > 15:
        embed.add_field(
            name="ℹ️ Hinweis",
            value=f"Es werden nur die ersten 15 User angezeigt. Insgesamt gibt es {len(humans)} Menschen.",
            inline=False
        )
    
    embed.set_footer(
        text=f"Server ID: {guild.id} | Abgefragt von {ctx.author.name}",
        icon_url=guild.icon.url if guild.icon else None
    )
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass

@bot.command(name='info')
async def info(ctx):
    """Display bot information"""
    embed = discord.Embed(
        title="🎮 Pokemon Trading Bot",
        description="Ein Discord Bot für Pokemon-Tausch mit discord.py erstellt",
        color=0x00ff00
    )
    embed.add_field(name="Server Count", value=len(bot.guilds), inline=True)
    embed.add_field(name="User Count", value=len(bot.users), inline=True)
    embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.set_footer(text=f"Bot ID: {bot.user.id}")
    
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass

# Load cogs
async def load_cogs():
    """Load all cogs from the cogs directory"""
    cogs_dir = os.path.join(os.path.dirname(__file__), 'cogs')
    
    if not os.path.exists(cogs_dir):
        logger.warning("Cogs directory not found, skipping cog loading")
        return
    
    for filename in os.listdir(cogs_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                logger.info(f'Loaded cog: {filename}')
            except Exception as e:
                logger.error(f'Failed to load cog {filename}: {e}')

# Main function
async def main():
    """Main function to start the bot"""
    # Check for Discord token
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables!")
        logger.error("Please create a .env file with your Discord bot token")
        logger.error("Example: DISCORD_TOKEN=your_token_here")
        return
    
    # Load cogs
    await load_cogs()
    
    # Start the bot
    try:
        await bot.start(token)
    except discord.LoginFailure:
        logger.error("Invalid Discord token! Please check your .env file")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
