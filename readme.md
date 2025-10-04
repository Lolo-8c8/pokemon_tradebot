# Discord Bot - Python

Ein vollständiges Grundgerüst für einen Discord Bot in Python mit discord.py.

## 🚀 Features

- **Modulare Struktur** mit Cogs für bessere Organisation
- **Pokemon-Tausch System** mit interaktiven Auswahlmöglichkeiten
- **Umfassende Befehle** für allgemeine und Moderationszwecke
- **Konfigurierbare Einstellungen** über Umgebungsvariablen
- **Fehlerbehandlung** und Logging
- **Embed-Nachrichten** für bessere Benutzererfahrung

## 📁 Projektstruktur

```
DiscordBot/
├── bot.py              # Haupt-Bot-Datei
├── config.py           # Konfigurationsklasse
├── pyproject.toml      # Python-Projektkonfiguration
├── .env.example        # Beispiel-Umgebungsvariablen
├── cogs/              # Modulare Befehlsgruppen
│   ├── __init__.py
│   ├── general.py      # Allgemeine Befehle
│   ├── moderation.py   # Moderationsbefehle
│   └── pokemon.py      # Pokemon-Tausch System
└── readme.md          # Diese Datei
```

## 🛠️ Installation

### 1. Repository klonen
```bash
git clone <repository-url>
cd DiscordBot
```

### 2. Python-Abhängigkeiten installieren
```bash
# Mit uv (empfohlen)
uv sync

# Oder mit pip
pip install -e .
```

### 3. Umgebungsvariablen konfigurieren
```bash
cp .env.example .env
```

Bearbeite die `.env` Datei und füge deinen Discord Bot Token hinzu:
```
DISCORD_TOKEN=dein_discord_bot_token_hier
PREFIX=!
OWNER_ID=deine_discord_user_id_hier
```

### 4. Discord Bot erstellen

1. Gehe zu [Discord Developer Portal](https://discord.com/developers/applications)
2. Erstelle eine neue Application
3. Gehe zum "Bot" Tab
4. Erstelle einen Bot und kopiere den Token
5. Füge den Token in deine `.env` Datei ein

### 5. Bot-Berechtigungen einstellen

Stelle sicher, dass dein Bot folgende Berechtigungen hat:
- Send Messages
- Manage Messages
- Kick Members
- Ban Members
- Manage Roles
- Read Message History

## 🚀 Bot starten

### **Empfohlener Weg (mit Startup-Check):**
```bash
uv run python start.py
```

### **Direkter Start:**
```bash
uv run python bot.py
```

### **Mit pip:**
```bash
python bot.py
```

## 📋 Verfügbare Befehle

### Allgemeine Befehle (`!help` für vollständige Liste)
- `!ping` - Bot-Latenz anzeigen
- `!info` - Bot-Informationen
- `!hello` - Begrüßung
- `!8ball <frage>` - Magic 8-Ball
- `!roll [seiten]` - Würfel werfen
- `!choose <option1, option2, ...>` - Zufällige Auswahl
- `!poll <frage>` - Ja/Nein-Umfrage erstellen
- `!avatar [mitglied]` - Avatar anzeigen
- `!serverinfo` - Server-Informationen

### Pokemon-Tausch System
- `!bieten` - Pokemon zum Tausch anbieten (interaktives Menü)
- `!pokemon_help` - Hilfe zum Pokemon-Tausch System

#### Pokemon-Eigenschaften:
- **Typen**: 🔥 Feuer, 🌊 Wasser, ⚡ Elektro, 🌿 Pflanze, 👊 Kampf, 💜 Liebe, 🐉 Drachen, 🌙 Unlicht
- **Phasen**: 🥚 Basis, 🐣 Phase 1, 🐤 Phase 2, 🦅 Phase 3
- **Seltenheit**: ⚪ Häufig, 🔷 Nicht so häufig, ⭐ Selten, 🌟 Doppelselten, 🏆 Illustrationskarte

### Moderationsbefehle (nur für Moderatoren)
- `!kick <mitglied> [grund]` - Mitglied kicken
- `!ban <mitglied> [grund]` - Mitglied bannen
- `!unban <username#discriminator>` - Mitglied entbannen
- `!mute <mitglied> [grund]` - Mitglied stummschalten
- `!unmute <mitglied>` - Stummschaltung aufheben
- `!clear <anzahl>` - Nachrichten löschen
- `!warn <mitglied> [grund]` - Mitglied verwarnen

## 🔧 Anpassung

### Neue Befehle hinzufügen
1. Erstelle eine neue Datei in `cogs/`
2. Erstelle eine Klasse, die von `commands.Cog` erbt
3. Füge Befehle als Methoden hinzu
4. Registriere den Cog in `bot.py`

### Beispiel für einen neuen Cog:
```python
import discord
from discord.ext import commands

class MeinCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='meinbefehl')
    async def mein_befehl(self, ctx):
        await ctx.send('Hallo!')

async def setup(bot):
    await bot.add_cog(MeinCog(bot))
```

## 🐛 Fehlerbehebung

### Bot startet nicht
- Überprüfe, ob der Discord Token korrekt ist
- Stelle sicher, dass alle Abhängigkeiten installiert sind
- Überprüfe die Logs auf Fehlermeldungen

### Bot antwortet nicht
- Überprüfe, ob der Bot die richtigen Berechtigungen hat
- Stelle sicher, dass der Bot online ist
- Überprüfe den Command-Prefix

### Berechtigungsfehler
- Stelle sicher, dass der Bot die notwendigen Rollen hat
- Überprüfe die Server-Berechtigungen
- Stelle sicher, dass der Bot über den Benutzer verfügen kann

## 📝 Lizenz

Dieses Projekt steht unter der MIT-Lizenz.

## 🤝 Beitragen

Beiträge sind willkommen! Bitte erstelle einen Pull Request oder öffne ein Issue.

## 📞 Support

Bei Fragen oder Problemen erstelle bitte ein Issue im Repository.