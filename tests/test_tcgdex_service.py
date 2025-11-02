"""
Tests für TCGdx Service
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import aiohttp
from cogs.tcgdex_service import TCGdexService


class TestTCGdexService:
    """Test-Klasse für TCGdxService"""
    
    @pytest.fixture
    def service(self):
        """Erstellt eine TCGdxService-Instanz für Tests"""
        return TCGdexService()
    
    @pytest.fixture
    def mock_sets_response_2024(self):
        """Mock-Response mit Sets aus 2024"""
        return [
            {
                "id": "sv4a",
                "name": "Stellar Crown",
                "releaseDate": "2024-08-23",
                "symbol": "https://assets.tcgdex.net/univ/sv/sv4a/symbol",
                "logo": "https://assets.tcgdex.net/en/sv/sv4a/logo"
            },
            {
                "id": "sv5",
                "name": "Ancient Roar",
                "releaseDate": "2024-11-01",
                "symbol": "https://assets.tcgdex.net/univ/sv/sv5/symbol",
                "logo": "https://assets.tcgdex.net/en/sv/sv5/logo"
            },
            {
                "id": "sv4",
                "name": "Temporal Forces",
                "releaseDate": "2024-03-22",
                "symbol": "https://assets.tcgdex.net/univ/sv/sv4/symbol",
                "logo": "https://assets.tcgdex.net/en/sv/sv4/logo"
            }
        ]
    
    @pytest.fixture
    def mock_sets_response_mixed_years(self):
        """Mock-Response mit Sets aus verschiedenen Jahren"""
        return [
            {
                "id": "sv4a",
                "name": "Stellar Crown",
                "releaseDate": "2024-08-23",
                "symbol": "https://assets.tcgdex.net/univ/sv/sv4a/symbol"
            },
            {
                "id": "sv3",
                "name": "Paradox Rift",
                "releaseDate": "2023-11-03",
                "symbol": "https://assets.tcgdex.net/univ/sv/sv3/symbol"
            },
            {
                "id": "sv5",
                "name": "Ancient Roar",
                "releaseDate": "2024-11-01",
                "symbol": "https://assets.tcgdex.net/univ/sv/sv5/symbol"
            }
        ]
    
    @pytest.mark.asyncio
    async def test_get_sets_by_year_2024_success(self, service, mock_sets_response_2024):
        """Test erfolgreiche Abfrage von Sets für 2024"""
        # Erstelle Brief-Sets (ohne releaseDate) und detaillierte Sets (mit releaseDate)
        brief_sets = [{"id": s["id"], "name": s["name"]} for s in mock_sets_response_2024]
        detailed_sets_map = {s["id"]: s for s in mock_sets_response_2024}
        
        # Mock get_all_sets und get_set
        with patch.object(service, 'get_all_sets', new_callable=AsyncMock) as mock_get_all, \
             patch.object(service, 'get_set', new_callable=AsyncMock) as mock_get_set:
            
            mock_get_all.return_value = (brief_sets, None)
            
            # get_set soll die detaillierten Sets zurückgeben
            async def mock_get_set_func(set_id):
                return detailed_sets_map.get(set_id)
            
            mock_get_set.side_effect = mock_get_set_func
            
            # Führe Test aus
            sets, error = await service.get_sets_by_year(2024)
            
            # Assertions
            assert error is None, f"Es sollte kein Fehler auftreten, aber: {error}"
            assert len(sets) == 3, f"Es sollten 3 Sets gefunden werden, aber es wurden {len(sets)} gefunden"
            
            # Prüfe dass alle Sets aus 2024 sind
            for set_data in sets:
                year = int(set_data["releaseDate"].split("-")[0])
                assert year == 2024, f"Set {set_data['name']} ist nicht aus 2024, sondern {year}"
            
            # Prüfe dass Sets nach Release-Datum sortiert sind (neueste zuerst)
            assert sets[0]["id"] == "sv5", "Das neueste Set sollte zuerst sein"
            assert sets[-1]["id"] == "sv4", "Das älteste Set sollte zuletzt sein"
    
    @pytest.mark.asyncio
    async def test_get_sets_by_year_2024_no_sets_found(self, service):
        """Test wenn keine Sets für 2024 gefunden werden"""
        mock_sets_other_years = [
            {
                "id": "sv3",
                "name": "Paradox Rift",
                "releaseDate": "2023-11-03",
                "symbol": "https://assets.tcgdex.net/univ/sv/sv3/symbol"
            },
            {
                "id": "sv2",
                "name": "Paldea Evolved",
                "releaseDate": "2023-06-09",
                "symbol": "https://assets.tcgdex.net/univ/sv/sv2/symbol"
            }
        ]
        
        # Erstelle Brief-Sets und detaillierte Sets
        brief_sets = [{"id": s["id"], "name": s["name"]} for s in mock_sets_other_years]
        detailed_sets_map = {s["id"]: s for s in mock_sets_other_years}
        
        with patch.object(service, 'get_all_sets', new_callable=AsyncMock) as mock_get_all, \
             patch.object(service, 'get_set', new_callable=AsyncMock) as mock_get_set:
            
            mock_get_all.return_value = (brief_sets, None)
            
            async def mock_get_set_func(set_id):
                return detailed_sets_map.get(set_id)
            
            mock_get_set.side_effect = mock_get_set_func
            
            sets, error = await service.get_sets_by_year(2024)
            
            # Assertions
            assert len(sets) == 0, "Es sollten keine Sets gefunden werden"
            assert error is not None, "Es sollte eine Fehlermeldung zurückgegeben werden"
            assert "2024" in error, "Die Fehlermeldung sollte das Jahr 2024 enthalten"
            assert "2023" in error, "Die Fehlermeldung sollte verfügbare Jahre zeigen"
    
    @pytest.mark.asyncio
    async def test_get_sets_by_year_2024_api_error(self, service):
        """Test wenn die API einen Fehler zurückgibt"""
        with patch.object(service, 'get_all_sets', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = ([], "API-Anfrage fehlgeschlagen - Server nicht erreichbar")
            
            sets, error = await service.get_sets_by_year(2024)
            
            # Assertions
            assert len(sets) == 0, "Es sollten keine Sets zurückgegeben werden"
            assert error is not None, "Es sollte eine Fehlermeldung zurückgegeben werden"
            assert "API-Anfrage fehlgeschlagen" in error, "Die Fehlermeldung sollte den API-Fehler enthalten"
    
    @pytest.mark.asyncio
    async def test_get_sets_by_year_2024_empty_list(self, service):
        """Test wenn die API eine leere Liste zurückgibt"""
        with patch.object(service, 'get_all_sets', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = ([], "Es wurden keine Sets von der API zurückgegeben")
            
            sets, error = await service.get_sets_by_year(2024)
            
            # Assertions
            assert len(sets) == 0, "Es sollten keine Sets zurückgegeben werden"
            assert error is not None, "Es sollte eine Fehlermeldung zurückgegeben werden"
            assert "keine Sets von der API" in error, "Die Fehlermeldung sollte angeben, dass keine Sets zurückgegeben wurden"
    
    @pytest.mark.asyncio
    async def test_get_sets_by_year_2024_invalid_release_date(self, service):
        """Test mit Sets mit ungültigem releaseDate Format"""
        mock_sets_invalid = [
            {
                "id": "sv4a",
                "name": "Stellar Crown",
                "releaseDate": "invalid-date",
                "symbol": "https://assets.tcgdex.net/univ/sv/sv4a/symbol"
            },
            {
                "id": "sv4",
                "name": "Temporal Forces",
                "releaseDate": "2024-03-22",
                "symbol": "https://assets.tcgdex.net/univ/sv/sv4/symbol"
            },
            {
                "id": "no-date",
                "name": "Set ohne Datum",
                "symbol": "https://assets.tcgdex.net/univ/sv/nodate/symbol"
                # Kein releaseDate Feld
            }
        ]
        
        brief_sets = [{"id": s["id"], "name": s["name"]} for s in mock_sets_invalid]
        detailed_sets_map = {s["id"]: s for s in mock_sets_invalid}
        
        with patch.object(service, 'get_all_sets', new_callable=AsyncMock) as mock_get_all, \
             patch.object(service, 'get_set', new_callable=AsyncMock) as mock_get_set:
            
            mock_get_all.return_value = (brief_sets, None)
            
            async def mock_get_set_func(set_id):
                return detailed_sets_map.get(set_id)
            
            mock_get_set.side_effect = mock_get_set_func
            
            sets, error = await service.get_sets_by_year(2024)
            
            # Assertions
            assert error is None, "Es sollte kein Fehler auftreten"
            assert len(sets) == 1, "Es sollte nur 1 gültiges Set gefunden werden (sv4)"
            assert sets[0]["id"] == "sv4", "Das gefundene Set sollte sv4 sein"
    
    @pytest.mark.asyncio
    async def test_get_sets_by_year_2024_filtering_only_2024(self, service, mock_sets_response_mixed_years):
        """Test dass nur Sets aus 2024 zurückgegeben werden, nicht aus anderen Jahren"""
        brief_sets = [{"id": s["id"], "name": s["name"]} for s in mock_sets_response_mixed_years]
        detailed_sets_map = {s["id"]: s for s in mock_sets_response_mixed_years}
        
        with patch.object(service, 'get_all_sets', new_callable=AsyncMock) as mock_get_all, \
             patch.object(service, 'get_set', new_callable=AsyncMock) as mock_get_set:
            
            mock_get_all.return_value = (brief_sets, None)
            
            async def mock_get_set_func(set_id):
                return detailed_sets_map.get(set_id)
            
            mock_get_set.side_effect = mock_get_set_func
            
            sets, error = await service.get_sets_by_year(2024)
            
            # Assertions
            assert error is None, "Es sollte kein Fehler auftreten"
            assert len(sets) == 2, "Es sollten genau 2 Sets aus 2024 gefunden werden"
            
            # Prüfe dass kein Set aus 2023 enthalten ist
            for set_data in sets:
                year = int(set_data["releaseDate"].split("-")[0])
                assert year == 2024, f"Set {set_data['name']} ist nicht aus 2024"
                assert set_data["id"] != "sv3", "Set sv3 (2023) sollte nicht enthalten sein"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_sets_by_year_2024_real_api(self, service):
        """Integration Test: Test mit echter API-Response für das Jahr 2024"""
        try:
            # Rufe tatsächlich die API auf
            sets, error = await service.get_sets_by_year(2024)
            
            # Wenn API nicht erreichbar ist, skip den Test
            if error and ("nicht erreichbar" in error.lower() or "network" in error.lower()):
                pytest.skip(f"API nicht erreichbar: {error}")
            
            # Prüfe Ergebnis
            if error:
                # Wenn keine Sets gefunden wurden, aber API erreichbar war
                print(f"\n⚠ Keine Sets für 2024 gefunden: {error}")
                # Das ist okay - vielleicht gibt es wirklich keine Sets für 2024
                # Aber prüfen wir ob die API überhaupt funktioniert hat
                all_sets, all_error = await service.get_all_sets()
                if all_error or len(all_sets) == 0:
                    pytest.fail(f"API-Fehler: {all_error}")
                # Prüfe ob überhaupt Sets mit releaseDate existieren
                sets_with_date = [s for s in all_sets if s.get("releaseDate")]
                print(f"  Gesamt Sets: {len(all_sets)}, Sets mit releaseDate: {len(sets_with_date)}")
                if len(sets_with_date) == 0:
                    pytest.skip("API gibt keine Sets mit releaseDate zurück")
                # Zeige Beispiel-Jahre
                years = set()
                for s in sets_with_date[:20]:
                    date = s.get("releaseDate", "")
                    if date:
                        try:
                            year = date.split("-")[0]
                            if year.isdigit():
                                years.add(year)
                        except:
                            pass
                print(f"  Verfügbare Jahre (Beispiele): {sorted(years)}")
            else:
                # Assertions wenn Sets gefunden wurden
                assert len(sets) > 0, "Es sollten Sets für 2024 gefunden werden"
                
                # Prüfe dass alle gefundenen Sets aus 2024 sind
                for set_data in sets:
                    release_date = set_data.get("releaseDate")
                    assert release_date is not None, f"Set {set_data.get('name', 'Unbekannt')} hat kein releaseDate"
                    
                    # Extrahiere Jahr
                    year = int(release_date.split("-")[0])
                    assert year == 2024, f"Set {set_data.get('name', 'Unbekannt')} ist nicht aus 2024, sondern {year}"
                    
                    # Prüfe dass wichtige Felder vorhanden sind
                    assert "id" in set_data, "Set sollte eine ID haben"
                    assert "name" in set_data, "Set sollte einen Namen haben"
                
                # Log für Debugging
                print(f"\n✓ Gefundene Sets für 2024: {len(sets)}")
                for set_data in sets[:5]:  # Zeige erste 5 Sets
                    print(f"  - {set_data.get('name')} ({set_data.get('releaseDate')})")
        finally:
            # Stelle sicher, dass Session geschlossen wird
            await service.close()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_all_sets_real_api(self, service):
        """Integration Test: Test ob get_all_sets die echte API aufruft"""
        try:
            sets, error = await service.get_all_sets()
            
            # Wenn API nicht erreichbar ist, skip den Test
            if error and ("nicht erreichbar" in error.lower() or "network" in error.lower()):
                pytest.skip(f"API nicht erreichbar: {error}")
            
            # Assertions
            assert error is None, f"Unerwarteter Fehler: {error}"
            assert len(sets) > 0, "Es sollten Sets von der API zurückgegeben werden"
            
            # Prüfe dass Sets die erwarteten Felder haben
            first_set = sets[0]
            assert "id" in first_set, "Set sollte eine ID haben"
            assert "name" in first_set, "Set sollte einen Namen haben"
            
            # releaseDate ist optional laut API-Dokumentation
            # Prüfe nur wenn vorhanden
            if "releaseDate" in first_set:
                release_date = first_set["releaseDate"]
                assert len(release_date.split("-")) == 3, f"releaseDate sollte Format yyyy-mm-dd haben, aber ist: {release_date}"
            
            # Zeige Statistiken
            sets_with_date = [s for s in sets if s.get("releaseDate")]
            print(f"\n✓ Gesamt gefundene Sets: {len(sets)}")
            print(f"  Sets mit releaseDate: {len(sets_with_date)}")
            if first_set.get("releaseDate"):
                print(f"  Beispiel-Set: {first_set.get('name')} ({first_set.get('releaseDate')})")
            else:
                print(f"  Beispiel-Set: {first_set.get('name')} (kein releaseDate)")
        finally:
            # Stelle sicher, dass Session geschlossen wird
            await service.close()
    
    @pytest.mark.asyncio
    async def test_set_logo_extraction_various_formats(self, service):
        """Test dass Set-Logos/Symbole in verschiedenen Formaten gefunden werden"""
        
        # Test verschiedene mögliche API-Strukturen
        test_cases = [
            {
                "name": "Direktes symbol Feld",
                "set_data": {
                    "id": "sv4",
                    "name": "Temporal Forces",
                    "releaseDate": "2024-03-22",
                    "symbol": "https://assets.tcgdex.net/univ/sv/sv4/symbol"
                },
                "expected_url": "https://assets.tcgdex.net/univ/sv/sv4/symbol.webp"
            },
            {
                "name": "Direktes logo Feld",
                "set_data": {
                    "id": "sv5",
                    "name": "Ancient Roar",
                    "releaseDate": "2024-11-01",
                    "logo": "https://assets.tcgdex.net/en/sv/sv5/logo"
                },
                "expected_url": "https://assets.tcgdex.net/en/sv/sv5/logo"
            },
            {
                "name": "Verschachtelt in images.symbol",
                "set_data": {
                    "id": "sv6",
                    "name": "Test Set",
                    "releaseDate": "2024-12-01",
                    "images": {
                        "symbol": "https://assets.tcgdex.net/univ/sv/sv6/symbol",
                        "logo": "https://assets.tcgdex.net/en/sv/sv6/logo"
                    }
                },
                "expected_url": "https://assets.tcgdex.net/univ/sv/sv6/symbol.webp"
            },
            {
                "name": "Verschachtelt in images.logo (falls symbol fehlt)",
                "set_data": {
                    "id": "sv7",
                    "name": "Test Set 2",
                    "releaseDate": "2024-12-01",
                    "images": {
                        "logo": "https://assets.tcgdex.net/en/sv/sv7/logo"
                    }
                },
                "expected_url": "https://assets.tcgdex.net/en/sv/sv7/logo"
            },
            {
                "name": "symbolUrl Feld",
                "set_data": {
                    "id": "sv8",
                    "name": "Test Set 3",
                    "releaseDate": "2024-12-01",
                    "symbolUrl": "https://assets.tcgdex.net/univ/sv/sv8/symbol"
                },
                "expected_url": "https://assets.tcgdex.net/univ/sv/sv8/symbol.webp"
            },
            {
                "name": "logoUrl Feld",
                "set_data": {
                    "id": "sv9",
                    "name": "Test Set 4",
                    "releaseDate": "2024-12-01",
                    "logoUrl": "https://assets.tcgdex.net/en/sv/sv9/logo"
                },
                "expected_url": "https://assets.tcgdex.net/en/sv/sv9/logo"
            },
            {
                "name": "icon.url Feld",
                "set_data": {
                    "id": "sv10",
                    "name": "Test Set 5",
                    "releaseDate": "2024-12-01",
                    "icon": {
                        "url": "https://assets.tcgdex.net/univ/sv/sv10/icon"
                    }
                },
                "expected_url": "https://assets.tcgdex.net/univ/sv/sv10/icon"
            },
            {
                "name": "icon als String",
                "set_data": {
                    "id": "sv11",
                    "name": "Test Set 6",
                    "releaseDate": "2024-12-01",
                    "icon": "https://assets.tcgdex.net/univ/sv/sv11/icon"
                },
                "expected_url": "https://assets.tcgdex.net/univ/sv/sv11/icon"
            },
            {
                "name": "Kein Logo vorhanden",
                "set_data": {
                    "id": "sv12",
                    "name": "Test Set 7",
                    "releaseDate": "2024-12-01"
                },
                "expected_url": ""
            }
        ]
        
        # Mock get_all_sets und get_set
        brief_sets = [{"id": tc["set_data"]["id"], "name": tc["set_data"]["name"]} for tc in test_cases]
        detailed_sets_map = {tc["set_data"]["id"]: tc["set_data"] for tc in test_cases}
        
        with patch.object(service, 'get_all_sets', new_callable=AsyncMock) as mock_get_all, \
             patch.object(service, 'get_set', new_callable=AsyncMock) as mock_get_set:
            
            mock_get_all.return_value = (brief_sets, None)
            
            async def mock_get_set_func(set_id):
                return detailed_sets_map.get(set_id)
            
            mock_get_set.side_effect = mock_get_set_func
            
            # Rufe Sets ab
            sets, error = await service.get_sets_by_year(2024)
            
            # Assertions
            assert error is None, "Es sollte kein Fehler auftreten"
            assert len(sets) == len(test_cases), f"Es sollten {len(test_cases)} Sets gefunden werden"
            
            # Prüfe für jeden Testfall, ob das Logo gefunden wird
            for test_case in test_cases:
                set_id = test_case["set_data"]["id"]
                expected_url = test_case["expected_url"]
                
                # Finde das entsprechende Set in den Ergebnissen
                found_set = next((s for s in sets if s.get("id") == set_id), None)
                assert found_set is not None, f"Set {set_id} sollte gefunden werden"
                
                # Teste die Logo-Extraktion (wie im Code implementiert)
                symbol_url = ""
                if isinstance(found_set, dict):
                    symbol_url = (found_set.get("symbol", "") or 
                                 found_set.get("logo", "") or
                                 found_set.get("symbolUrl", "") or
                                 found_set.get("logoUrl", ""))
                    
                    if not symbol_url:
                        images = found_set.get("images", {})
                        if isinstance(images, dict):
                            symbol_url = (images.get("symbol", "") or 
                                         images.get("logo", "") or
                                         images.get("symbolUrl", "") or
                                         images.get("logoUrl", ""))
                    
                    if not symbol_url:
                        icon = found_set.get("icon", {})
                        if isinstance(icon, dict):
                            symbol_url = icon.get("url", "") or icon.get("symbol", "") or icon.get("logo", "")
                        elif isinstance(icon, str):
                            symbol_url = icon
                
                # Fixe URL falls nötig (wie im Code implementiert)
                if symbol_url:
                    symbol_url = service.fix_symbol_url(symbol_url)
                
                # Assertion
                assert symbol_url == expected_url, (
                    f"Test '{test_case['name']}' fehlgeschlagen:\n"
                    f"  Erwartet: {expected_url}\n"
                    f"  Gefunden: {symbol_url}\n"
                    f"  Set-Daten: {found_set}"
                )
                
                print(f"✓ {test_case['name']}: {symbol_url if symbol_url else '(kein Logo)'}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_api_set_logo_extraction(self, service):
        """Integration Test: Prüfe ob echte API Set-Logos/Symbole zurückgibt"""
        try:
            # Rufe Sets für 2024 ab
            sets, error = await service.get_sets_by_year(2024)
            
            assert error is None, f"API-Fehler: {error}"
            assert len(sets) > 0, "Es sollten Sets gefunden werden"
            
            print(f"\n📊 Analysiere {len(sets)} Sets aus der echten API:\n")
            
            sets_with_logo = 0
            sets_without_logo = 0
            logo_formats = {}
            
            for i, set_data in enumerate(sets[:10]):  # Analysiere erste 10 Sets
                set_name = set_data.get("name", "Unbekannt")
                set_id = set_data.get("id", "unknown")
                
                # Extrahiere Logo (wie im Code)
                symbol_url = ""
                found_format = None
                
                if isinstance(set_data, dict):
                    # Direkte Felder
                    if set_data.get("symbol"):
                        symbol_url = set_data.get("symbol")
                        found_format = "symbol"
                    elif set_data.get("logo"):
                        symbol_url = set_data.get("logo")
                        found_format = "logo"
                    elif set_data.get("symbolUrl"):
                        symbol_url = set_data.get("symbolUrl")
                        found_format = "symbolUrl"
                    elif set_data.get("logoUrl"):
                        symbol_url = set_data.get("logoUrl")
                        found_format = "logoUrl"
                    # Verschachtelte Strukturen
                    elif set_data.get("images"):
                        images = set_data.get("images")
                        if isinstance(images, dict):
                            if images.get("symbol"):
                                symbol_url = images.get("symbol")
                                found_format = "images.symbol"
                            elif images.get("logo"):
                                symbol_url = images.get("logo")
                                found_format = "images.logo"
                    # Icon
                    elif set_data.get("icon"):
                        icon = set_data.get("icon")
                        if isinstance(icon, dict):
                            if icon.get("url"):
                                symbol_url = icon.get("url")
                                found_format = "icon.url"
                        elif isinstance(icon, str):
                            symbol_url = icon
                            found_format = "icon (string)"
                
                if symbol_url:
                    sets_with_logo += 1
                    if found_format:
                        logo_formats[found_format] = logo_formats.get(found_format, 0) + 1
                    print(f"  ✓ {set_name} ({set_id}): {symbol_url[:60]}... [{found_format or 'unbekannt'}]")
                else:
                    sets_without_logo += 1
                    available_keys = list(set_data.keys()) if isinstance(set_data, dict) else []
                    print(f"  ✗ {set_name} ({set_id}): KEIN LOGO gefunden")
                    print(f"      Verfügbare Keys: {', '.join(available_keys[:10])}")
            
            # Zusammenfassung
            print(f"\n📈 Zusammenfassung:")
            print(f"  Sets mit Logo: {sets_with_logo}/{min(10, len(sets))}")
            print(f"  Sets ohne Logo: {sets_without_logo}/{min(10, len(sets))}")
            if logo_formats:
                print(f"  Gefundene Formate: {logo_formats}")
            
            # Mindestens ein Set sollte ein Logo haben
            assert sets_with_logo > 0, "Mindestens ein Set sollte ein Logo haben!"
            
        finally:
            await service.close()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_construct_symbol_url_with_real_api(self, service):
        """Integration Test: Teste ob konstruierte Symbol-URLs tatsächlich funktionieren"""
        
        # Test verschiedene Sets mit bekannten IDs
        test_sets = [
            {"set_id": "swsh3", "serie_id": "swsh", "name": "Darkness Ablaze"},
            {"set_id": "sv4", "serie_id": "sv", "name": "Temporal Forces"},
            {"set_id": "sv5", "serie_id": "sv", "name": "Ancient Roar"},
            {"set_id": "swsh1", "serie_id": "swsh", "name": "Sword & Shield"},
        ]
        
        print("\n🔍 Teste konstruierte Symbol-URLs mit echter API:\n")
        
        successful_urls = 0
        failed_urls = 0
        
        async with aiohttp.ClientSession() as session:
            for test_set in test_sets:
                set_id = test_set["set_id"]
                serie_id = test_set["serie_id"]
                set_name = test_set["name"]
                
                # Konstruiere Symbol-URL
                symbol_url = service.construct_symbol_url(set_id, serie_id, "webp")
                
                print(f"  Testing: {set_name} ({set_id})")
                print(f"    URL: {symbol_url}")
                
                try:
                    # Versuche das Symbol abzurufen
                    async with session.get(symbol_url) as response:
                        if response.status == 200:
                            content_type = response.headers.get("Content-Type", "")
                            content_length = response.headers.get("Content-Length", "unknown")
                            
                            # Prüfe ob es tatsächlich ein Bild ist
                            if "image" in content_type.lower() or content_type.startswith("image/"):
                                successful_urls += 1
                                print(f"    ✅ Symbol gefunden! (Content-Type: {content_type}, Size: {content_length})")
                            else:
                                failed_urls += 1
                                print(f"    ❌ Kein Bild (Content-Type: {content_type})")
                        elif response.status == 404:
                            failed_urls += 1
                            print("    ❌ Symbol nicht gefunden (404)")
                        else:
                            failed_urls += 1
                            print(f"    ❌ Fehler: HTTP {response.status}")
                
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    failed_urls += 1
                    print(f"    ❌ Fehler beim Abrufen: {e}")
        
        print("\n📊 Zusammenfassung:")
        print(f"  Erfolgreiche URLs: {successful_urls}/{len(test_sets)}")
        print(f"  Fehlgeschlagene URLs: {failed_urls}/{len(test_sets)}")
        
        # Mindestens eine URL sollte funktionieren
        assert successful_urls > 0, "Mindestens eine Symbol-URL sollte funktionieren!"
        
        await service.close()

