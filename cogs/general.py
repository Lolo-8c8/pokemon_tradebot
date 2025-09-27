import discord
from discord.ext import commands
import random
import asyncio

class General(commands.Cog):
    """General purpose commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='hello')
    async def hello(self, ctx):
        """Say hello to the bot"""
        await ctx.send(f'Hello {ctx.author.mention}! 👋')
    
    @commands.command(name='8ball')
    async def eight_ball(self, ctx, *, question):
        """Ask the magic 8-ball a question"""
        responses = [
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes - definitely.",
            "You may rely on it.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful."
        ]
        
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            description=f"**Question:** {question}\n**Answer:** {random.choice(responses)}",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='roll')
    async def roll_dice(self, ctx, sides: int = 6):
        """Roll a dice with specified number of sides (default: 6)"""
        if sides < 2:
            await ctx.send("Dice must have at least 2 sides!")
            return
        
        result = random.randint(1, sides)
        await ctx.send(f"🎲 You rolled a **{result}** on a {sides}-sided die!")
    
    @commands.command(name='choose')
    async def choose(self, ctx, *, choices):
        """Choose randomly from given options"""
        options = [choice.strip() for choice in choices.split(',')]
        
        if len(options) < 2:
            await ctx.send("Please provide at least 2 options separated by commas!")
            return
        
        chosen = random.choice(options)
        
        embed = discord.Embed(
            title="🎯 Random Choice",
            description=f"I choose: **{chosen}**",
            color=0x00ff00  # Green color
        )
        embed.set_footer(text=f"From {len(options)} options - Hot Reload Test!")
        
        await ctx.send(embed=embed)
    
    class CoinflipView(discord.ui.View):
        """View for coinflip buttons"""
        
        def __init__(self, bot_instance):
            super().__init__(timeout=60)
            self.bot_instance = bot_instance
        
        @discord.ui.button(label="🪙 Kopf", style=discord.ButtonStyle.primary, emoji="🪙")
        async def kopf_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.handle_choice(interaction, "kopf")
        
        @discord.ui.button(label="🪙 Zahl", style=discord.ButtonStyle.secondary, emoji="🪙")
        async def zahl_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.handle_choice(interaction, "zahl")
        
        async def handle_choice(self, interaction: discord.Interaction, user_choice: str):
            """Handle the coinflip logic"""
            # Bot's random choice
            bot_choice = random.choice(['kopf', 'zahl'])
            
            # Determine result
            won = user_choice == bot_choice
            
            # Create embed
            embed = discord.Embed(
                title="🪙 Coinflip Result",
                color=0x00ff00 if won else 0xff0000
            )
            
            # Add result fields
            embed.add_field(
                name="Your Choice", 
                value=f"**{user_choice.title()}**", 
                inline=True
            )
            embed.add_field(
                name="Bot's Choice", 
                value=f"**{bot_choice.title()}**", 
                inline=True
            )
            embed.add_field(
                name="Result", 
                value=f"**{'🎉 You Won!' if won else '😢 You Lost!'}**", 
                inline=False
            )
            
            # Add emoji based on result
            result_emoji = "🎉" if won else "😢"
            embed.set_footer(text=f"{result_emoji} {'Congratulations!' if won else 'Better luck next time!'}")
            
            # Disable buttons after use
            for item in self.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
        
        async def on_timeout(self):
            """Handle timeout"""
            for item in self.children:
                item.disabled = True

    @commands.command(name='coinflip')
    async def coinflip(self, ctx):
        """Flip a coin! Choose 'kopf' or 'zahl' with buttons"""
        embed = discord.Embed(
            title="🪙 Coinflip",
            description="Click a button to choose your side!",
            color=0xffd700
        )
        embed.add_field(
            name="How it works:",
            value="• Click **Kopf** for heads\n• Click **Zahl** for tails\n• Bot will flip randomly\n• See if you win!",
            inline=False
        )
        
        view = self.CoinflipView(self)
        await ctx.send(embed=embed, view=view)
    
    @commands.command(name='poll')
    async def poll(self, ctx, *, question):
        """Create a simple yes/no poll"""
        embed = discord.Embed(
            title="📊 Poll",
            description=question,
            color=0x00ff00
        )
        embed.set_footer(text=f"Poll created by {ctx.author.display_name}")
        
        message = await ctx.send(embed=embed)
        await message.add_reaction("✅")  # Yes
        await message.add_reaction("❌")  # No
    
    @commands.command(name='avatar')
    async def avatar(self, ctx, member: discord.Member = None):
        """Get a user's avatar"""
        if member is None:
            member = ctx.author
        
        embed = discord.Embed(
            title=f"{member.display_name}'s Avatar",
            color=member.color
        )
        embed.set_image(url=member.avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='serverinfo')
    async def server_info(self, ctx):
        """Display server information"""
        guild = ctx.guild
        
        embed = discord.Embed(
            title=f"Server Information: {guild.name}",
            color=0x00ff00
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Emojis", value=len(guild.emojis), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(General(bot))
