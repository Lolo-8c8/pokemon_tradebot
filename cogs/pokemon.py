import discord
from discord.ext import commands

class TypeSelect(discord.ui.Select):
    """Dropdown für Pokemon-Typ Auswahl"""
    
    def __init__(self, view):
        self.pokemon_view = view
        options = [
            discord.SelectOption(
                label=f"{emoji} {name}", 
                value=name, 
                emoji=emoji
            ) for emoji, name in view.cog.pokemon_types.items()
        ]
        
        super().__init__(
            placeholder="Wähle den Pokemon-Typ...",
            options=options,
            custom_id="type_select"
        )
    
    async def callback(self, interaction: discord.Interaction):
        self.pokemon_view.pokemon_data['type'] = self.values[0]
        await self.pokemon_view.update_embed(interaction)

class PhaseSelect(discord.ui.Select):
    """Dropdown für Pokemon-Phase Auswahl"""
    
    def __init__(self, view):
        self.pokemon_view = view
        options = [
            discord.SelectOption(
                label=f"{emoji} {name}",
                value=name,
                emoji=emoji
            ) for emoji, name in view.cog.pokemon_phases.items()
        ]
        
        super().__init__(
            placeholder="Wähle die Pokemon-Phase...",
            options=options,
            custom_id="phase_select"
        )
    
    async def callback(self, interaction: discord.Interaction):
        self.pokemon_view.pokemon_data['phase'] = self.values[0]
        await self.pokemon_view.update_embed(interaction)

class RaritySelect(discord.ui.Select):
    """Dropdown für Seltenheitsstufe Auswahl"""
    
    def __init__(self, view):
        self.pokemon_view = view
        options = [
            discord.SelectOption(
                label=f"{emoji} {name}",
                value=name,
                emoji=emoji
            ) for emoji, name in view.cog.rarity_levels.items()
        ]
        
        super().__init__(
            placeholder="Wähle die Seltenheitsstufe...",
            options=options,
            custom_id="rarity_select"
        )
    
    async def callback(self, interaction: discord.Interaction):
        self.pokemon_view.pokemon_data['rarity'] = self.values[0]
        await self.pokemon_view.update_embed(interaction)

