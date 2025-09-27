import discord
from discord.ext import commands
import asyncio

class Moderation(commands.Cog):
    """Moderation commands for server management"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick_member(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Kick a member from the server"""
        if member == ctx.author:
            await ctx.send("You cannot kick yourself!")
            return
        
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot kick someone with equal or higher role!")
            return
        
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="Member Kicked",
                description=f"{member.mention} has been kicked from the server.",
                color=0xff0000
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I don't have permission to kick this member!")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
    
    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban_member(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Ban a member from the server"""
        if member == ctx.author:
            await ctx.send("You cannot ban yourself!")
            return
        
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot ban someone with equal or higher role!")
            return
        
        try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                title="Member Banned",
                description=f"{member.mention} has been banned from the server.",
                color=0xff0000
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I don't have permission to ban this member!")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
    
    @commands.command(name='unban')
    @commands.has_permissions(ban_members=True)
    async def unban_member(self, ctx, *, member):
        """Unban a member from the server"""
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split('#')
        
        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                embed = discord.Embed(
                    title="Member Unbanned",
                    description=f"{user.mention} has been unbanned from the server.",
                    color=0x00ff00
                )
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
                await ctx.send(embed=embed)
                return
        
        await ctx.send(f"Could not find banned user: {member}")
    
    @commands.command(name='mute')
    @commands.has_permissions(manage_roles=True)
    async def mute_member(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Mute a member (remove ability to send messages)"""
        if member == ctx.author:
            await ctx.send("You cannot mute yourself!")
            return
        
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot mute someone with equal or higher role!")
            return
        
        # Find or create muted role
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted", color=discord.Color.red())
            
            # Set permissions for muted role
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, send_messages=False, speak=False)
        
        try:
            await member.add_roles(muted_role, reason=reason)
            embed = discord.Embed(
                title="Member Muted",
                description=f"{member.mention} has been muted.",
                color=0xffaa00
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
    
    @commands.command(name='unmute')
    @commands.has_permissions(manage_roles=True)
    async def unmute_member(self, ctx, member: discord.Member):
        """Unmute a member"""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            await ctx.send("No muted role found!")
            return
        
        try:
            await member.remove_roles(muted_role)
            embed = discord.Embed(
                title="Member Unmuted",
                description=f"{member.mention} has been unmuted.",
                color=0x00ff00
            )
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
    
    @commands.command(name='clear')
    @commands.has_permissions(manage_messages=True)
    async def clear_messages(self, ctx, amount: int = 5):
        """Clear a specified number of messages"""
        if amount < 1 or amount > 100:
            await ctx.send("Please specify a number between 1 and 100!")
            return
        
        try:
            deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message
            embed = discord.Embed(
                title="Messages Cleared",
                description=f"Deleted {len(deleted)} messages.",
                color=0x00ff00
            )
            await ctx.send(embed=embed, delete_after=5)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
    
    @commands.command(name='warn')
    @commands.has_permissions(manage_messages=True)
    async def warn_member(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Warn a member"""
        if member == ctx.author:
            await ctx.send("You cannot warn yourself!")
            return
        
        embed = discord.Embed(
            title="⚠️ Warning",
            description=f"{member.mention} has been warned.",
            color=0xffaa00
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
        
        await ctx.send(embed=embed)
        
        # Try to send DM to the warned member
        try:
            dm_embed = discord.Embed(
                title="⚠️ You have been warned",
                description=f"You have been warned in **{ctx.guild.name}**",
                color=0xffaa00
            )
            dm_embed.add_field(name="Reason", value=reason, inline=False)
            dm_embed.add_field(name="Moderator", value=ctx.author.display_name, inline=False)
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass  # User has DMs disabled

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(Moderation(bot))
