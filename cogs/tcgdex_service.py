"""
TCGdex API Service
Service-Klasse für Interaktionen mit der TCGdex REST API
"""
import aiohttp
import asyncio
import logging
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

class TCGdexService:
    """Service-Klasse für TCGdex API-Requests"""
    
    BASE_URL = "https://api.tcgdex.net/v2/de"
    TIMEOUT = 10  # Sekunden
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Lazy initialization des aiohttp Sessions"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.TIMEOUT)
            )
        return self.session
    
    async def close(self):
        """Schließt die aiohttp Session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _request(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """
        Führt einen GET-Request zur TCGdex API aus
        
        Args:
            endpoint: API-Endpunkt (z.B. "/sets" oder "/cards/base1-4")
        
        Returns:
            JSON-Response als Dict oder None bei Fehler
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            session = await self._get_session()
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                elif response.status == 404:
                    logger.warning("Resource not found: %s", url)
                    return None
                else:
                    logger.error("API request failed: %s - Status %s", url, response.status)
                    return None
        except aiohttp.ClientError as e:
            logger.error("Network error during API request to %s: %s", url, e)
            return None
        except asyncio.TimeoutError:
            logger.error("Timeout during API request to %s", url)
            return None
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Unexpected error during API request to %s: %s", url, e)
            return None
    
    async def get_all_sets(self) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Ruft alle Sets ab
        
        Returns:
            Tuple von (Liste aller Sets, Error-Message falls vorhanden)
        """
        data = await self._request("/sets")
        if isinstance(data, list):
            if len(data) == 0:
                return [], "Die API hat eine leere Liste zurückgegeben"
            return data, None
        elif data is None:
            return [], "API-Anfrage fehlgeschlagen - Server nicht erreichbar oder ungültige Antwort"
        else:
            logger.warning("Unerwartetes Datenformat von API: %s", type(data))
            return [], f"Unerwartetes Datenformat von API: {type(data).__name__}"
    
    async def get_sets_by_year(self, year: int) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Filtert Sets nach Erscheinungsjahr
        
        Der /sets Endpunkt gibt keine releaseDate zurück, daher müssen wir
        für jedes Set den detaillierten Endpunkt /sets/{set_id} aufrufen.
        
        Args:
            year: Das Jahr, nach dem gefiltert werden soll (z.B. 2023)
        
        Returns:
            Tuple von (Liste von Sets aus dem angegebenen Jahr, Error-Message falls vorhanden)
        """
        all_sets, error = await self.get_all_sets()
        
        if error:
            return [], error
        
        if len(all_sets) == 0:
            return [], "Es wurden keine Sets von der API zurückgegeben"
        
        logger.info("Gefundene Sets gesamt: %d, Filtere nach Jahr: %d", len(all_sets), year)
        
        # Rufe für jedes Set die detaillierten Informationen ab
        # (da /sets keine releaseDate enthält, brauchen wir /sets/{id})
        
        async def fetch_set_details(set_brief: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            """Holt detaillierte Set-Informationen mit releaseDate"""
            set_id = set_brief.get("id")
            if not set_id:
                return None
            
            detailed_set = await self.get_set(set_id)
            return detailed_set
        
        # Rufe Set-Details parallel ab (max 10 gleichzeitig für Performance)
        filtered_sets = []
        available_years = set()
        
        # Teile Sets in Chunks für Batch-Processing
        chunk_size = 10
        for i in range(0, len(all_sets), chunk_size):
            chunk = all_sets[i:i + chunk_size]
            
            # Rufe Set-Details parallel ab
            tasks = [fetch_set_details(set_brief) for set_brief in chunk]
            detailed_sets = await asyncio.gather(*tasks, return_exceptions=True)
            
            for detailed_set in detailed_sets:
                # Skip Fehler oder None
                if detailed_set is None or isinstance(detailed_set, Exception):
                    continue
                
                # Debug: Log Set-Struktur für erste 3 Sets, um zu sehen was die API zurückgibt
                if len(filtered_sets) < 3 and isinstance(detailed_set, dict):
                    set_id_debug = detailed_set.get("id", "unknown")
                    logger.debug("Set-Daten für %s: keys=%s", 
                               set_id_debug, 
                               list(detailed_set.keys()))
                    logger.debug("  - symbol: %s", detailed_set.get("symbol", "NOT_FOUND"))
                    logger.debug("  - logo: %s", detailed_set.get("logo", "NOT_FOUND"))
                
                release_date = detailed_set.get("releaseDate", "")
                
                if not release_date:
                    continue
                
                # Extrahiere Jahr aus releaseDate (Format: "yyyy-mm-dd")
                try:
                    release_date_str = str(release_date)
                    year_part = release_date_str.split("-")[0]
                    
                    # Sammle verfügbare Jahre für Fehlermeldung
                    if year_part.isdigit():
                        available_years.add(year_part)
                    
                    # Prüfe ob das extrahierte Jahr mit dem gesuchten Jahr übereinstimmt
                    if year_part.isdigit() and int(year_part) == year:
                        filtered_sets.append(detailed_set)
                        logger.debug("Set gefunden: %s (Release: %s)", detailed_set.get("name", "Unbekannt"), release_date)
                except (AttributeError, IndexError, ValueError) as e:
                    logger.debug("Set übersprungen (ungültiges releaseDate): %s - %s", detailed_set.get("name", "Unbekannt"), e)
                    continue
        
        if len(filtered_sets) == 0:
            years_str = ", ".join(sorted(available_years)) if available_years else "keine Daten verfügbar"
            return [], f"Keine Sets für das Jahr **{year}** gefunden. Verfügbare Jahre (Beispiele): {years_str}"
        
        # Sortiere nach Release-Datum (neueste zuerst)
        filtered_sets.sort(
            key=lambda x: x.get("releaseDate", ""),
            reverse=True
        )
        
        logger.info("Gefilterte Sets für Jahr %d: %d", year, len(filtered_sets))
        return filtered_sets, None
    
    async def get_set(self, set_id: str) -> Optional[Dict[str, Any]]:
        """
        Ruft Details eines spezifischen Sets ab
        
        Args:
            set_id: Die Set-ID (z.B. "base1", "swsh3")
        
        Returns:
            Set-Daten oder None wenn nicht gefunden
        """
        return await self._request(f"/sets/{set_id}")
    
    async def get_card(self, set_id: str, card_number: str) -> Optional[Dict[str, Any]]:
        """
        Ruft Details einer spezifischen Karte ab
        
        Args:
            set_id: Die Set-ID (z.B. "base1")
            card_number: Die Kartennummer (z.B. "4")
        
        Returns:
            Karten-Daten oder None wenn nicht gefunden
        """
        card_id = f"{set_id}-{card_number}"
        return await self._request(f"/cards/{card_id}")
    
    def extract_card_info(self, card_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrahiert relevante Informationen aus den Karten-Daten
        
        Args:
            card_data: Die rohen Karten-Daten von der API
        
        Returns:
            Dict mit extrahierten Informationen:
            - name: Kartenname
            - hp: KP-Wert
            - types: Liste der Typen
            - set_name: Name des Sets
            - set_symbol: URL zum Set-Symbol
            - card_number: Kartennummer
            - image: URL zum Kartenbild
            - cardmarket_price: Cardmarket Durchschnittspreis
        """
        if not card_data:
            return {}
        
        # Extrahiere HP
        hp = card_data.get("hp")
        if isinstance(hp, str):
            # Manche Karten haben HP als String "120" oder "None"
            try:
                hp = int(hp) if hp and hp.lower() != "none" else None
            except (ValueError, AttributeError):
                hp = None
        elif hp is not None:
            hp = int(hp)
        
        # Extrahiere Typen
        types = []
        card_type = card_data.get("types")
        if isinstance(card_type, list):
            types = card_type
        elif isinstance(card_type, str):
            types = [card_type]
        
        # Extrahiere Set-Informationen
        set_info = card_data.get("set", {})
        set_name = set_info.get("name", "") if isinstance(set_info, dict) else ""
        # Versuche zuerst symbol, dann logo als Fallback
        set_symbol = (set_info.get("symbol", "") or set_info.get("logo", "")) if isinstance(set_info, dict) else ""
        
        # Extrahiere Kartennummer
        card_number = card_data.get("number", "")
        
        # Extrahiere Bilder
        images = card_data.get("image", "")
        if isinstance(images, dict):
            # Falls image ein Dict ist, nimm die größte Version
            image_url = images.get("large") or images.get("small") or ""
        elif isinstance(images, str):
            image_url = images
        else:
            image_url = ""
        
        # Extrahiere Cardmarket-Preis
        cardmarket_price = None
        tcgplayer = card_data.get("tcgplayer", {})
        if isinstance(tcgplayer, dict):
            prices = tcgplayer.get("prices", {})
            if isinstance(prices, dict):
                # Prüfe verschiedene Preis-Typen
                for price_type in ["normal", "holofoil", "reverseHolofoil", "1stEditionHolofoil"]:
                    price_data = prices.get(price_type, {})
                    if isinstance(price_data, dict):
                        market_price = price_data.get("market", 0) or price_data.get("averageSellPrice", 0)
                        if market_price:
                            cardmarket_price = float(market_price)
                            break
        
        # Alternative: Prüfe direkt cardmarket Feld falls vorhanden
        if not cardmarket_price:
            cardmarket = card_data.get("cardmarket", {})
            if isinstance(cardmarket, dict):
                prices = cardmarket.get("prices", {})
                if isinstance(prices, dict):
                    market_price = prices.get("averageSellPrice", 0)
                    if market_price:
                        cardmarket_price = float(market_price)
        
        return {
            "name": card_data.get("name", ""),
            "hp": hp,
            "types": types,
            "set_name": set_name,
            "set_symbol": set_symbol,
            "card_number": str(card_number),
            "image": image_url,
            "cardmarket_price": cardmarket_price
        }