class Pokemon(commands.Cog):
    """Pokemon Tausch System"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Pokemon-Arten (Typen)
        self.pokemon_types = {
            "🔥": "Feuer",
            "🌊": "Wasser", 
            "⚡": "Elektro",
            "🌿": "Pflanze",
            "👊": "Kampf",
            "💜": "Liebe",
            "🐉": "Drachen",
            "🌙": "Unlicht"
        }
        
        # Pokemon-Phasen
        self.pokemon_phases = {
            "🥚": "Basis",
            "🐣": "Phase 1",
            "🐤": "Phase 2", 
            "🦅": "Phase 3"
        }
        
        # Seltenheitsstufen
        self.rarity_levels = {
            "⚪": "Häufig (Kreis)",
            "🔷": "Nicht so häufig (Raute)",
            "⭐": "Selten (Stern)",
            "🌟": "Doppelselten (Zweisterne)",
            "🏆": "Illustrationskarte (Goldener Stern)"
        }
        
        # Beispiel Pokemon-Namen für Autocomplete
        self.example_pokemon = [
            "Pikachu", "Charizard", "Blastoise", "Venusaur", "Mewtwo", "Mew",
            "Lugia", "Ho-Oh", "Rayquaza", "Kyogre", "Groudon", "Dialga",
            "Palkia", "Giratina", "Arceus", "Reshiram", "Zekrom", "Kyurem",
            "Xerneas", "Yveltal", "Zygarde", "Solgaleo", "Lunala", "Necrozma",
            "Glurak", "Bisaflor", "Turtok", "Relaxo", "Lucario", "Garchomp"
        ]
    
    
    class PokemonNameModal(discord.ui.Modal):
        """Modal für Pokemon-Name und KP-Eingabe"""
        
        def __init__(self, view):
            super().__init__(title="Pokemon Details eingeben")
            self.view = view
            
            self.name_input = discord.ui.TextInput(
                label="Pokemon Name",
                placeholder="z.B. Pikachu, Charizard, etc.",
                required=True,
                max_length=50
            )
            self.add_item(self.name_input)
            
            self.hp_input = discord.ui.TextInput(
                label="KP (Kraftpunkte)",
                placeholder="z.B. 120, 250, etc.",
                required=True,
                max_length=4
            )
            self.add_item(self.hp_input)
        
        async def on_submit(self, interaction: discord.Interaction):
            try:
                hp_value = int(self.hp_input.value)
                if hp_value <= 0:
                    raise ValueError("KP müssen größer als 0 sein")
                
                self.view.pokemon_data['name'] = self.name_input.value
                self.view.pokemon_data['hp'] = hp_value
                self.view.pokemon_data['user'] = interaction.user
                
                # Aktualisiere das Embed mit den neuen Informationen
                await self.view.update_embed(interaction)
                
            except ValueError as e:
                if "invalid literal" in str(e):
                    await interaction.response.send_message("❌ KP müssen eine gültige Zahl sein!", ephemeral=True)
                else:
                    await interaction.response.send_message(f"❌ {str(e)}", ephemeral=True)
    
    
    # Die PokemonOfferView wird jetzt vollständig definiert
    class PokemonOfferViewFull(discord.ui.View):
        """View für das Pokemon-Angebot mit allen Auswahlmöglichkeiten"""
        
        def __init__(self, cog):
            super().__init__(timeout=300)
            self.cog = cog
            self.pokemon_data = {
                'name': None,
                'type': None,
                'hp': None,
                'phase': None,
                'rarity': None,
                'user': None
            }
            
            # Füge alle Select-Komponenten hinzu
            self.add_item(TypeSelect(self))
            self.add_item(PhaseSelect(self))
            self.add_item(RaritySelect(self))
        
        @discord.ui.button(label="📝 Name & KP eingeben", style=discord.ButtonStyle.primary, row=4)
        async def enter_details(self, interaction: discord.Interaction, button: discord.ui.Button):
            _ = button  # Ignoriere unused argument warning
            modal = self.cog.PokemonNameModal(self)
            await interaction.response.send_modal(modal)
        
        @discord.ui.button(label="✅ Angebot bestätigen", style=discord.ButtonStyle.success, row=4)
        async def confirm_offer(self, interaction: discord.Interaction, button: discord.ui.Button):
            _ = button  # Ignoriere unused argument warning
            # Prüfe ob alle Daten vorhanden sind
            missing_fields = []
            if not self.pokemon_data['name']:
                missing_fields.append("Name")
            if not self.pokemon_data['hp']:
                missing_fields.append("KP")
            if not self.pokemon_data['type']:
                missing_fields.append("Typ")
            if not self.pokemon_data['phase']:
                missing_fields.append("Phase")
            if not self.pokemon_data['rarity']:
                missing_fields.append("Seltenheit")
            
            if missing_fields:
                await interaction.response.send_message(
                    f"❌ Bitte fülle alle Felder aus! Fehlend: {', '.join(missing_fields)}", 
                    ephemeral=True
                )
                return
            
            # Erstelle finales Angebot-Embed
            await self.create_final_offer(interaction)
        
        @discord.ui.button(label="❌ Abbrechen", style=discord.ButtonStyle.danger, row=4)
        async def cancel_offer(self, interaction: discord.Interaction, button: discord.ui.Button):
            _ = button  # Ignoriere unused argument warning
            embed = discord.Embed(
                title="❌ Pokemon-Angebot abgebrochen",
                description="Das Angebot wurde abgebrochen.",
                color=0xff0000
            )
            
            # Deaktiviere alle Buttons
            for item in self.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
        
        async def update_embed(self, interaction: discord.Interaction):
            """Aktualisiert das Embed mit den aktuellen Pokemon-Daten"""
            embed = discord.Embed(
                title="🎮 Pokemon-Angebot erstellen",
                description="Wähle die Eigenschaften deines Pokemon aus:",
                color=0x3498db
            )
            
            # Zeige ausgefüllte Felder an
            if self.pokemon_data['name']:
                embed.add_field(
                    name="📛 Name", 
                    value=self.pokemon_data['name'], 
                    inline=True
                )
            
            if self.pokemon_data['hp']:
                embed.add_field(
                    name="❤️ KP", 
                    value=str(self.pokemon_data['hp']), 
                    inline=True
                )
            
            if self.pokemon_data['type']:
                type_emoji = next((emoji for emoji, name in self.cog.pokemon_types.items() if name == self.pokemon_data['type']), "")
                embed.add_field(
                    name="🏷️ Typ", 
                    value=f"{type_emoji} {self.pokemon_data['type']}", 
                    inline=True
                )
            
            if self.pokemon_data['phase']:
                phase_emoji = next((emoji for emoji, name in self.cog.pokemon_phases.items() if name == self.pokemon_data['phase']), "")
                embed.add_field(
                    name="🔄 Phase", 
                    value=f"{phase_emoji} {self.pokemon_data['phase']}", 
                    inline=True
                )
            
            if self.pokemon_data['rarity']:
                rarity_emoji = next((emoji for emoji, name in self.cog.rarity_levels.items() if name == self.pokemon_data['rarity']), "")
                embed.add_field(
                    name="💎 Seltenheit", 
                    value=f"{rarity_emoji} {self.pokemon_data['rarity']}", 
                    inline=True
                )
            
            # Fortschrittsanzeige
            completed_fields = sum(1 for value in [
                self.pokemon_data['name'],
                self.pokemon_data['hp'], 
                self.pokemon_data['type'],
                self.pokemon_data['phase'],
                self.pokemon_data['rarity']
            ] if value is not None)
            
            embed.set_footer(text=f"Fortschritt: {completed_fields}/5 Felder ausgefüllt")
            
            await interaction.response.edit_message(embed=embed, view=self)
        
        async def create_final_offer(self, interaction: discord.Interaction):
            """Erstellt das finale Pokemon-Angebot"""
            
            # Hole die entsprechenden Emojis
            type_emoji = next((emoji for emoji, name in self.cog.pokemon_types.items() if name == self.pokemon_data['type']), "")
            phase_emoji = next((emoji for emoji, name in self.cog.pokemon_phases.items() if name == self.pokemon_data['phase']), "")
            rarity_emoji = next((emoji for emoji, name in self.cog.rarity_levels.items() if name == self.pokemon_data['rarity']), "")
            
            embed = discord.Embed(
                title="🎯 Neues Pokemon-Angebot!",
                description=f"**{self.pokemon_data['user'].display_name}** bietet ein Pokemon zum Tausch an:",
                color=0x00ff00
            )
            
            embed.add_field(
                name="📛 Pokemon",
                value=f"**{self.pokemon_data['name']}**",
                inline=True
            )
            
            embed.add_field(
                name="❤️ KP",
                value=f"**{self.pokemon_data['hp']}**",
                inline=True
            )
            
            embed.add_field(
                name="🏷️ Typ",
                value=f"{type_emoji} **{self.pokemon_data['type']}**",
                inline=True
            )
            
            embed.add_field(
                name="🔄 Phase",
                value=f"{phase_emoji} **{self.pokemon_data['phase']}**",
                inline=True
            )
            
            embed.add_field(
                name="💎 Seltenheit",
                value=f"{rarity_emoji} **{self.pokemon_data['rarity']}**",
                inline=True
            )
            
            embed.add_field(
                name="👤 Anbieter",
                value=self.pokemon_data['user'].mention,
                inline=True
            )
            
            embed.set_thumbnail(url=self.pokemon_data['user'].display_avatar.url)
            embed.set_footer(text="Interessiert? Kontaktiere den Anbieter für einen Tausch!")
            
            # Erstelle neue View für das finale Angebot
            final_view = self.cog.FinalOfferView(self.pokemon_data)
            
            await interaction.response.edit_message(embed=embed, view=final_view)
        
        async def on_timeout(self):
            """Wird aufgerufen wenn die View timeout erreicht"""
            for item in self.children:
                item.disabled = True
    
    class FinalOfferView(discord.ui.View):
        """View für das finale Pokemon-Angebot"""
        
        def __init__(self, pokemon_data):
            super().__init__(timeout=3600)  # 1 Stunde für finale Angebote
            self.pokemon_data = pokemon_data
        
        @discord.ui.button(label="💬 Interesse zeigen", style=discord.ButtonStyle.primary, emoji="💬")
        async def show_interest(self, interaction: discord.Interaction, button: discord.ui.Button):
            _ = button  # Ignoriere unused argument warning
            if interaction.user.id == self.pokemon_data['user'].id:
                await interaction.response.send_message(
                    "❌ Du kannst nicht Interesse an deinem eigenen Angebot zeigen!", 
                    ephemeral=True
                )
                return
            
            # Sende private Nachricht an den Anbieter
            try:
                dm_embed = discord.Embed(
                    title="🔔 Jemand ist interessiert an deinem Pokemon!",
                    description=f"**{interaction.user.display_name}** hat Interesse an deinem **{self.pokemon_data['name']}** gezeigt!",
                    color=0x00ff00
                )
                dm_embed.add_field(
                    name="Kontakt",
                    value=f"Schreibe {interaction.user.mention} eine private Nachricht um den Tausch zu besprechen!",
                    inline=False
                )
                
                await self.pokemon_data['user'].send(embed=dm_embed)
                
                await interaction.response.send_message(
                    f"✅ Ich habe {self.pokemon_data['user'].display_name} über dein Interesse informiert! "
                    f"Sie werden sich bei dir melden.", 
                    ephemeral=True
                )
                
            except discord.Forbidden:
                await interaction.response.send_message(
                    f"❌ Ich konnte {self.pokemon_data['user'].display_name} keine private Nachricht senden. "
                    f"Kontaktiere sie direkt: {self.pokemon_data['user'].mention}",
                    ephemeral=True
                )
        
        @discord.ui.button(label="📊 Details", style=discord.ButtonStyle.secondary, emoji="📊")
        async def show_details(self, interaction: discord.Interaction, button: discord.ui.Button):
            _ = button  # Ignoriere unused argument warning
            details_embed = discord.Embed(
                title=f"📊 Details zu {self.pokemon_data['name']}",
                color=0x3498db
            )
            
            details_embed.add_field(name="Name", value=self.pokemon_data['name'], inline=True)
            details_embed.add_field(name="KP", value=self.pokemon_data['hp'], inline=True)
            details_embed.add_field(name="Typ", value=self.pokemon_data['type'], inline=True)
            details_embed.add_field(name="Phase", value=self.pokemon_data['phase'], inline=True)
            details_embed.add_field(name="Seltenheit", value=self.pokemon_data['rarity'], inline=True)
            details_embed.add_field(name="Anbieter", value=self.pokemon_data['user'].display_name, inline=True)
            
            await interaction.response.send_message(embed=details_embed, ephemeral=True)
    
    @commands.command(name='bieten')
    async def offer_pokemon(self, ctx):
        """Biete ein Pokemon zum Tausch an"""
        
        embed = discord.Embed(
            title="🎮 Pokemon-Angebot erstellen",
            description="Wähle die Eigenschaften deines Pokemon aus:",
            color=0x3498db
        )
        
        embed.add_field(
            name="📝 Anleitung",
            value="1. **Name & KP eingeben** - Klicke den Button um Name und Kraftpunkte einzugeben\n"
                  "2. **Typ wählen** - Wähle den Pokemon-Typ aus dem Dropdown\n"
                  "3. **Phase wählen** - Wähle die Entwicklungsphase\n"
                  "4. **Seltenheit wählen** - Wähle die Seltenheitsstufe\n"
                  "5. **Bestätigen** - Wenn alles ausgefüllt ist, bestätige dein Angebot",
            inline=False
        )
        
        embed.set_footer(text="Fortschritt: 0/5 Felder ausgefüllt")
        
        view = self.PokemonOfferViewFull(self)
        await ctx.send(embed=embed, view=view)
    
    @commands.command(name='pokemon_help')
    async def pokemon_help(self, ctx):
        """Zeigt Hilfe für das Pokemon-Tausch System"""
        
        embed = discord.Embed(
            title="🎮 Pokemon-Tausch System Hilfe",
            description="Hier findest du alle Informationen zum Pokemon-Tausch System:",
            color=0x3498db
        )
        
        embed.add_field(
            name="🎯 Befehle",
            value="`!bieten` - Biete ein Pokemon zum Tausch an\n"
                  "`!pokemon_help` - Zeige diese Hilfe",
            inline=False
        )
        
        # Pokemon-Typen
        types_text = "\n".join([f"{emoji} {name}" for emoji, name in self.pokemon_types.items()])
        embed.add_field(
            name="🏷️ Verfügbare Pokemon-Typen",
            value=types_text,
            inline=True
        )
        
        # Pokemon-Phasen  
        phases_text = "\n".join([f"{emoji} {name}" for emoji, name in self.pokemon_phases.items()])
        embed.add_field(
            name="🔄 Pokemon-Phasen",
            value=phases_text,
            inline=True
        )
        
        # Seltenheitsstufen
        rarity_text = "\n".join([f"{emoji} {name}" for emoji, name in self.rarity_levels.items()])
        embed.add_field(
            name="💎 Seltenheitsstufen",
            value=rarity_text,
            inline=True
        )
        
        embed.add_field(
            name="💡 Tipps",
            value="• Sei ehrlich bei den Pokemon-Daten\n"
                  "• Verwende klare Pokemon-Namen\n"
                  "• KP sollten realistisch sein\n"
                  "• Nutze private Nachrichten für Tauschverhandlungen",
            inline=False
        )
        
        embed.set_footer(text="Viel Spaß beim Pokemon-Tauschen! 🎉")
        
        await ctx.send(embed=embed)

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(Pokemon(bot))
