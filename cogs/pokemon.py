import discord
from discord.ext import commands

class TypeSelect(discord.ui.Select):
    """Dropdown für Pokemon-Typ Auswahl"""
    
    def __init__(self, view):
        self.pokemon_view = view
        options = [
            discord.SelectOption(
                label=name, 
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
        # Bestimme welcher Datencontainer verwendet wird
        if hasattr(self.pokemon_view, 'pokemon_data'):
            self.pokemon_view.pokemon_data['type'] = self.values[0]
        elif hasattr(self.pokemon_view, 'wish_data'):
            self.pokemon_view.wish_data['type'] = self.values[0]
        
        # Gehe automatisch zum nächsten Schritt (Phase)
        await self.pokemon_view.show_phase_selection(interaction)

class PhaseSelect(discord.ui.Select):
    """Dropdown für Pokemon-Phase Auswahl"""
    
    def __init__(self, view):
        self.pokemon_view = view
        options = [
            discord.SelectOption(
                label=name,
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
        # Bestimme welcher Datencontainer verwendet wird
        if hasattr(self.pokemon_view, 'pokemon_data'):
            self.pokemon_view.pokemon_data['phase'] = self.values[0]
        elif hasattr(self.pokemon_view, 'wish_data'):
            self.pokemon_view.wish_data['phase'] = self.values[0]
        
        # Gehe automatisch zum nächsten Schritt (Seltenheit)
        await self.pokemon_view.show_rarity_selection(interaction)

class RaritySelect(discord.ui.Select):
    """Dropdown für Seltenheitsstufe Auswahl"""
    
    def __init__(self, view):
        self.pokemon_view = view
        options = [
            discord.SelectOption(
                label=name,
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
        # Bestimme welcher Datencontainer verwendet wird
        if hasattr(self.pokemon_view, 'pokemon_data'):
            self.pokemon_view.pokemon_data['rarity'] = self.values[0]
        elif hasattr(self.pokemon_view, 'wish_data'):
            self.pokemon_view.wish_data['rarity'] = self.values[0]
        
        # Finalisiere das Angebot automatisch
        await self.pokemon_view.finalize_offer(interaction)

class OfferSelect(discord.ui.Select):
    """Dropdown für Pokemon-Angebote Auswahl"""
    
    def __init__(self, offers, cog):
        self.offers = offers
        self.cog = cog
        
        options = []
        for offer_id, offer_data in offers.items():
            # Hole Emojis für bessere Darstellung
            type_emoji = next((emoji for emoji, name in cog.pokemon_types.items() if name == offer_data['type']), "")
            rarity_emoji = next((emoji for emoji, name in cog.rarity_levels.items() if name == offer_data['rarity']), "")
            
            # Erstelle Option-Label (max 100 Zeichen)
            label = f"#{offer_id} {offer_data['name']} ({offer_data['hp']} KP)"
            if len(label) > 100:
                label = label[:97] + "..."
            
            # Erstelle Beschreibung (max 100 Zeichen)  
            description = f"{type_emoji} {offer_data['type']} | {rarity_emoji} {offer_data['rarity']}"
            if len(description) > 100:
                description = description[:97] + "..."
            
            options.append(discord.SelectOption(
                label=label,
                value=str(offer_id),
                description=description,
                emoji="🎯"
            ))
        
        # Discord erlaubt maximal 25 Optionen
        if len(options) > 25:
            options = options[:25]
        
        super().__init__(
            placeholder="Wähle ein Pokemon-Angebot aus...",
            options=options,
            custom_id="offer_select"
        )
    
    async def callback(self, interaction: discord.Interaction):
        offer_id = int(self.values[0])
        selected_offer = self.offers[offer_id]
        
        # Überprüfe ob der Benutzer nicht sein eigenes Angebot auswählt
        if selected_offer['user'].id == interaction.user.id:
            await interaction.response.send_message(
                "❌ Du kannst nicht auf dein eigenes Angebot reagieren!", 
                ephemeral=True
            )
            return
        
        # Erstelle Counter-Offer View
        counter_offer_view = CounterOfferView(selected_offer, interaction.user)
        
        # Erstelle Embed für das ausgewählte Angebot
        type_emoji = next((emoji for emoji, name in self.cog.pokemon_types.items() if name == selected_offer['type']), "")
        phase_emoji = next((emoji for emoji, name in self.cog.pokemon_phases.items() if name == selected_offer['phase']), "")
        rarity_emoji = next((emoji for emoji, name in self.cog.rarity_levels.items() if name == selected_offer['rarity']), "")
        
        embed = discord.Embed(
            title="🎯 Ausgewähltes Angebot",
            description=f"Du möchtest auf das Angebot von **{selected_offer['user'].display_name}** reagieren:",
            color=0x3498db
        )
        
        embed.add_field(name="📛 Pokemon", value=f"**{selected_offer['name']}**", inline=True)
        embed.add_field(name="❤️ KP", value=f"**{selected_offer['hp']}**", inline=True)
        embed.add_field(name="🏷️ Typ", value=f"{type_emoji} **{selected_offer['type']}**", inline=True)
        embed.add_field(name="🔄 Phase", value=f"{phase_emoji} **{selected_offer['phase']}**", inline=True)
        embed.add_field(name="💎 Seltenheit", value=f"{rarity_emoji} **{selected_offer['rarity']}**", inline=True)
        embed.add_field(name="👤 Anbieter", value=selected_offer['user'].mention, inline=True)
        
        embed.add_field(
            name="🔄 Nächster Schritt",
            value="Wähle eine Option um zu reagieren:",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=counter_offer_view)

class OffersListView(discord.ui.View):
    """View für die Angebote-Liste"""
    
    def __init__(self, offers, cog):
        super().__init__(timeout=300)
        self.offers = offers
        self.cog = cog
        
        if offers:
            self.add_item(OfferSelect(offers, cog))
    
    @discord.ui.button(label="Aktualisieren", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def refresh_offers(self, interaction: discord.Interaction, button: discord.ui.Button):
        _ = button  # Ignoriere unused argument warning
        # Aktualisiere die Angebote-Liste
        await self.cog.show_offers_list(interaction, is_refresh=True)
    
    @discord.ui.button(label="Schließen", style=discord.ButtonStyle.secondary, emoji="❌")
    async def close_offers(self, interaction: discord.Interaction, button: discord.ui.Button):
        _ = button  # Ignoriere unused argument warning
        embed = discord.Embed(
            title="📋 Angebote-Liste geschlossen",
            description="Du kannst jederzeit `!angebote` verwenden um die Liste erneut zu öffnen.",
            color=0xff0000
        )
        
        # Deaktiviere alle Buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)

class CounterOfferView(discord.ui.View):
    """View für Reaktionen auf ein Angebot"""
    
    def __init__(self, target_offer, responding_user):
        super().__init__(timeout=300)
        self.target_offer = target_offer
        self.responding_user = responding_user
    
    @discord.ui.button(label="Gegenangebot erstellen", style=discord.ButtonStyle.primary, emoji="🎮")
    async def create_counter_offer(self, interaction: discord.Interaction, button: discord.ui.Button):
        _ = button  # Ignoriere unused argument warning
        
        embed = discord.Embed(
            title="🎮 Gegenangebot erstellen",
            description=f"Erstelle ein Gegenangebot für **{self.target_offer['user'].display_name}**s {self.target_offer['name']}!",
            color=0x3498db
        )
        
        embed.add_field(
            name="📋 Anleitung",
            value="Du wirst jetzt durch die Erstellung deines Gegenangebots geführt.\n"
                  "Nach der Erstellung wird dein Angebot automatisch an den ursprünglichen Anbieter gesendet!",
            inline=False
        )
        
        embed.set_footer(text="Klicke 'Gegenangebot starten' um zu beginnen")
        
        # Erstelle neue sequenzielle View für das Gegenangebot
        cog = interaction.client.get_cog('Pokemon')
        counter_offer_view = cog.CounterOfferSequentialView(cog, self.target_offer, self.responding_user)
        
        await interaction.response.edit_message(embed=embed, view=counter_offer_view)
    
    @discord.ui.button(label="💬 Private Nachricht", style=discord.ButtonStyle.secondary, emoji="💬")
    async def send_private_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        _ = button  # Ignoriere unused argument warning
        
        # Sende private Nachricht an den Anbieter
        try:
            dm_embed = discord.Embed(
                title="🔔 Jemand ist interessiert an deinem Pokemon!",
                description=f"**{interaction.user.display_name}** hat Interesse an deinem **{self.target_offer['name']}** gezeigt!",
                color=0x00ff00
            )
            dm_embed.add_field(
                name="Kontakt",
                value=f"Schreibe {interaction.user.mention} eine private Nachricht um den Tausch zu besprechen!",
                inline=False
            )
            
            await self.target_offer['user'].send(embed=dm_embed)
            
            await interaction.response.send_message(
                f"✅ Ich habe {self.target_offer['user'].display_name} über dein Interesse informiert! "
                f"Sie werden sich bei dir melden.", 
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                f"❌ Ich konnte {self.target_offer['user'].display_name} keine private Nachricht senden. "
                f"Kontaktiere sie direkt: {self.target_offer['user'].mention}",
                ephemeral=True
            )
    
    @discord.ui.button(label="Zurück zur Liste", style=discord.ButtonStyle.secondary, emoji="↩️")
    async def back_to_list(self, interaction: discord.Interaction, button: discord.ui.Button):
        _ = button  # Ignoriere unused argument warning
        # Gehe zurück zur Angebote-Liste
        cog = interaction.client.get_cog('Pokemon')
        await cog.show_offers_list(interaction, is_refresh=True)

class WishSequentialView(discord.ui.View):
    """View für sequenzielle Pokemon-Wunsch-Eingabe"""
    
    def __init__(self, cog):
        super().__init__(timeout=300)
        self.cog = cog
        self.wish_data = {
            'name': None,
            'type': None,
            'hp': None,
            'phase': None,
            'rarity': None,
            'user': None,
            'offer_included': False,
            'offer_data': None
        }
        self.current_step = 1
    
    @discord.ui.button(label="Wunsch erstellen", style=discord.ButtonStyle.primary, emoji="🌟")
    async def start_wish(self, interaction: discord.Interaction, button: discord.ui.Button):
        _ = button  # Ignoriere unused argument warning
        # Starte mit Name-Eingabe
        modal = self.cog.PokemonNameModal(self)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Abbrechen", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_wish(self, interaction: discord.Interaction, button: discord.ui.Button = None):
        if button:
            _ = button  # Ignoriere unused argument warning
        embed = discord.Embed(
            title="❌ Pokemon-Wunsch abgebrochen",
            description="Der Wunsch wurde abgebrochen.",
            color=0xff0000
        )
        
        # Deaktiviere alle Buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def show_hp_input(self, interaction: discord.Interaction):
        """Zeige KP-Eingabe (Schritt 2)"""
        self.current_step = 2
        embed = discord.Embed(
            title="🌟 Pokemon-Wunsch erstellen - Schritt 2/5",
            description=f"✅ **Name:** {self.wish_data['name']}\n\nJetzt gib die gewünschten KP ein:",
            color=0xffd700
        )
        embed.set_footer(text="Schritt 2 von 5: KP eingeben")
        
        self.clear_items()
        self.add_item(discord.ui.Button(label="❤️ KP eingeben", style=discord.ButtonStyle.primary, custom_id="hp_input"))
        self.add_item(discord.ui.Button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary, custom_id="cancel"))
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Behandle Button-Klicks in der Wunsch-View"""
        if interaction.data.get("custom_id") == "hp_input":
            modal = self.cog.PokemonHPModal(self)
            await interaction.response.send_modal(modal)
            return False
        elif interaction.data.get("custom_id") == "cancel":
            embed = discord.Embed(
                title="❌ Pokemon-Wunsch abgebrochen",
                description="Der Wunsch wurde abgebrochen.",
                color=0xff0000
            )
            
            # Deaktiviere alle Buttons
            for item in self.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
            return False
        return True
    
    async def show_type_selection(self, interaction: discord.Interaction):
        """Zeige Typ-Auswahl (Schritt 3)"""
        self.current_step = 3
        embed = discord.Embed(
            title="🌟 Pokemon-Wunsch erstellen - Schritt 3/5",
            description=f"✅ **Name:** {self.wish_data['name']}\n✅ **KP:** {self.wish_data['hp']}\n\nWähle den gewünschten Typ:",
            color=0xffd700
        )
        embed.set_footer(text="Schritt 3 von 5: Typ auswählen")
        
        self.clear_items()
        self.add_item(TypeSelect(self))
        self.add_item(discord.ui.Button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary, custom_id="cancel", row=1))
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def show_phase_selection(self, interaction: discord.Interaction):
        """Zeige Phase-Auswahl (Schritt 4)"""
        self.current_step = 4
        type_emoji = next((emoji for emoji, name in self.cog.pokemon_types.items() if name == self.wish_data['type']), "")
        
        embed = discord.Embed(
            title="🌟 Pokemon-Wunsch erstellen - Schritt 4/5",
            description=f"✅ **Name:** {self.wish_data['name']}\n✅ **KP:** {self.wish_data['hp']}\n✅ **Typ:** {type_emoji} {self.wish_data['type']}\n\nWähle die gewünschte Phase:",
            color=0xffd700
        )
        embed.set_footer(text="Schritt 4 von 5: Phase auswählen")
        
        self.clear_items()
        self.add_item(PhaseSelect(self))
        self.add_item(discord.ui.Button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary, custom_id="cancel", row=1))
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def show_rarity_selection(self, interaction: discord.Interaction):
        """Zeige Seltenheit-Auswahl (Schritt 5)"""
        self.current_step = 5
        type_emoji = next((emoji for emoji, name in self.cog.pokemon_types.items() if name == self.wish_data['type']), "")
        phase_emoji = next((emoji for emoji, name in self.cog.pokemon_phases.items() if name == self.wish_data['phase']), "")
        
        embed = discord.Embed(
            title="🌟 Pokemon-Wunsch erstellen - Schritt 5/5",
            description=f"✅ **Name:** {self.wish_data['name']}\n✅ **KP:** {self.wish_data['hp']}\n✅ **Typ:** {type_emoji} {self.wish_data['type']}\n✅ **Phase:** {phase_emoji} {self.wish_data['phase']}\n\nWähle die gewünschte Seltenheit:",
            color=0xffd700
        )
        embed.set_footer(text="Schritt 5 von 5: Seltenheit auswählen")
        
        self.clear_items()
        self.add_item(RaritySelect(self))
        self.add_item(discord.ui.Button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary, custom_id="cancel", row=1))
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def finalize_offer(self, interaction: discord.Interaction):
        await self.show_offer_option(interaction)
    
    async def show_offer_option(self, interaction: discord.Interaction):
        """Zeigt die Option, ein Tauschangebot hinzuzufügen"""
        type_emoji = next((emoji for emoji, name in self.cog.pokemon_types.items() if name == self.wish_data['type']), "")
        phase_emoji = next((emoji for emoji, name in self.cog.pokemon_phases.items() if name == self.wish_data['phase']), "")
        rarity_emoji = next((emoji for emoji, name in self.cog.rarity_levels.items() if name == self.wish_data['rarity']), "")
        
        embed = discord.Embed(
            title="🌟 Pokemon-Wunsch fast fertig!",
            description="Dein Wunsch-Pokemon ist vollständig definiert:",
            color=0xffd700
        )
        
        embed.add_field(
            name="🎯 Gesuchtes Pokemon",
            value=f"**{self.wish_data['name']}** ({self.wish_data['hp']} KP)\n"
                  f"{type_emoji} {self.wish_data['type']} | "
                  f"{phase_emoji} {self.wish_data['phase']} | "
                  f"{rarity_emoji} {self.wish_data['rarity']}",
            inline=False
        )
        
        embed.add_field(
            name="🔄 Optionaler nächster Schritt",
            value="Möchtest du direkt ein Pokemon zum Tausch anbieten?",
            inline=False
        )
        
        # Neue View mit Optionen
        offer_option_view = WishOfferOptionView(self.cog, self.wish_data)
        
        await interaction.response.edit_message(embed=embed, view=offer_option_view)

class WishOfferOptionView(discord.ui.View):
    """View für die Wahl, ob ein Tauschangebot hinzugefügt werden soll"""
    
    def __init__(self, cog, wish_data):
        super().__init__(timeout=300)
        self.cog = cog
        self.wish_data = wish_data
    
    @discord.ui.button(label="Tauschangebot hinzufügen", style=discord.ButtonStyle.primary, emoji="🎮")
    async def add_trade_offer(self, interaction: discord.Interaction, button: discord.ui.Button):
        _ = button  # Ignoriere unused argument warning
        
        embed = discord.Embed(
            title="🎮 Tauschangebot hinzufügen",
            description="Erstelle jetzt ein Pokemon, das du im Tausch anbieten möchtest!",
            color=0x3498db
        )
        
        embed.add_field(
            name="📋 Info",
            value="Du wirst durch die Erstellung deines Tauschangebots geführt.\n"
                  "Danach wird dein Wunsch mit dem Angebot zusammen veröffentlicht!",
            inline=False
        )
        
        # Erstelle eine neue sequenzielle View für das Tauschangebot
        trade_offer_view = self.cog.WishTradeOfferView(self.cog, self.wish_data, interaction.user)
        
        await interaction.response.edit_message(embed=embed, view=trade_offer_view)
    
    @discord.ui.button(label="Nur Wunsch veröffentlichen", style=discord.ButtonStyle.secondary, emoji="🌟")
    async def publish_wish_only(self, interaction: discord.Interaction, button: discord.ui.Button):
        _ = button  # Ignoriere unused argument warning
        self.wish_data['user'] = interaction.user
        await self.cog.create_final_wish(interaction, self.wish_data)
    
    @discord.ui.button(label="Abbrechen", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_wish(self, interaction: discord.Interaction, button: discord.ui.Button):
        _ = button  # Ignoriere unused argument warning
        embed = discord.Embed(
            title="❌ Pokemon-Wunsch abgebrochen",
            description="Der Wunsch wurde abgebrochen.",
            color=0xff0000
        )
        
        # Deaktiviere alle Buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)

class CounterOfferResponseView(discord.ui.View):
    """View für die Annahme/Ablehnung von Gegenangeboten"""
    
    def __init__(self, original_offer_data, counter_offer_data, counter_offer_user):
        super().__init__(timeout=86400)  # 24 Stunden für Entscheidung
        self.original_offer_data = original_offer_data
        self.counter_offer_data = counter_offer_data
        self.counter_offer_user = counter_offer_user
        
        # Erkenne ob es sich um ein Angebot oder einen Wunsch handelt
        self.is_wish = 'offer_id' not in original_offer_data
        self.is_offer = 'offer_id' in original_offer_data
    
    @discord.ui.button(label="Annehmen", style=discord.ButtonStyle.success, emoji="✅")
    async def accept_counter_offer(self, interaction: discord.Interaction, button: discord.ui.Button):
        _ = button  # Ignoriere unused argument warning
        
        # Deaktiviere alle Buttons
        for item in self.children:
            item.disabled = True
        
        # Aktualisiere die DM-Nachricht
        embed = discord.Embed(
            title="✅ Gegenangebot angenommen!",
            description=f"Du hast das Gegenangebot von **{self.counter_offer_user.display_name}** angenommen!",
            color=0x00ff00
        )
        
        embed.add_field(
            name="🎯 Dein Pokemon",
            value=f"**{self.original_offer_data['name']}** ({self.original_offer_data['hp']} KP)",
            inline=True
        )
        
        embed.add_field(
            name="🎮 Erhaltenes Pokemon",
            value=f"**{self.counter_offer_data['name']}** ({self.counter_offer_data['hp']} KP)",
            inline=True
        )
        
        embed.add_field(
            name="💬 Nächster Schritt",
            value=f"Kontaktiere {self.counter_offer_user.mention} um den Tausch durchzuführen!",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=self)
        
        # Entferne das ursprüngliche Angebot/Wunsch aus der aktiven Liste
        cog = interaction.client.get_cog('Pokemon')
        if self.is_offer and 'offer_id' in self.original_offer_data:
            # Entferne das ursprüngliche Angebot
            offer_id = self.original_offer_data['offer_id']
            if cog.remove_offer(offer_id):
                print(f"✅ Angebot #{offer_id} wurde nach erfolgreichem Tausch entfernt")
        elif self.is_wish and 'wish_id' in self.original_offer_data:
            # Entferne den ursprünglichen Wunsch
            wish_id = self.original_offer_data['wish_id']
            if cog.remove_wish(wish_id):
                print(f"✅ Wunsch #{wish_id} wurde nach erfolgreichem Tausch entfernt")
        
        # Benachrichtige den Gegenangebot-Ersteller
        try:
            success_embed = discord.Embed(
                title="🎉 Dein Gegenangebot wurde angenommen!",
                description=f"**{interaction.user.display_name}** hat dein Gegenangebot angenommen!",
                color=0x00ff00
            )
            
            success_embed.add_field(
                name="🎯 Du bekommst",
                value=f"**{self.original_offer_data['name']}** ({self.original_offer_data['hp']} KP)",
                inline=True
            )
            
            success_embed.add_field(
                name="🎮 Du gibst",
                value=f"**{self.counter_offer_data['name']}** ({self.counter_offer_data['hp']} KP)",
                inline=True
            )
            
            success_embed.add_field(
                name="💬 Nächster Schritt",
                value=f"**{interaction.user.display_name}** wird sich bei dir melden um den Tausch durchzuführen!\n"
                      f"Du kannst auch direkt {interaction.user.mention} kontaktieren.",
                inline=False
            )
            
            await self.counter_offer_user.send(embed=success_embed)
            
        except discord.Forbidden:
            # Falls DM nicht möglich ist, ignoriere es
            pass
    
    @discord.ui.button(label="Ablehnen", style=discord.ButtonStyle.secondary, emoji="❌")
    async def reject_counter_offer(self, interaction: discord.Interaction, button: discord.ui.Button):
        _ = button  # Ignoriere unused argument warning
        
        # Deaktiviere alle Buttons
        for item in self.children:
            item.disabled = True
        
        # Aktualisiere die DM-Nachricht
        embed = discord.Embed(
            title="❌ Gegenangebot abgelehnt",
            description=f"Du hast das Gegenangebot von **{self.counter_offer_user.display_name}** abgelehnt.",
            color=0xff0000
        )
        
        embed.add_field(
            name="📝 Info",
            value="Das Gegenangebot wurde abgelehnt. Du kannst weiterhin auf andere Angebote warten oder selbst Gegenangebote erstellen.",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=self)
        
        # Benachrichtige den Gegenangebot-Ersteller
        try:
            rejection_embed = discord.Embed(
                title="😔 Dein Gegenangebot wurde abgelehnt",
                description=f"**{interaction.user.display_name}** hat dein Gegenangebot leider abgelehnt.",
                color=0xff9900
            )
            
            rejection_embed.add_field(
                name="💡 Nächste Schritte",
                value="• Versuche ein anderes Gegenangebot zu erstellen\n"
                      "• Schaue dir andere verfügbare Angebote an (`!angebote`)\n"
                      "• Erstelle dein eigenes Angebot (`!bieten`)",
                inline=False
            )
            
            await self.counter_offer_user.send(embed=rejection_embed)
            
        except discord.Forbidden:
            # Falls DM nicht möglich ist, ignoriere es
            pass
    
    @discord.ui.button(label="💬 Nachricht senden", style=discord.ButtonStyle.secondary, emoji="💬")
    async def send_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        _ = button  # Ignoriere unused argument warning
        
        await interaction.response.send_message(
            f"Du kannst {self.counter_offer_user.mention} direkt kontaktieren um über das Gegenangebot zu sprechen!",
            ephemeral=True
        )

class WishSelect(discord.ui.Select):
    """Dropdown für Pokemon-Wünsche Auswahl"""
    
    def __init__(self, wishes, cog):
        self.wishes = wishes
        self.cog = cog
        
        options = []
        for wish_id, wish_data in wishes.items():
            # Hole Emojis für bessere Darstellung
            type_emoji = next((emoji for emoji, name in cog.pokemon_types.items() if name == wish_data['type']), "")
            rarity_emoji = next((emoji for emoji, name in cog.rarity_levels.items() if name == wish_data['rarity']), "")
            
            # Erstelle Option-Label (max 100 Zeichen)
            label = f"#{wish_id} {wish_data['name']} ({wish_data['hp']} KP)"
            if len(label) > 100:
                label = label[:97] + "..."
            
            # Erstelle Beschreibung mit Tauschangebot-Info (max 100 Zeichen)  
            if wish_data.get('offer_included', False):
                description = f"{type_emoji} {wish_data['type']} | {rarity_emoji} {wish_data['rarity']} | 🎮 Mit Angebot"
            else:
                description = f"{type_emoji} {wish_data['type']} | {rarity_emoji} {wish_data['rarity']}"
            
            if len(description) > 100:
                description = description[:97] + "..."
            
            # Wähle Emoji basierend auf Tauschangebot
            emoji = "🎮" if wish_data.get('offer_included', False) else "🌟"
            
            options.append(discord.SelectOption(
                label=label,
                value=str(wish_id),
                description=description,
                emoji=emoji
            ))
        
        # Discord erlaubt maximal 25 Optionen
        if len(options) > 25:
            options = options[:25]
        
        super().__init__(
            placeholder="Wähle einen Pokemon-Wunsch aus...",
            options=options,
            custom_id="wish_select"
        )
    
    async def callback(self, interaction: discord.Interaction):
        wish_id = int(self.values[0])
        selected_wish = self.wishes[wish_id]
        
        # Überprüfe ob der Benutzer nicht seinen eigenen Wunsch auswählt
        if selected_wish['user'].id == interaction.user.id:
            await interaction.response.send_message(
                "❌ Du kannst nicht auf deinen eigenen Wunsch reagieren!", 
                ephemeral=True
            )
            return
        
        # Erstelle Response View basierend auf Wunsch-Typ
        if selected_wish.get('offer_included', False):
            # Wunsch mit Tauschangebot
            wish_response_view = WishWithOfferResponseView(selected_wish, interaction.user)
        else:
            # Nur Wunsch ohne Tauschangebot
            wish_response_view = WishOnlyResponseView(selected_wish, interaction.user)
        
        # Erstelle Embed für den ausgewählten Wunsch
        type_emoji = next((emoji for emoji, name in self.cog.pokemon_types.items() if name == selected_wish['type']), "")
        phase_emoji = next((emoji for emoji, name in self.cog.pokemon_phases.items() if name == selected_wish['phase']), "")
        rarity_emoji = next((emoji for emoji, name in self.cog.rarity_levels.items() if name == selected_wish['rarity']), "")
        
        embed = discord.Embed(
            title="🌟 Ausgewählter Wunsch",
            description=f"Du möchtest auf den Wunsch von **{selected_wish['user'].display_name}** reagieren:",
            color=0xffd700
        )
        
        embed.add_field(name="📛 Gesuchtes Pokemon", value=f"**{selected_wish['name']}**", inline=True)
        embed.add_field(name="❤️ KP", value=f"**{selected_wish['hp']}**", inline=True)
        embed.add_field(name="🏷️ Typ", value=f"{type_emoji} **{selected_wish['type']}**", inline=True)
        embed.add_field(name="🔄 Phase", value=f"{phase_emoji} **{selected_wish['phase']}**", inline=True)
        embed.add_field(name="💎 Seltenheit", value=f"{rarity_emoji} **{selected_wish['rarity']}**", inline=True)
        embed.add_field(name="👤 Wünschender", value=selected_wish['user'].mention, inline=True)
        
        # Zeige Tauschangebot-Info falls vorhanden
        if selected_wish.get('offer_included', False) and selected_wish.get('offer_data'):
            offer_data = selected_wish['offer_data']
            offer_type_emoji = next((emoji for emoji, name in self.cog.pokemon_types.items() if name == offer_data['type']), "")
            offer_phase_emoji = next((emoji for emoji, name in self.cog.pokemon_phases.items() if name == offer_data['phase']), "")
            offer_rarity_emoji = next((emoji for emoji, name in self.cog.rarity_levels.items() if name == offer_data['rarity']), "")
            
            embed.add_field(
                name="🎮 Angebotenes Pokemon",
                value=f"**{offer_data['name']}** ({offer_data['hp']} KP)\n"
                      f"{offer_type_emoji} {offer_data['type']} | "
                      f"{offer_phase_emoji} {offer_data['phase']} | "
                      f"{offer_rarity_emoji} {offer_data['rarity']}",
                inline=False
            )
        
        embed.add_field(
            name="🔄 Nächster Schritt",
            value="Wähle eine Option um zu reagieren:",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=wish_response_view)

class WishesListView(discord.ui.View):
    """View für die Wünsche-Liste"""
    
    def __init__(self, wishes, cog):
        super().__init__(timeout=300)
        self.wishes = wishes
        self.cog = cog
        
        if wishes:
            self.add_item(WishSelect(wishes, cog))
    
    @discord.ui.button(label="Aktualisieren", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def refresh_wishes(self, interaction: discord.Interaction, button: discord.ui.Button):
        _ = button  # Ignoriere unused argument warning
        # Aktualisiere die Wünsche-Liste
        await self.cog.show_wishes_list(interaction, is_refresh=True)
    
    @discord.ui.button(label="Schließen", style=discord.ButtonStyle.danger, emoji="❌")
    async def close_wishes(self, interaction: discord.Interaction, button: discord.ui.Button):
        _ = button  # Ignoriere unused argument warning
        embed = discord.Embed(
            title="📋 Wünsche-Liste geschlossen",
            description="Du kannst jederzeit `!wünsche` verwenden um die Liste erneut zu öffnen.",
            color=0xff0000
        )
        
        # Deaktiviere alle Buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)

class WishOnlyResponseView(discord.ui.View):
    """View für Reaktionen auf einen reinen Wunsch (ohne Tauschangebot)"""
    
    def __init__(self, target_wish, responding_user):
        super().__init__(timeout=300)
        self.target_wish = target_wish
        self.responding_user = responding_user
    
    @discord.ui.button(label="Gegenangebot erstellen", style=discord.ButtonStyle.primary, emoji="🎮")
    async def create_counter_offer_for_wish(self, interaction: discord.Interaction, button: discord.ui.Button):
        _ = button  # Ignoriere unused argument warning
        
        embed = discord.Embed(
            title="🎮 Gegenangebot für Wunsch erstellen",
            description=f"Erstelle ein Angebot für **{self.target_wish['user'].display_name}**s Wunsch!",
            color=0x3498db
        )
        
        embed.add_field(
            name="🎯 Gesuchtes Pokemon",
            value=f"**{self.target_wish['name']}** ({self.target_wish['hp']} KP)",
            inline=False
        )
        
        embed.add_field(
            name="📋 Anleitung",
            value="Du wirst jetzt durch die Erstellung deines Angebots geführt.\n"
                  "Nach der Erstellung wird dein Angebot automatisch an den Wünschenden gesendet!",
            inline=False
        )
        
        embed.set_footer(text="Klicke 'Angebot starten' um zu beginnen")
        
        # Erstelle neue sequenzielle View für das Angebot
        cog = interaction.client.get_cog('Pokemon')
        offer_view = cog.create_wish_counter_offer_view(self.target_wish, self.responding_user)
        
        await interaction.response.edit_message(embed=embed, view=offer_view)
    
    @discord.ui.button(label="💬 Kontakt aufnehmen", style=discord.ButtonStyle.secondary, emoji="💬")
    async def contact_wisher(self, interaction: discord.Interaction, button: discord.ui.Button):
        _ = button  # Ignoriere unused argument warning
        
        # Sende private Nachricht an den Wünschenden
        try:
            dm_embed = discord.Embed(
                title="🔔 Jemand ist interessiert an deinem Wunsch!",
                description=f"**{interaction.user.display_name}** hat Interesse an deinem Pokemon-Wunsch gezeigt!",
                color=0x00ff00
            )
            
            dm_embed.add_field(
                name="🎯 Dein Wunsch",
                value=f"**{self.target_wish['name']}** ({self.target_wish['hp']} KP)",
                inline=False
            )
            
            dm_embed.add_field(
                name="Kontakt",
                value=f"Schreibe {interaction.user.mention} eine private Nachricht um den Tausch zu besprechen!",
                inline=False
            )
            
            await self.target_wish['user'].send(embed=dm_embed)
            
            await interaction.response.send_message(
                f"✅ Ich habe {self.target_wish['user'].display_name} über dein Interesse informiert! "
                f"Sie werden sich bei dir melden.", 
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                f"❌ Ich konnte {self.target_wish['user'].display_name} keine private Nachricht senden. "
                f"Kontaktiere sie direkt: {self.target_wish['user'].mention}",
                ephemeral=True
            )
    
    @discord.ui.button(label="Zurück zur Liste", style=discord.ButtonStyle.secondary, emoji="↩️")
    async def back_to_list(self, interaction: discord.Interaction, button: discord.ui.Button):
        _ = button  # Ignoriere unused argument warning
        # Gehe zurück zur Wünsche-Liste  
        cog = interaction.client.get_cog('Pokemon')
        await cog.show_wishes_list(interaction, is_refresh=True)

class WishWithOfferResponseView(discord.ui.View):
    """View für Reaktionen auf einen Wunsch mit Tauschangebot"""
    
    def __init__(self, target_wish, responding_user):
        super().__init__(timeout=300)
        self.target_wish = target_wish
        self.responding_user = responding_user
    
    @discord.ui.button(label="Tauschangebot annehmen", style=discord.ButtonStyle.success, emoji="✅")
    async def accept_trade_offer(self, interaction: discord.Interaction, button: discord.ui.Button):
        _ = button  # Ignoriere unused argument warning
        
        offer_data = self.target_wish['offer_data']
        
        # Erstelle Annahme-Embed
        embed = discord.Embed(
            title="✅ Tauschangebot angenommen!",
            description=f"Du hast das Tauschangebot von **{self.target_wish['user'].display_name}** angenommen!",
            color=0x00ff00
        )
        
        embed.add_field(
            name="🎯 Du gibst",
            value=f"**{self.target_wish['name']}** ({self.target_wish['hp']} KP)",
            inline=True
        )
        
        embed.add_field(
            name="🎮 Du bekommst",
            value=f"**{offer_data['name']}** ({offer_data['hp']} KP)",
            inline=True
        )
        
        embed.add_field(
            name="💬 Nächster Schritt",
            value=f"Kontaktiere {self.target_wish['user'].mention} um den Tausch durchzuführen!",
            inline=False
        )
        
        # Deaktiviere alle Buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
        
        # Entferne den Wunsch aus der aktiven Liste
        cog = interaction.client.get_cog('Pokemon')
        if 'wish_id' in self.target_wish:
            wish_id = self.target_wish['wish_id']
            if cog.remove_wish(wish_id):
                print(f"✅ Wunsch #{wish_id} wurde nach erfolgreichem Tausch entfernt")
        
        # Benachrichtige den Wünschenden
        try:
            success_embed = discord.Embed(
                title="🎉 Dein Tauschangebot wurde angenommen!",
                description=f"**{interaction.user.display_name}** hat dein Tauschangebot angenommen!",
                color=0x00ff00
            )
            
            success_embed.add_field(
                name="🎯 Du bekommst",
                value=f"**{self.target_wish['name']}** ({self.target_wish['hp']} KP)",
                inline=True
            )
            
            success_embed.add_field(
                name="🎮 Du gibst",
                value=f"**{offer_data['name']}** ({offer_data['hp']} KP)",
                inline=True
            )
            
            success_embed.add_field(
                name="💬 Nächster Schritt",
                value=f"**{interaction.user.display_name}** wird sich bei dir melden um den Tausch durchzuführen!\n"
                      f"Du kannst auch direkt {interaction.user.mention} kontaktieren.",
                inline=False
            )
            
            await self.target_wish['user'].send(embed=success_embed)
            
        except discord.Forbidden:
            # Falls DM nicht möglich ist, ignoriere es
            pass
    
    @discord.ui.button(label="Gegenangebot erstellen", style=discord.ButtonStyle.primary, emoji="🎮")
    async def create_counter_offer(self, interaction: discord.Interaction, button: discord.ui.Button):
        _ = button  # Ignoriere unused argument warning
        
        embed = discord.Embed(
            title="🎮 Gegenangebot erstellen",
            description=f"Erstelle ein alternatives Angebot für **{self.target_wish['user'].display_name}**!",
            color=0x3498db
        )
        
        embed.add_field(
            name="📋 Info",
            value="Du kannst ein anderes Pokemon anbieten als das bereits vorgeschlagene.\n"
                  "Nach der Erstellung wird dein Gegenangebot an den Wünschenden gesendet!",
            inline=False
        )
        
        # Erstelle neue sequenzielle View für das Gegenangebot
        cog = interaction.client.get_cog('Pokemon')
        offer_view = cog.create_wish_counter_offer_view(self.target_wish, self.responding_user)
        
        await interaction.response.edit_message(embed=embed, view=offer_view)
    
    @discord.ui.button(label="💬 Kontakt aufnehmen", style=discord.ButtonStyle.secondary, emoji="💬")
    async def contact_wisher(self, interaction: discord.Interaction, button: discord.ui.Button):
        _ = button  # Ignoriere unused argument warning
        
        # Sende private Nachricht an den Wünschenden
        try:
            dm_embed = discord.Embed(
                title="🔔 Jemand ist interessiert an deinem Wunsch!",
                description=f"**{interaction.user.display_name}** hat Interesse an deinem Pokemon-Wunsch gezeigt!",
                color=0x00ff00
            )
            
            dm_embed.add_field(
                name="🎯 Dein Wunsch mit Angebot",
                value=f"**{self.target_wish['name']}** für **{self.target_wish['offer_data']['name']}**",
                inline=False
            )
            
            dm_embed.add_field(
                name="Kontakt",
                value=f"Schreibe {interaction.user.mention} eine private Nachricht um zu besprechen!",
                inline=False
            )
            
            await self.target_wish['user'].send(embed=dm_embed)
            
            await interaction.response.send_message(
                f"✅ Ich habe {self.target_wish['user'].display_name} über dein Interesse informiert! "
                f"Sie werden sich bei dir melden.", 
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                f"❌ Ich konnte {self.target_wish['user'].display_name} keine private Nachricht senden. "
                f"Kontaktiere sie direkt: {self.target_wish['user'].mention}",
                ephemeral=True
            )
    
    @discord.ui.button(label="Zurück zur Liste", style=discord.ButtonStyle.secondary, emoji="↩️")
    async def back_to_list(self, interaction: discord.Interaction, button: discord.ui.Button):
        _ = button  # Ignoriere unused argument warning
        # Gehe zurück zur Wünsche-Liste  
        cog = interaction.client.get_cog('Pokemon')
        await cog.show_wishes_list(interaction, is_refresh=True)

class Pokemon(commands.Cog):
    """Pokemon Tausch System"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Speicher für aktive Pokemon-Angebote (in Produktion sollte das eine Datenbank sein)
        self.active_offers = {}  # offer_id: pokemon_data
        self.offer_counter = 0
        
        # Speicher für Pokemon-Wünsche
        self.active_wishes = {}  # wish_id: wish_data
        self.wish_counter = 0
        
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
            "⚪": "Häufig",
            "🔷": "Nicht so häufig",
            "⭐": "Selten",
            "✨": "Doppelselten",
            "🌟": "Illustrationskarte"
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
        """Modal für Pokemon-Name Eingabe"""
        
        def __init__(self, view):
            super().__init__(title="Schritt 1: Pokemon Name")
            self.view = view
            
            self.name_input = discord.ui.TextInput(
                label="Pokemon Name",
                placeholder="z.B. Pikachu, Charizard, Glurak...",
                required=True,
                max_length=50
            )
            self.add_item(self.name_input)
        
        async def on_submit(self, interaction: discord.Interaction):
            # Bestimme welcher Datencontainer verwendet wird
            if hasattr(self.view, 'pokemon_data'):
                self.view.pokemon_data['name'] = self.name_input.value
                self.view.pokemon_data['user'] = interaction.user
            elif hasattr(self.view, 'wish_data'):
                self.view.wish_data['name'] = self.name_input.value
                self.view.wish_data['user'] = interaction.user
            
            # Gehe automatisch zum nächsten Schritt (KP)
            await self.view.show_hp_input(interaction)
    
    class PokemonHPModal(discord.ui.Modal):
        """Modal für Pokemon-KP Eingabe"""
        
        def __init__(self, view):
            super().__init__(title="Schritt 2: Pokemon KP")
            self.view = view
            
            self.hp_input = discord.ui.TextInput(
                label="KP (Kraftpunkte)",
                placeholder="z.B. 60, 120, 250...",
                required=True,
                max_length=4
            )
            self.add_item(self.hp_input)
        
        async def on_submit(self, interaction: discord.Interaction):
            try:
                hp_value = int(self.hp_input.value)
                if hp_value <= 0:
                    raise ValueError("KP müssen größer als 0 sein")
                
                # Bestimme welcher Datencontainer verwendet wird
                if hasattr(self.view, 'pokemon_data'):
                    self.view.pokemon_data['hp'] = hp_value
                elif hasattr(self.view, 'wish_data'):
                    self.view.wish_data['hp'] = hp_value
                
                # Gehe automatisch zum nächsten Schritt (Typ)
                await self.view.show_type_selection(interaction)
                
            except ValueError as e:
                if "invalid literal" in str(e):
                    await interaction.response.send_message("❌ KP müssen eine gültige Zahl sein!", ephemeral=True)
                else:
                    await interaction.response.send_message(f"❌ {str(e)}", ephemeral=True)
    
    
    # Neue sequenzielle View-Klasse
    class PokemonSequentialView(discord.ui.View):
        """View für sequenzielle Pokemon-Eingabe"""
        
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
            self.current_step = 1
        
        @discord.ui.button(label="Los geht's!", style=discord.ButtonStyle.primary, emoji="🚀")
        async def start_process(self, interaction: discord.Interaction, button: discord.ui.Button):
            _ = button  # Ignoriere unused argument warning
            # Starte mit Name-Eingabe
            modal = self.cog.PokemonNameModal(self)
            await interaction.response.send_modal(modal)
        
        @discord.ui.button(label="Abbrechen", style=discord.ButtonStyle.secondary, emoji="❌")
        async def cancel_offer(self, interaction: discord.Interaction, button: discord.ui.Button = None):
            if button:
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
        
        async def show_hp_input(self, interaction: discord.Interaction):
            """Zeige KP-Eingabe (Schritt 2)"""
            self.current_step = 2
            embed = discord.Embed(
                title="🎮 Pokemon-Angebot erstellen - Schritt 2/5",
                description=f"✅ **Name:** {self.pokemon_data['name']}\n\nJetzt gib die KP deines Pokemon ein:",
                color=0x3498db
            )
            embed.set_footer(text="Schritt 2 von 5: KP eingeben")
            
            # Erstelle View mit KP-Button
            self.clear_items()
            self.add_item(discord.ui.Button(label="❤️ KP eingeben", style=discord.ButtonStyle.primary, custom_id="hp_input"))
            self.add_item(discord.ui.Button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary, custom_id="cancel"))
            
            await interaction.response.edit_message(embed=embed, view=self)
        
        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            """Behandle Button-Klicks in der sequenziellen View"""
            if interaction.data.get("custom_id") == "hp_input":
                modal = self.cog.PokemonHPModal(self)
                await interaction.response.send_modal(modal)
                return False
            elif interaction.data.get("custom_id") == "cancel":
                embed = discord.Embed(
                    title="❌ Pokemon-Angebot abgebrochen",
                    description="Das Angebot wurde abgebrochen.",
                    color=0xff0000
                )
                
                # Deaktiviere alle Buttons
                for item in self.children:
                    item.disabled = True
                
                await interaction.response.edit_message(embed=embed, view=self)
                return False
            return True
        
        async def show_type_selection(self, interaction: discord.Interaction):
            """Zeige Typ-Auswahl (Schritt 3)"""
            self.current_step = 3
            embed = discord.Embed(
                title="🎮 Pokemon-Angebot erstellen - Schritt 3/5",
                description=f"✅ **Name:** {self.pokemon_data['name']}\n✅ **KP:** {self.pokemon_data['hp']}\n\nWähle den Typ deines Pokemon:",
                color=0x3498db
            )
            embed.set_footer(text="Schritt 3 von 5: Typ auswählen")
            
            # Erstelle neue View mit Type-Select
            self.clear_items()
            self.add_item(TypeSelect(self))
            self.add_item(discord.ui.Button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary, custom_id="cancel", row=1))
            
            await interaction.response.edit_message(embed=embed, view=self)
        
        async def show_phase_selection(self, interaction: discord.Interaction):
            """Zeige Phase-Auswahl (Schritt 4)"""
            self.current_step = 4
            type_emoji = next((emoji for emoji, name in self.cog.pokemon_types.items() if name == self.pokemon_data['type']), "")
            
            embed = discord.Embed(
                title="🎮 Pokemon-Angebot erstellen - Schritt 4/5",
                description=f"✅ **Name:** {self.pokemon_data['name']}\n✅ **KP:** {self.pokemon_data['hp']}\n✅ **Typ:** {type_emoji} {self.pokemon_data['type']}\n\nWähle die Phase deines Pokemon:",
                color=0x3498db
            )
            embed.set_footer(text="Schritt 4 von 5: Phase auswählen")
            
            # Erstelle neue View mit Phase-Select
            self.clear_items()
            self.add_item(PhaseSelect(self))
            self.add_item(discord.ui.Button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary, custom_id="cancel", row=1))
            
            await interaction.response.edit_message(embed=embed, view=self)
        
        async def show_rarity_selection(self, interaction: discord.Interaction):
            """Zeige Seltenheit-Auswahl (Schritt 5)"""
            self.current_step = 5
            type_emoji = next((emoji for emoji, name in self.cog.pokemon_types.items() if name == self.pokemon_data['type']), "")
            phase_emoji = next((emoji for emoji, name in self.cog.pokemon_phases.items() if name == self.pokemon_data['phase']), "")
            
            embed = discord.Embed(
                title="🎮 Pokemon-Angebot erstellen - Schritt 5/5",
                description=f"✅ **Name:** {self.pokemon_data['name']}\n✅ **KP:** {self.pokemon_data['hp']}\n✅ **Typ:** {type_emoji} {self.pokemon_data['type']}\n✅ **Phase:** {phase_emoji} {self.pokemon_data['phase']}\n\nWähle die Seltenheit deines Pokemon:",
                color=0x3498db
            )
            embed.set_footer(text="Schritt 5 von 5: Seltenheit auswählen")
            
            # Erstelle neue View mit Rarity-Select
            self.clear_items()
            self.add_item(RaritySelect(self))
            self.add_item(discord.ui.Button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary, custom_id="cancel", row=1))
            
            await interaction.response.edit_message(embed=embed, view=self)
        
        async def finalize_offer(self, interaction: discord.Interaction):
            """Finalisiere das Angebot"""
            # Prüfe ob dies ein Angebot für einen Wunsch ist
            if hasattr(self, 'target_wish') and hasattr(self, 'responding_user'):
                await self.create_wish_counter_offer(interaction)
            else:
                await self.create_final_offer(interaction)
        
        async def create_final_offer(self, interaction: discord.Interaction):
            """Erstellt das finale Pokemon-Angebot"""
            
            # Erstelle eine eindeutige Angebots-ID
            self.cog.offer_counter += 1
            offer_id = self.cog.offer_counter
            
            # Speichere das Angebot mit zusätzlichen Metadaten
            offer_data = self.pokemon_data.copy()
            offer_data['offer_id'] = offer_id
            offer_data['created_at'] = interaction.created_at
            offer_data['guild_id'] = interaction.guild_id
            offer_data['channel_id'] = interaction.channel_id
            
            self.cog.active_offers[offer_id] = offer_data
            
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
            embed.set_footer(text=f"Angebots-ID: #{offer_id} | Interessiert? Verwende !angebote oder den Button!")
            
            # Erstelle neue View für das finale Angebot
            final_view = self.cog.FinalOfferView(offer_data)
            
            await interaction.response.edit_message(embed=embed, view=final_view)
        
        async def create_wish_counter_offer(self, interaction: discord.Interaction):
            """Erstellt ein Gegenangebot für einen Wunsch"""
            
            # Hole die entsprechenden Emojis für das angebotene Pokemon
            type_emoji = next((emoji for emoji, name in self.cog.pokemon_types.items() if name == self.pokemon_data['type']), "")
            phase_emoji = next((emoji for emoji, name in self.cog.pokemon_phases.items() if name == self.pokemon_data['phase']), "")
            rarity_emoji = next((emoji for emoji, name in self.cog.rarity_levels.items() if name == self.pokemon_data['rarity']), "")
            
            # Hole die entsprechenden Emojis für das gewünschte Pokemon
            orig_type_emoji = next((emoji for emoji, name in self.cog.pokemon_types.items() if name == self.target_wish['type']), "")
            orig_phase_emoji = next((emoji for emoji, name in self.cog.pokemon_phases.items() if name == self.target_wish['phase']), "")
            orig_rarity_emoji = next((emoji for emoji, name in self.cog.rarity_levels.items() if name == self.target_wish['rarity']), "")
            
            embed = discord.Embed(
                title="✅ Gegenangebot für Wunsch erstellt!",
                description=f"Dein Angebot für **{self.target_wish['user'].display_name}**s Wunsch wurde erstellt!",
                color=0x00ff00
            )
            
            embed.add_field(
                name="🎯 Gewünschtes Pokemon",
                value=f"**{self.target_wish['name']}** ({self.target_wish['hp']} KP)\n"
                      f"{orig_type_emoji} {self.target_wish['type']} | "
                      f"{orig_phase_emoji} {self.target_wish['phase']} | "
                      f"{orig_rarity_emoji} {self.target_wish['rarity']}",
                inline=False
            )
            
            embed.add_field(
                name="🎮 Dein Angebot",
                value=f"**{self.pokemon_data['name']}** ({self.pokemon_data['hp']} KP)\n"
                      f"{type_emoji} {self.pokemon_data['type']} | "
                      f"{phase_emoji} {self.pokemon_data['phase']} | "
                      f"{rarity_emoji} {self.pokemon_data['rarity']}",
                inline=False
            )
            
            embed.set_footer(text="Angebot wird an den Wünschenden gesendet!")
            
            await interaction.response.edit_message(embed=embed, view=None)
            
            # Sende das Angebot an den Wünschenden
            try:
                dm_embed = discord.Embed(
                    title="🎁 Angebot für deinen Wunsch erhalten!",
                    description=f"**{self.responding_user.display_name}** möchte dir ein Pokemon für deinen Wunsch anbieten!",
                    color=0x3498db
                )
                
                dm_embed.add_field(
                    name="🎯 Dein Wunsch",
                    value=f"**{self.target_wish['name']}** ({self.target_wish['hp']} KP)\n"
                          f"{orig_type_emoji} {self.target_wish['type']} | "
                          f"{orig_phase_emoji} {self.target_wish['phase']} | "
                          f"{orig_rarity_emoji} {self.target_wish['rarity']}",
                    inline=False
                )
                
                dm_embed.add_field(
                    name=f"🎮 Angebot von {self.responding_user.display_name}",
                    value=f"**{self.pokemon_data['name']}** ({self.pokemon_data['hp']} KP)\n"
                          f"{type_emoji} {self.pokemon_data['type']} | "
                          f"{phase_emoji} {self.pokemon_data['phase']} | "
                          f"{rarity_emoji} {self.pokemon_data['rarity']}",
                    inline=False
                )
                
                dm_embed.add_field(
                    name="🔄 Entscheidung treffen",
                    value="Wähle eine Option:",
                    inline=False
                )
                
                # Erstelle die interaktive View mit Annehmen/Ablehnen Buttons (für Wünsche)
                response_view = CounterOfferResponseView(self.target_wish, self.pokemon_data, self.responding_user)
                
                await self.target_wish['user'].send(embed=dm_embed, view=response_view)
                
                # Bestätigung an den Absender
                await interaction.followup.send(
                    f"✅ Dein Angebot wurde erfolgreich an **{self.target_wish['user'].display_name}** gesendet!",
                    ephemeral=True
                )
                
            except discord.Forbidden:
                await interaction.followup.send(
                    f"❌ Ich konnte {self.target_wish['user'].display_name} keine private Nachricht senden. "
                    f"Kontaktiere sie direkt: {self.target_wish['user'].mention}",
                    ephemeral=True
                )
    
    class CounterOfferSequentialView(discord.ui.View):
        """View für sequenzielle Gegenangebot-Eingabe"""
        
        def __init__(self, cog, target_offer, responding_user):
            super().__init__(timeout=300)
            self.cog = cog
            self.target_offer = target_offer
            self.responding_user = responding_user
            self.pokemon_data = {
                'name': None,
                'type': None,
                'hp': None,
                'phase': None,
                'rarity': None,
                'user': responding_user
            }
            self.current_step = 1
        
        @discord.ui.button(label="🚀 Gegenangebot starten", style=discord.ButtonStyle.primary, emoji="🚀")
        async def start_counter_offer(self, interaction: discord.Interaction, button: discord.ui.Button):
            _ = button  # Ignoriere unused argument warning
            # Starte mit Name-Eingabe
            modal = self.cog.PokemonNameModal(self)
            await interaction.response.send_modal(modal)
        
        @discord.ui.button(label="Abbrechen", style=discord.ButtonStyle.secondary, emoji="❌")
        async def cancel_counter_offer(self, interaction: discord.Interaction, button: discord.ui.Button):
            _ = button  # Ignoriere unused argument warning
            # Gehe zurück zur Angebote-Liste
            await self.cog.show_offers_list(interaction, is_refresh=True)
        
        # Alle Methoden von PokemonSequentialView übernehmen
        async def show_hp_input(self, interaction: discord.Interaction):
            self.current_step = 2
            embed = discord.Embed(
                title="🎮 Gegenangebot erstellen - Schritt 2/5",
                description=f"✅ **Name:** {self.pokemon_data['name']}\n\nJetzt gib die KP deines Pokemon ein:",
                color=0x3498db
            )
            embed.set_footer(text="Schritt 2 von 5: KP eingeben")
            
            self.clear_items()
            self.add_item(discord.ui.Button(label="❤️ KP eingeben", style=discord.ButtonStyle.primary, custom_id="hp_input"))
            self.add_item(discord.ui.Button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary, custom_id="cancel"))
            
            await interaction.response.edit_message(embed=embed, view=self)
        
        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            if interaction.data.get("custom_id") == "hp_input":
                modal = self.cog.PokemonHPModal(self)
                await interaction.response.send_modal(modal)
                return False
            elif interaction.data.get("custom_id") == "cancel":
                await self.cog.show_offers_list(interaction, is_refresh=True)
                return False
            return True
        
        async def show_type_selection(self, interaction: discord.Interaction):
            self.current_step = 3
            embed = discord.Embed(
                title="🎮 Gegenangebot erstellen - Schritt 3/5",
                description=f"✅ **Name:** {self.pokemon_data['name']}\n✅ **KP:** {self.pokemon_data['hp']}\n\nWähle den Typ deines Pokemon:",
                color=0x3498db
            )
            embed.set_footer(text="Schritt 3 von 5: Typ auswählen")
            
            self.clear_items()
            self.add_item(TypeSelect(self))
            self.add_item(discord.ui.Button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary, custom_id="cancel", row=1))
            
            await interaction.response.edit_message(embed=embed, view=self)
        
        async def show_phase_selection(self, interaction: discord.Interaction):
            self.current_step = 4
            type_emoji = next((emoji for emoji, name in self.cog.pokemon_types.items() if name == self.pokemon_data['type']), "")
            
            embed = discord.Embed(
                title="🎮 Gegenangebot erstellen - Schritt 4/5",
                description=f"✅ **Name:** {self.pokemon_data['name']}\n✅ **KP:** {self.pokemon_data['hp']}\n✅ **Typ:** {type_emoji} {self.pokemon_data['type']}\n\nWähle die Phase deines Pokemon:",
                color=0x3498db
            )
            embed.set_footer(text="Schritt 4 von 5: Phase auswählen")
            
            self.clear_items()
            self.add_item(PhaseSelect(self))
            self.add_item(discord.ui.Button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary, custom_id="cancel", row=1))
            
            await interaction.response.edit_message(embed=embed, view=self)
        
        async def show_rarity_selection(self, interaction: discord.Interaction):
            self.current_step = 5
            type_emoji = next((emoji for emoji, name in self.cog.pokemon_types.items() if name == self.pokemon_data['type']), "")
            phase_emoji = next((emoji for emoji, name in self.cog.pokemon_phases.items() if name == self.pokemon_data['phase']), "")
            
            embed = discord.Embed(
                title="🎮 Gegenangebot erstellen - Schritt 5/5",
                description=f"✅ **Name:** {self.pokemon_data['name']}\n✅ **KP:** {self.pokemon_data['hp']}\n✅ **Typ:** {type_emoji} {self.pokemon_data['type']}\n✅ **Phase:** {phase_emoji} {self.pokemon_data['phase']}\n\nWähle die Seltenheit deines Pokemon:",
                color=0x3498db
            )
            embed.set_footer(text="Schritt 5 von 5: Seltenheit auswählen")
            
            self.clear_items()
            self.add_item(RaritySelect(self))
            self.add_item(discord.ui.Button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary, custom_id="cancel", row=1))
            
            await interaction.response.edit_message(embed=embed, view=self)
        
        async def finalize_offer(self, interaction: discord.Interaction):
            await self.create_counter_offer_message(interaction)
        
        async def create_counter_offer_message(self, interaction: discord.Interaction):
            """Erstellt die finale Gegenangebot-Nachricht"""
            
            # Hole die entsprechenden Emojis
            type_emoji = next((emoji for emoji, name in self.cog.pokemon_types.items() if name == self.pokemon_data['type']), "")
            phase_emoji = next((emoji for emoji, name in self.cog.pokemon_phases.items() if name == self.pokemon_data['phase']), "")
            rarity_emoji = next((emoji for emoji, name in self.cog.rarity_levels.items() if name == self.pokemon_data['rarity']), "")
            
            # Originales Angebot Emojis
            orig_type_emoji = next((emoji for emoji, name in self.cog.pokemon_types.items() if name == self.target_offer['type']), "")
            orig_phase_emoji = next((emoji for emoji, name in self.cog.pokemon_phases.items() if name == self.target_offer['phase']), "")
            orig_rarity_emoji = next((emoji for emoji, name in self.cog.rarity_levels.items() if name == self.target_offer['rarity']), "")
            
            embed = discord.Embed(
                title="🔄 Gegenangebot erstellt!",
                description=f"**{self.responding_user.display_name}** möchte mit **{self.target_offer['user'].display_name}** tauschen:",
                color=0x00ff00
            )
            
            # Originales Angebot
            embed.add_field(
                name="🎯 Gewünschtes Pokemon",
                value=f"**{self.target_offer['name']}** ({self.target_offer['hp']} KP)\n"
                      f"{orig_type_emoji} {self.target_offer['type']} | "
                      f"{orig_phase_emoji} {self.target_offer['phase']} | "
                      f"{orig_rarity_emoji} {self.target_offer['rarity']}",
                inline=False
            )
            
            # Gegenangebot
            embed.add_field(
                name="🎮 Angebotenes Pokemon",
                value=f"**{self.pokemon_data['name']}** ({self.pokemon_data['hp']} KP)\n"
                      f"{type_emoji} {self.pokemon_data['type']} | "
                      f"{phase_emoji} {self.pokemon_data['phase']} | "
                      f"{rarity_emoji} {self.pokemon_data['rarity']}",
                inline=False
            )
            
            embed.set_footer(text="Gegenangebot wird an den ursprünglichen Anbieter gesendet!")
            
            await interaction.response.edit_message(embed=embed, view=None)
            
            # Sende das Gegenangebot an den ursprünglichen Anbieter
            try:
                dm_embed = discord.Embed(
                    title="🔄 Neues Gegenangebot erhalten!",
                    description=f"**{self.responding_user.display_name}** möchte mit dir tauschen!",
                    color=0x3498db
                )
                
                dm_embed.add_field(
                    name="🎯 Dein Pokemon",
                    value=f"**{self.target_offer['name']}** ({self.target_offer['hp']} KP)\n"
                          f"{orig_type_emoji} {self.target_offer['type']} | "
                          f"{orig_phase_emoji} {self.target_offer['phase']} | "
                          f"{orig_rarity_emoji} {self.target_offer['rarity']}",
                    inline=False
                )
                
                dm_embed.add_field(
                    name=f"🎮 Angebot von {self.responding_user.display_name}",
                    value=f"**{self.pokemon_data['name']}** ({self.pokemon_data['hp']} KP)\n"
                          f"{type_emoji} {self.pokemon_data['type']} | "
                          f"{phase_emoji} {self.pokemon_data['phase']} | "
                          f"{rarity_emoji} {self.pokemon_data['rarity']}",
                    inline=False
                )
                
                dm_embed.add_field(
                    name="🔄 Entscheidung treffen",
                    value="Wähle eine Option:",
                    inline=False
                )
                
                # Erstelle die interaktive View mit Annehmen/Ablehnen Buttons
                response_view = CounterOfferResponseView(self.target_offer, self.pokemon_data, self.responding_user)
                
                await self.target_offer['user'].send(embed=dm_embed, view=response_view)
                
                # Bestätigung an den Absender
                await interaction.followup.send(
                    f"✅ Dein Gegenangebot wurde erfolgreich an **{self.target_offer['user'].display_name}** gesendet!",
                    ephemeral=True
                )
                
            except discord.Forbidden:
                await interaction.followup.send(
                    f"❌ Konnte das Gegenangebot nicht an {self.target_offer['user'].display_name} senden. "
                    f"Kontaktiere sie direkt: {self.target_offer['user'].mention}",
                    ephemeral=True
                )
        
        async def on_timeout(self):
            """Wird aufgerufen wenn die View timeout erreicht"""
            for item in self.children:
                item.disabled = True
    
    class FinalOfferView(discord.ui.View):
        """View für das finale Pokemon-Angebot"""
        
        def __init__(self, pokemon_data):
            super().__init__(timeout=3600)  # 1 Stunde für finale Angebote
            self.pokemon_data = pokemon_data
        
        @discord.ui.button(label="Interesse zeigen", style=discord.ButtonStyle.primary, emoji="💬")
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
        
        @discord.ui.button(label="Details", style=discord.ButtonStyle.secondary, emoji="📊")
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
            description="Willkommen beim Pokemon-Tausch System!\n\nWir führen dich Schritt für Schritt durch die Eingabe deines Pokemon-Angebots:",
            color=0x3498db
        )
        
        embed.add_field(
            name="📋 Ablauf",
            value="**Schritt 1:** 📛 Pokemon Name eingeben\n"
                  "**Schritt 2:** ❤️ KP (Kraftpunkte) eingeben\n"
                  "**Schritt 3:** 🏷️ Pokemon-Typ auswählen\n"
                  "**Schritt 4:** 🔄 Entwicklungsphase auswählen\n"
                  "**Schritt 5:** 💎 Seltenheitsstufe auswählen",
            inline=False
        )
        
        embed.add_field(
            name="💡 Hinweis",
            value="Nach jeder Eingabe gelangst du automatisch zum nächsten Schritt!",
            inline=False
        )
        
        embed.set_footer(text="Klicke 'Los geht's!' um zu beginnen")
        
        view = self.PokemonSequentialView(self)
        await ctx.send(embed=embed, view=view)
        await ctx.message.delete()
    
    async def show_offers_list(self, interaction: discord.Interaction, is_refresh=False):
        """Zeigt die Liste aller verfügbaren Angebote"""
        
        # Filtere Angebote nach der aktuellen Guild
        guild_offers = {
            offer_id: offer_data 
            for offer_id, offer_data in self.active_offers.items() 
            if offer_data.get('guild_id') == interaction.guild_id
        }
        
        if not guild_offers:
            embed = discord.Embed(
                title="📋 Keine Pokemon-Angebote verfügbar",
                description="Zurzeit gibt es keine aktiven Pokemon-Angebote auf diesem Server.\n\nVerwende `!bieten` um das erste Angebot zu erstellen!",
                color=0xff9900
            )
            embed.set_footer(text="Tipp: Mit !bieten kannst du ein eigenes Pokemon anbieten")
            
            if is_refresh:
                await interaction.response.edit_message(embed=embed, view=None)
            else:
                await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title="📋 Verfügbare Pokemon-Angebote",
            description=f"Hier sind alle **{len(guild_offers)}** verfügbaren Pokemon-Angebote auf diesem Server:",
            color=0x3498db
        )
        
        # Zeige die ersten 5 Angebote in der Beschreibung
        offer_list = []
        for i, (offer_id, offer_data) in enumerate(list(guild_offers.items())[:5]):
            type_emoji = next((emoji for emoji, name in self.pokemon_types.items() if name == offer_data['type']), "")
            rarity_emoji = next((emoji for emoji, name in self.rarity_levels.items() if name == offer_data['rarity']), "")
            
            offer_list.append(
                f"**#{offer_id}** {offer_data['name']} ({offer_data['hp']} KP) - {type_emoji} {offer_data['type']} {rarity_emoji}"
            )
        
        if offer_list:
            embed.add_field(
                name="🎯 Aktuelle Angebote (Auswahl)",
                value="\n".join(offer_list),
                inline=False
            )
        
        if len(guild_offers) > 5:
            embed.add_field(
                name="📌 Hinweis",
                value=f"Es gibt {len(guild_offers) - 5} weitere Angebote. Verwende das Dropdown-Menü um alle zu sehen!",
                inline=False
            )
        
        embed.add_field(
            name="💡 Wie es funktioniert",
            value="1. Wähle ein Angebot aus dem Dropdown-Menü\n"
                  "2. Entscheide ob du ein Gegenangebot erstellen oder direkt kontaktieren möchtest\n"
                  "3. Bei Gegenangeboten wirst du durch die Erstellung geführt",
            inline=False
        )
        
        embed.set_footer(text=f"Insgesamt {len(guild_offers)} Angebote verfügbar")
        
        view = OffersListView(guild_offers, self)
        
        if is_refresh:
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.send_message(embed=embed, view=view)
    
    @commands.command(name='angebote')
    async def list_offers(self, ctx):
        """Zeigt alle verfügbaren Pokemon-Angebote"""
        
        # Simuliere eine Interaction für die show_offers_list Methode
        class FakeInteraction:
            def __init__(self, ctx):
                self.guild_id = ctx.guild.id
                self.user = ctx.author
                self.channel = ctx.channel
            
            async def response_send_message(self, embed, view=None):
                await ctx.send(embed=embed, view=view)
        
        fake_interaction = FakeInteraction(ctx)
        
        # Filtere Angebote nach der aktuellen Guild
        guild_offers = {
            offer_id: offer_data 
            for offer_id, offer_data in self.active_offers.items() 
            if offer_data.get('guild_id') == ctx.guild.id
        }
        
        if not guild_offers:
            embed = discord.Embed(
                title="📋 Keine Pokemon-Angebote verfügbar",
                description="Zurzeit gibt es keine aktiven Pokemon-Angebote auf diesem Server.\n\nVerwende `!bieten` um das erste Angebot zu erstellen!",
                color=0xff9900
            )
            embed.set_footer(text="Tipp: Mit !bieten kannst du ein eigenes Pokemon anbieten")
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="📋 Verfügbare Pokemon-Angebote",
            description=f"Hier sind alle **{len(guild_offers)}** verfügbaren Pokemon-Angebote auf diesem Server:",
            color=0x3498db
        )
        
        # Zeige die ersten 5 Angebote in der Beschreibung
        offer_list = []
        for i, (offer_id, offer_data) in enumerate(list(guild_offers.items())[:5]):
            type_emoji = next((emoji for emoji, name in self.pokemon_types.items() if name == offer_data['type']), "")
            rarity_emoji = next((emoji for emoji, name in self.rarity_levels.items() if name == offer_data['rarity']), "")
            
            offer_list.append(
                f"**#{offer_id}** {offer_data['name']} ({offer_data['hp']} KP) - {type_emoji} {offer_data['type']} {rarity_emoji}"
            )
        
        if offer_list:
            embed.add_field(
                name="🎯 Aktuelle Angebote (Auswahl)",
                value="\n".join(offer_list),
                inline=False
            )
        
        if len(guild_offers) > 5:
            embed.add_field(
                name="📌 Hinweis",
                value=f"Es gibt {len(guild_offers) - 5} weitere Angebote. Verwende das Dropdown-Menü um alle zu sehen!",
                inline=False
            )
        
        embed.add_field(
            name="💡 Wie es funktioniert",
            value="1. Wähle ein Angebot aus dem Dropdown-Menü\n"
                  "2. Entscheide ob du ein Gegenangebot erstellen oder direkt kontaktieren möchtest\n"
                  "3. Bei Gegenangeboten wirst du durch die Erstellung geführt",
            inline=False
        )
        
        embed.set_footer(text=f"Insgesamt {len(guild_offers)} Angebote verfügbar")
        
        view = OffersListView(guild_offers, self)
        await ctx.send(embed=embed, view=view)
        await ctx.message.delete()
    
    class WishTradeOfferView(discord.ui.View):
        """View für das Tauschangebot zu einem Wunsch"""
        
        def __init__(self, cog, wish_data, user):
            super().__init__(timeout=300)
            self.cog = cog
            self.wish_data = wish_data
            self.user = user
            self.pokemon_data = {
                'name': None,
                'type': None,
                'hp': None,
                'phase': None,
                'rarity': None,
                'user': user
            }
            self.current_step = 1
        
        @discord.ui.button(label="🚀 Tauschangebot erstellen", style=discord.ButtonStyle.primary, emoji="🚀")
        async def start_offer(self, interaction: discord.Interaction, button: discord.ui.Button):
            _ = button  # Ignoriere unused argument warning
            # Starte mit Name-Eingabe
            modal = self.cog.PokemonNameModal(self)
            await interaction.response.send_modal(modal)
        
        @discord.ui.button(label="Abbrechen", style=discord.ButtonStyle.secondary, emoji="❌")
        async def cancel_offer(self, interaction: discord.Interaction, button: discord.ui.Button):
            _ = button  # Ignoriere unused argument warning
            # Gehe zurück zur Wunsch-Option
            offer_option_view = WishOfferOptionView(self.cog, self.wish_data)
            
            # Erstelle das ursprüngliche Embed neu
            type_emoji = next((emoji for emoji, name in self.cog.pokemon_types.items() if name == self.wish_data['type']), "")
            phase_emoji = next((emoji for emoji, name in self.cog.pokemon_phases.items() if name == self.wish_data['phase']), "")
            rarity_emoji = next((emoji for emoji, name in self.cog.rarity_levels.items() if name == self.wish_data['rarity']), "")
            
            embed = discord.Embed(
                title="🌟 Pokemon-Wunsch fast fertig!",
                description="Dein Wunsch-Pokemon ist vollständig definiert:",
                color=0xffd700
            )
            
            embed.add_field(
                name="🎯 Gesuchtes Pokemon",
                value=f"**{self.wish_data['name']}** ({self.wish_data['hp']} KP)\n"
                      f"{type_emoji} {self.wish_data['type']} | "
                      f"{phase_emoji} {self.wish_data['phase']} | "
                      f"{rarity_emoji} {self.wish_data['rarity']}",
                inline=False
            )
            
            embed.add_field(
                name="🔄 Optionaler nächster Schritt",
                value="Möchtest du direkt ein Pokemon zum Tausch anbieten?",
                inline=False
            )
            
            await interaction.response.edit_message(embed=embed, view=offer_option_view)
        
        # Alle Methoden von PokemonSequentialView übernehmen
        async def show_hp_input(self, interaction: discord.Interaction):
            self.current_step = 2
            embed = discord.Embed(
                title="🎮 Tauschangebot erstellen - Schritt 2/5",
                description=f"✅ **Name:** {self.pokemon_data['name']}\n\nJetzt gib die KP deines Pokemon ein:",
                color=0x3498db
            )
            embed.set_footer(text="Schritt 2 von 5: KP eingeben")
            
            self.clear_items()
            self.add_item(discord.ui.Button(label="❤️ KP eingeben", style=discord.ButtonStyle.primary, custom_id="hp_input"))
            self.add_item(discord.ui.Button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary, custom_id="cancel"))
            
            await interaction.response.edit_message(embed=embed, view=self)
        
        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            if interaction.data.get("custom_id") == "hp_input":
                modal = self.cog.PokemonHPModal(self)
                await interaction.response.send_modal(modal)
                return False
            elif interaction.data.get("custom_id") == "cancel":
                await self.cancel_offer(interaction, None)
                return False
            return True
        
        async def show_type_selection(self, interaction: discord.Interaction):
            self.current_step = 3
            embed = discord.Embed(
                title="🎮 Tauschangebot erstellen - Schritt 3/5",
                description=f"✅ **Name:** {self.pokemon_data['name']}\n✅ **KP:** {self.pokemon_data['hp']}\n\nWähle den Typ deines Pokemon:",
                color=0x3498db
            )
            embed.set_footer(text="Schritt 3 von 5: Typ auswählen")
            
            self.clear_items()
            self.add_item(TypeSelect(self))
            self.add_item(discord.ui.Button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary, custom_id="cancel", row=1))
            
            await interaction.response.edit_message(embed=embed, view=self)
        
        async def show_phase_selection(self, interaction: discord.Interaction):
            self.current_step = 4
            type_emoji = next((emoji for emoji, name in self.cog.pokemon_types.items() if name == self.pokemon_data['type']), "")
            
            embed = discord.Embed(
                title="🎮 Tauschangebot erstellen - Schritt 4/5",
                description=f"✅ **Name:** {self.pokemon_data['name']}\n✅ **KP:** {self.pokemon_data['hp']}\n✅ **Typ:** {type_emoji} {self.pokemon_data['type']}\n\nWähle die Phase deines Pokemon:",
                color=0x3498db
            )
            embed.set_footer(text="Schritt 4 von 5: Phase auswählen")
            
            self.clear_items()
            self.add_item(PhaseSelect(self))
            self.add_item(discord.ui.Button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary, custom_id="cancel", row=1))
            
            await interaction.response.edit_message(embed=embed, view=self)
        
        async def show_rarity_selection(self, interaction: discord.Interaction):
            self.current_step = 5
            type_emoji = next((emoji for emoji, name in self.cog.pokemon_types.items() if name == self.pokemon_data['type']), "")
            phase_emoji = next((emoji for emoji, name in self.cog.pokemon_phases.items() if name == self.pokemon_data['phase']), "")
            
            embed = discord.Embed(
                title="🎮 Tauschangebot erstellen - Schritt 5/5",
                description=f"✅ **Name:** {self.pokemon_data['name']}\n✅ **KP:** {self.pokemon_data['hp']}\n✅ **Typ:** {type_emoji} {self.pokemon_data['type']}\n✅ **Phase:** {phase_emoji} {self.pokemon_data['phase']}\n\nWähle die Seltenheit deines Pokemon:",
                color=0x3498db
            )
            embed.set_footer(text="Schritt 5 von 5: Seltenheit auswählen")
            
            self.clear_items()
            self.add_item(RaritySelect(self))
            self.add_item(discord.ui.Button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary, custom_id="cancel", row=1))
            
            await interaction.response.edit_message(embed=embed, view=self)
        
        async def finalize_offer(self, interaction: discord.Interaction):
            # Füge das Tauschangebot zum Wunsch hinzu
            self.wish_data['offer_included'] = True
            self.wish_data['offer_data'] = self.pokemon_data
            self.wish_data['user'] = interaction.user
            
            await self.cog.create_final_wish(interaction, self.wish_data)
    
    async def create_final_wish(self, interaction: discord.Interaction, wish_data):
        """Erstellt den finalen Pokemon-Wunsch"""
        
        # Erstelle eine eindeutige Wunsch-ID
        self.wish_counter += 1
        wish_id = self.wish_counter
        
        # Speichere den Wunsch mit zusätzlichen Metadaten
        final_wish_data = wish_data.copy()
        final_wish_data['wish_id'] = wish_id
        final_wish_data['created_at'] = interaction.created_at
        final_wish_data['guild_id'] = interaction.guild_id
        final_wish_data['channel_id'] = interaction.channel_id
        
        self.active_wishes[wish_id] = final_wish_data
        
        # Hole die entsprechenden Emojis für den Wunsch
        wish_type_emoji = next((emoji for emoji, name in self.pokemon_types.items() if name == wish_data['type']), "")
        wish_phase_emoji = next((emoji for emoji, name in self.pokemon_phases.items() if name == wish_data['phase']), "")
        wish_rarity_emoji = next((emoji for emoji, name in self.rarity_levels.items() if name == wish_data['rarity']), "")
        
        if wish_data.get('offer_included', False) and wish_data.get('offer_data'):
            # Wunsch mit Tauschangebot
            offer_data = wish_data['offer_data']
            offer_type_emoji = next((emoji for emoji, name in self.pokemon_types.items() if name == offer_data['type']), "")
            offer_phase_emoji = next((emoji for emoji, name in self.pokemon_phases.items() if name == offer_data['phase']), "")
            offer_rarity_emoji = next((emoji for emoji, name in self.rarity_levels.items() if name == offer_data['rarity']), "")
            
            embed = discord.Embed(
                title="🌟 Neuer Pokemon-Wunsch mit Tauschangebot!",
                description=f"**{wish_data['user'].display_name}** sucht ein Pokemon und bietet einen Tausch an:",
                color=0xffd700
            )
            
            embed.add_field(
                name="🎯 Gesuchtes Pokemon",
                value=f"**{wish_data['name']}** ({wish_data['hp']} KP)\n"
                      f"{wish_type_emoji} {wish_data['type']} | "
                      f"{wish_phase_emoji} {wish_data['phase']} | "
                      f"{wish_rarity_emoji} {wish_data['rarity']}",
                inline=False
            )
            
            embed.add_field(
                name="🎮 Angebotenes Pokemon",
                value=f"**{offer_data['name']}** ({offer_data['hp']} KP)\n"
                      f"{offer_type_emoji} {offer_data['type']} | "
                      f"{offer_phase_emoji} {offer_data['phase']} | "
                      f"{offer_rarity_emoji} {offer_data['rarity']}",
                inline=False
            )
            
        else:
            # Nur Wunsch ohne Tauschangebot
            embed = discord.Embed(
                title="🌟 Neuer Pokemon-Wunsch!",
                description=f"**{wish_data['user'].display_name}** sucht ein Pokemon:",
                color=0xffd700
            )
            
            embed.add_field(
                name="🎯 Gesuchtes Pokemon",
                value=f"**{wish_data['name']}** ({wish_data['hp']} KP)\n"
                      f"{wish_type_emoji} {wish_data['type']} | "
                      f"{wish_phase_emoji} {wish_data['phase']} | "
                      f"{wish_rarity_emoji} {wish_data['rarity']}",
                inline=False
            )
        
        embed.add_field(
            name="👤 Suchender",
            value=wish_data['user'].mention,
            inline=True
        )
        
        embed.set_thumbnail(url=wish_data['user'].display_avatar.url)
        embed.set_footer(text=f"Wunsch-ID: #{wish_id} | Kontaktiere {wish_data['user'].display_name} für einen Tausch!")
        
        # Erstelle View für finale Wunsch-Interaktionen
        final_view = self.FinalWishView(final_wish_data)
        
        await interaction.response.edit_message(embed=embed, view=final_view)
    
    class FinalWishView(discord.ui.View):
        """View für das finale Wunsch-Angebot"""
        
        def __init__(self, wish_data):
            super().__init__(timeout=3600)  # 1 Stunde für finale Wünsche
            self.wish_data = wish_data
        
        @discord.ui.button(label="💬 Kontakt aufnehmen", style=discord.ButtonStyle.primary, emoji="💬")
        async def contact_wisher(self, interaction: discord.Interaction, button: discord.ui.Button):
            _ = button  # Ignoriere unused argument warning
            
            if interaction.user.id == self.wish_data['user'].id:
                await interaction.response.send_message(
                    "❌ Du kannst nicht deinen eigenen Wunsch kontaktieren!", 
                    ephemeral=True
                )
                return
            
            # Sende private Nachricht an den Wünschenden
            try:
                dm_embed = discord.Embed(
                    title="🔔 Jemand ist interessiert an deinem Wunsch!",
                    description=f"**{interaction.user.display_name}** hat Interesse an deinem Pokemon-Wunsch gezeigt!",
                    color=0x00ff00
                )
                
                dm_embed.add_field(
                    name="🎯 Dein Wunsch",
                    value=f"**{self.wish_data['name']}** ({self.wish_data['hp']} KP)",
                    inline=False
                )
                
                dm_embed.add_field(
                    name="Kontakt",
                    value=f"Schreibe {interaction.user.mention} eine private Nachricht um den Tausch zu besprechen!",
                    inline=False
                )
                
                await self.wish_data['user'].send(embed=dm_embed)
                
                await interaction.response.send_message(
                    f"✅ Ich habe {self.wish_data['user'].display_name} über dein Interesse informiert! "
                    f"Sie werden sich bei dir melden.", 
                    ephemeral=True
                )
                
            except discord.Forbidden:
                await interaction.response.send_message(
                    f"❌ Ich konnte {self.wish_data['user'].display_name} keine private Nachricht senden. "
                    f"Kontaktiere sie direkt: {self.wish_data['user'].mention}",
                    ephemeral=True
                )
        
        @discord.ui.button(label="📊 Details", style=discord.ButtonStyle.secondary, emoji="📊")
        async def show_details(self, interaction: discord.Interaction, button: discord.ui.Button):
            _ = button  # Ignoriere unused argument warning
            
            details_embed = discord.Embed(
                title=f"📊 Details zu Wunsch #{self.wish_data['wish_id']}",
                color=0xffd700
            )
            
            details_embed.add_field(name="Gesuchtes Pokemon", value=self.wish_data['name'], inline=True)
            details_embed.add_field(name="KP", value=self.wish_data['hp'], inline=True)
            details_embed.add_field(name="Typ", value=self.wish_data['type'], inline=True)
            details_embed.add_field(name="Phase", value=self.wish_data['phase'], inline=True)
            details_embed.add_field(name="Seltenheit", value=self.wish_data['rarity'], inline=True)
            details_embed.add_field(name="Wünschender", value=self.wish_data['user'].display_name, inline=True)
            
            if self.wish_data.get('offer_included', False) and self.wish_data.get('offer_data'):
                offer_data = self.wish_data['offer_data']
                details_embed.add_field(
                    name="Angebotenes Pokemon",
                    value=f"{offer_data['name']} ({offer_data['hp']} KP) - {offer_data['type']} | {offer_data['phase']} | {offer_data['rarity']}",
                    inline=False
                )
            
            await interaction.response.send_message(embed=details_embed, ephemeral=True)
    
    @commands.command(name='wünschen')
    async def create_wish(self, ctx):
        """Erstelle einen Pokemon-Wunsch"""
        
        embed = discord.Embed(
            title="🌟 Pokemon-Wunsch erstellen",
            description="Willkommen beim Pokemon-Wunsch System!\n\nErstelle einen Wunsch für ein Pokemon, das du suchst:",
            color=0xffd700
        )
        
        embed.add_field(
            name="📋 Ablauf",
            value="**Schritt 1:** 📛 Pokemon Name eingeben\n"
                  "**Schritt 2:** ❤️ KP (Kraftpunkte) eingeben\n"
                  "**Schritt 3:** 🏷️ Pokemon-Typ auswählen\n"
                  "**Schritt 4:** 🔄 Entwicklungsphase auswählen\n"
                  "**Schritt 5:** 💎 Seltenheitsstufe auswählen\n"
                  "**Optional:** 🎮 Tauschangebot hinzufügen",
            inline=False
        )
        
        embed.add_field(
            name="💡 Hinweis",
            value="Du kannst optional direkt ein Pokemon zum Tausch anbieten!\n"
                  "Nach jeder Eingabe gelangst du automatisch zum nächsten Schritt.",
            inline=False
        )
        
        embed.set_footer(text="Klicke 'Wunsch erstellen' um zu beginnen")
        
        view = WishSequentialView(self)
        await ctx.send(embed=embed, view=view)
        await ctx.message.delete()
    
    @commands.command(name='wünsche')
    async def list_wishes(self, ctx):
        """Zeige alle verfügbaren Pokemon-Wünsche an"""
        await self.show_wishes_list(ctx)
    
    async def show_wishes_list(self, interaction_or_ctx, is_refresh=False):
        """Zeige die Liste aller verfügbaren Wünsche"""
        
        # Filtere Wünsche nach Guild (Server)
        if hasattr(interaction_or_ctx, 'guild'):
            guild_id = interaction_or_ctx.guild.id
        else:
            guild_id = interaction_or_ctx.guild.id
        
        guild_wishes = {}
        for wish_id, wish_data in self.active_wishes.items():
            if wish_data.get('guild_id') == guild_id:
                guild_wishes[wish_id] = wish_data
        
        if not guild_wishes:
            embed = discord.Embed(
                title="📋 Keine Wünsche verfügbar",
                description="Aktuell sind keine Pokemon-Wünsche verfügbar.\n\n"
                           "💡 **Erstelle deinen eigenen Wunsch:**\n"
                           "`!wünschen` - Neuen Wunsch erstellen",
                color=0xff9900
            )
            
            embed.add_field(
                name="🎮 Verfügbare Befehle",
                value="`!bieten` - Pokemon anbieten\n"
                      "`!angebote` - Verfügbare Angebote anzeigen\n"
                      "`!wünschen` - Pokemon-Wunsch erstellen\n"
                      "`!pokemon_help` - Vollständige Hilfe",
                inline=False
            )
            
            if is_refresh:
                await interaction_or_ctx.response.edit_message(embed=embed, view=None)
            else:
                await interaction_or_ctx.send(embed=embed)
            return
        
        # Erstelle Embed für verfügbare Wünsche
        embed = discord.Embed(
            title="🌟 Verfügbare Pokemon-Wünsche",
            description=f"**{len(guild_wishes)}** Wünsche verfügbar!\n"
                       "Wähle einen Wunsch aus dem Dropdown-Menü:",
            color=0xffd700
        )
        
        # Zähle Wünsche mit und ohne Tauschangebot
        wishes_with_offer = sum(1 for wish in guild_wishes.values() if wish.get('offer_included', False))
        wishes_only = len(guild_wishes) - wishes_with_offer
        
        embed.add_field(
            name="📊 Übersicht",
            value=f"🌟 **{wishes_only}** Reine Wünsche\n"
                  f"🎮 **{wishes_with_offer}** Wünsche mit Tauschangebot",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Aktionen",
            value="• **Wunsch auswählen** - Dropdown verwenden\n"
                  "• **🎮 Mit Angebot** - Kann direkt angenommen werden\n"
                  "• **🌟 Nur Wunsch** - Angebot erstellen",
            inline=True
        )
        
        embed.add_field(
            name="💡 Legende",
            value="🌟 = Reiner Wunsch\n"
                  "🎮 = Mit Tauschangebot",
            inline=True
        )
        
        embed.set_footer(text="Tipp: Verwende !wünschen um einen eigenen Wunsch zu erstellen")
        
        # Erstelle View mit Dropdown und Buttons
        view = WishesListView(guild_wishes, self)
        
        if is_refresh:
            await interaction_or_ctx.response.edit_message(embed=embed, view=view)
        else:
            await interaction_or_ctx.send(embed=embed, view=view)
            # Delete the command message if called from a command context
            if hasattr(interaction_or_ctx, 'message'):
                await interaction_or_ctx.message.delete()
    
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
                  "`!angebote` - Zeige alle verfügbaren Angebote\n"
                  "`!wünschen` - Erstelle einen Pokemon-Wunsch (optional mit Tauschangebot)\n"
                  "`!wünsche` - Zeige alle verfügbaren Pokemon-Wünsche\n"
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
        await ctx.message.delete()
    
    def create_wish_counter_offer_view(self, target_wish, responding_user):
        """Factory-Methode um Reihenfolge-Probleme zu vermeiden"""
        view = self.PokemonSequentialView(self)
        view.target_wish = target_wish
        view.responding_user = responding_user
        return view
    
    def remove_offer(self, offer_id):
        """Entfernt ein Angebot aus der aktiven Liste"""
        if offer_id in self.active_offers:
            del self.active_offers[offer_id]
            return True
        return False
    
    def remove_wish(self, wish_id):
        """Entfernt einen Wunsch aus der aktiven Liste"""
        if wish_id in self.active_wishes:
            del self.active_wishes[wish_id]
            return True
        return False

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(Pokemon(bot))
