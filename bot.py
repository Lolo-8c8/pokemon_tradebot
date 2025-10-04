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

# Create bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    """Event that runs when the bot is ready"""
    logger.info(f'✅ {bot.user} has connected to Discord!')
    logger.info(f'📊 Bot is in {len(bot.guilds)} guilds')
    logger.info(f'👥 Serving {len(bot.users)} users')
    
    # Set bot status
    activity = discord.Game(name="Pokemon Trading | !bieten | !pokemon_help")
    await bot.change_presence(activity=activity)
    
    # Log loaded cogs
    logger.info(f'🔧 Loaded cogs: {list(bot.cogs.keys())}')

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
    await ctx.message.delete()

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
