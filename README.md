# Kliko Container Manager Home Assistant-integratie

Custom integration voor afvalcontainers uit Kliko Container Manager.

GitHub-repository:

```text
https://github.com/realrolfje/klikostatus
```

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=realrolfje&repository=klikostatus&category=integration)

Dit project is een Home Assistant custom integration. Het is geen Home Assistant Supervisor add-on voor de Add-on Store.

Voor GitHub social preview kan `assets/social-preview.png` worden gebruikt.

## Installatie in Home Assistant

### Installatie via HACS

Als je HACS gebruikt:

1. Klik op de HACS-knop bovenaan deze README.
2. Bevestig in Home Assistant dat je deze repository als HACS-repository wilt openen.
3. Installeer de integratie.
4. Herstart Home Assistant.

Als de knop niet werkt, voeg de repository dan handmatig toe:

1. Open HACS in Home Assistant.
2. Ga naar `Integrations`.
3. Open het menu rechtsboven en kies `Custom repositories`.
4. Vul deze repository in:

```text
https://github.com/realrolfje/klikostatus
```

5. Kies als categorie `Integration`.
6. Klik `Add`.
7. Zoek daarna in HACS naar `Kliko Container Manager`.
8. Installeer de integratie.
9. Herstart Home Assistant.

Voeg de integratie daarna toe via:

```text
Instellingen > Apparaten & diensten > Integratie toevoegen > Kliko Container Manager
```

### Handmatige installatie

Kopieer de integratiemap naar de `custom_components` map van je Home Assistant-configuratie.

```text
<home-assistant-config>/custom_components/kliko_status
```

De map moet er daarna ongeveer zo uitzien:

```text
configuration.yaml
custom_components/
  kliko_status/
    __init__.py
    manifest.json
    config_flow.py
    sensor.py
    binary_sensor.py
    ...
```

Voorbeelden:

```bash
# Home Assistant OS / supervised, via de config share
cp -R custom_components/kliko_status /config/custom_components/

# Docker-installatie met lokale configmap
cp -R custom_components/kliko_status /pad/naar/homeassistant/config/custom_components/
```

Herstart daarna Home Assistant.

Voeg de integratie toe via:

```text
Instellingen > Apparaten & diensten > Integratie toevoegen > Kliko Container Manager
```

## Configuratie

Tijdens het toevoegen vraagt de integratie om:

- Gemeente
- Containernummer
- Update-interval in minuten

Daarna vraagt de integratie om de gegevens die bij de gekozen gemeente horen:

- Bij `PASSWORD` login: kaartnummer en wachtwoord.
- Bij `ADDRESS` login: postcode, huisnummer en eventueel huisnummertoevoeging.

Deze defaults zijn al ingevuld:

- Update-interval: `60` minuten, minimaal `30` minuten. Dit is later aanpasbaar via de opties van de integratie.

Je kiest zelf de gemeente en vult het containernummer en de gevraagde inloggegevens in. De integratie leidt op basis van de gekozen gemeente de juiste Kliko endpoints af, logt daarmee in, bewaart de ontvangen token alleen in geheugen, en gebruikt die token voor de containerdata.

Ondersteunde gemeenten in deze integratie:

- Land van Cuijk (`PASSWORD`)
- Maassluis (`ADDRESS`)
- Oude IJsselstreek (`ADDRESS`)
- Ouder Amstel (`PASSWORD`)
- Uithoorn (`PASSWORD`)

Het update-interval kun je later wijzigen via:

```text
Instellingen > Apparaten & diensten > Kliko Container Manager > Configureren
```

## Entities

De integratie maakt deze entities aan:

- Sensor `Vulling`: waarde van `percentageFull`, als percentage.
- Binary sensor `Fout`: waarde van `error`.
- Binary sensor `Vol`: waarde van `isFull`.
- Binary sensor `Bijna vol`: waarde van `isNearlyFull`.
- Sensor `Straat`: waarde van `address.street`.
- Sensor `Afvaltype`: waarde van `fraction`.

De data wordt standaard elke 60 minuten opgehaald. Bij het opstarten logt de integratie in via `loginWithPassword`; daarna doet de coordinator een POST naar `getMyContainers` met de ontvangen token.

`address.latitude` en `address.longitude` worden als attributen `latitude` en `longitude` op de entities gezet.

## Beveiliging

Home Assistant custom integrations slaan config-entry data lokaal op in de Home Assistant-configuratie. Het wachtwoord wordt in de setup-flow als wachtwoordveld gevraagd, maar is geen aparte secret vault. Beperk toegang tot je Home Assistant-configuratiebestanden.

De integratie logt het wachtwoord niet, maakt er geen entities of attributen van, en neemt het niet op in de containerdata. Ook de ontvangen token wordt niet opgeslagen in de config entry; die blijft alleen in geheugen zolang Home Assistant draait.

## Updaten

### Updaten via HACS

Als de integratie via HACS is toegevoegd, verschijnt een update automatisch in HACS zodra er een nieuwe versie beschikbaar is op GitHub.

1. Open HACS.
2. Ga naar `Integrations`.
3. Open `Kliko Container Manager`.
4. Klik `Update` als er een update beschikbaar is.
5. Herstart Home Assistant.

### Handmatig updaten met Git

Als je de repository direct in je Home Assistant-configuratie wilt beheren, clone dan de repository in `custom_components`:

```bash
cd /config/custom_components
git clone https://github.com/realrolfje/klikostatus.git kliko_status
```

Updaten kan daarna met:

```bash
cd /config/custom_components/kliko_status
git pull
```

Herstart daarna Home Assistant.

### Handmatig updaten zonder Git

Vervang bij een nieuwe versie de map:

```text
custom_components/kliko_status
```

Herstart daarna Home Assistant.

## Verwijderen

Verwijder eerst de integratie uit Home Assistant:

```text
Instellingen > Apparaten & diensten > Kliko Container Manager > Verwijderen
```

Stop Home Assistant daarna en verwijder de map:

```text
custom_components/kliko_status
```

## Veilig testen buiten Home Assistant

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

Testen in een tijdelijke Docker-container vanuit deze projectmap:

```bash
docker run --rm -it -v "$PWD:/work:ro" -w /work python:3.12-slim python scripts/test_kliko.py --client '<client>' --container-number '<containernummer>'
```

Het script doet dezelfde twee requests als de integratie: eerst `loginWithPassword`, daarna `getMyContainers` met de ontvangen token.
