# Development

Voor GitHub social preview kan `assets/social-preview.png` worden gebruikt.

## Testen buiten Home Assistant

Er staat een standalone testscript in `scripts/test_kliko.py`. Dit gebruikt alleen de Python standard library en schrijft geen credentials weg.

Interactief testen, zonder wachtwoord in je shell history:

```bash
python3 scripts/test_kliko.py --client '<client>' --container-number '<containernummer>'
```

Of met environment variables:

```bash
KLIKO_CLIENT='<client>' KLIKO_CONTAINER_NUMBER='<containernummer>' KLIKO_CARD_NUMBER='<kaartnummer>' KLIKO_PASSWORD='<wachtwoord>' python3 scripts/test_kliko.py
```

Volledige JSON van de gevonden container printen:

```bash
python3 scripts/test_kliko.py --client '<client>' --container-number '<containernummer>' --dump-container
```

Het script doet dezelfde twee requests als de integratie: eerst `loginWithPassword`, daarna `getMyContainers` met de ontvangen token.

Het standalone script kan ook in een tijdelijke Python-container draaien:

```bash
docker run --rm -it -v "$PWD:/work:ro" -w /work python:3.12-slim python scripts/test_kliko.py --client '<client>' --container-number '<containernummer>'
```

## Testen in een tijdelijke Home Assistant Docker-container

Met deze route test je de echte Home Assistant config-flow, entities en device-koppeling zonder je bestaande Home Assistant-installatie aan te passen.

Maak een tijdelijke configmap:

```bash
mkdir -p /tmp/ha-kliko-status/config/custom_components
cp -R custom_components/kliko_status /tmp/ha-kliko-status/config/custom_components/
```

Start Home Assistant:

```bash
docker run -d \
  --name ha-kliko-status-test \
  -p 8123:8123 \
  -v /tmp/ha-kliko-status/config:/config \
  ghcr.io/home-assistant/home-assistant:stable
```

Als poort `8123` al in gebruik is, gebruik dan bijvoorbeeld `-p 8124:8123` en open daarna `http://localhost:8124`.

Bekijk de logs tot Home Assistant klaar is met starten:

```bash
docker logs -f ha-kliko-status-test
```

Druk op `Ctrl+C` om het volgen van de logs te stoppen. De container blijft dan draaien.

Open daarna:

```text
http://localhost:8123
```

Doorloop de eerste Home Assistant-wizard:

1. Maak een tijdelijk lokaal gebruikeraccount aan.
2. Kies een naam voor de test-installatie.
3. Stel locatie/tijdzone in of sla onderdelen over waar mogelijk.
4. Wacht tot Home Assistant klaar is met starten.

Voeg daarna de integratie toe:

```text
Instellingen > Apparaten & diensten > Integratie toevoegen > Kliko Afvalcontainer Status
```

Vul in:

1. De gemeente.
2. Het update-interval, standaard `60` minuten.
3. De gevraagde login-gegevens voor de gekozen gemeente.
4. Zoek in de opgehaalde lijst en selecteer een of meer containers.

Na succesvol toevoegen verwacht je:

- Een device per geselecteerde container.
- Sensor `Vulling` met `%` als eenheid.
- Sensor `Straat`.
- Sensor `Afvaltype`.
- Binary sensors `Fout`, `Vol` en `Bijna vol`.

Stoppen en opruimen:

```bash
docker stop ha-kliko-status-test
docker rm ha-kliko-status-test
rm -rf /tmp/ha-kliko-status
```

## Lokale validatie

Deze checks komen overeen met de GitHub Actions workflow:

```bash
python3 -m compileall custom_components/kliko_status scripts/test_kliko.py
python3 -m json.tool hacs.json > /dev/null
python3 -m json.tool custom_components/kliko_status/manifest.json > /dev/null
python3 -m json.tool custom_components/kliko_status/translations/en.json > /dev/null
python3 -m json.tool custom_components/kliko_status/translations/nl.json > /dev/null
```

## Releaseproces

1. Werk `CHANGELOG.md` bij met de nieuwe versie en de belangrijkste wijzigingen.
2. Verhoog de versie in `custom_components/kliko_status/manifest.json`.
3. Draai de lokale validatiechecks uit dit document.
4. Commit de wijzigingen:

```bash
git add CHANGELOG.md custom_components/kliko_status/manifest.json
git commit -m "Release <versie>"
```

5. Push `main` naar GitHub:

```bash
git push
```

6. Maak een tag voor dezelfde versie:

```bash
git tag "v<versie>"
git push origin "v<versie>"
```

7. Maak op GitHub een Release met dezelfde tag, bijvoorbeeld `v0.1.1`.
8. Gebruik de inhoud uit `CHANGELOG.md` als release notes.

Voor HACS-gebruikers is vooral de GitHub Release belangrijk: daar zien gebruikers wat er gewijzigd is wanneer HACS een update aanbiedt.
