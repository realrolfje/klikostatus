# Kliko Afvalcontainer Status Home Assistant-integratie

[![CI](https://github.com/realrolfje/klikostatus/actions/workflows/ci.yml/badge.svg)](https://github.com/realrolfje/klikostatus/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/dynamic/json?label=version&query=%24.version&url=https%3A%2F%2Fraw.githubusercontent.com%2Frealrolfje%2Fklikostatus%2Fmain%2Fcustom_components%2Fkliko_status%2Fmanifest.json)](https://github.com/realrolfje/klikostatus/releases)

Home Assistant-integratie voor afvalcontainers uit Kliko Container Manager.

GitHub-repository:

```text
https://github.com/realrolfje/klikostatus
```

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=realrolfje&repository=klikostatus&category=integration)

Dit project is een Home Assistant custom integration. Het is geen Home Assistant Supervisor add-on voor de Add-on Store.

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
7. Zoek daarna in HACS naar `Kliko Afvalcontainer Status`.
8. Installeer de integratie.
9. Herstart Home Assistant.

Voeg de integratie daarna toe via:

```text
Instellingen > Apparaten & diensten > Integratie toevoegen > Kliko Afvalcontainer Status
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
Instellingen > Apparaten & diensten > Integratie toevoegen > Kliko Afvalcontainer Status
```

## Configuratie

Tijdens het toevoegen vraagt de integratie om:

- Gemeente
- Update-interval in minuten

Daarna vraagt de integratie om de gegevens die bij de gekozen gemeente horen:

- Bij `PASSWORD` login: kaartnummer en wachtwoord.
- Bij `ADDRESS` login: postcode, huisnummer en eventueel huisnummertoevoeging.

Na het inloggen haalt de integratie de beschikbare containers op. Zoek in de lijst en vink alleen de containers aan waarvoor Home Assistant devices en entities moet aanmaken.

Deze defaults zijn al ingevuld:

- Update-interval: `60` minuten, minimaal `30` minuten. Dit is later aanpasbaar via de opties van de integratie.

Je kiest zelf de gemeente en vult de gevraagde inloggegevens in. De integratie leidt op basis van de gekozen gemeente de juiste Kliko endpoints af, logt daarmee in, bewaart de ontvangen token alleen in geheugen, en gebruikt die token voor de containerdata.

Ondersteunde gemeenten in deze integratie:

- Land van Cuijk (`PASSWORD`)
- Maassluis (`ADDRESS`)
- Oude IJsselstreek (`ADDRESS`)
- Ouder Amstel (`PASSWORD`)
- Uithoorn (`PASSWORD`)

Het update-interval en de geselecteerde containers kun je later wijzigen via:

```text
Instellingen > Apparaten & diensten > Kliko Afvalcontainer Status > Configureren
```

## Entities

De integratie maakt per geselecteerde container een device aan. Per device worden deze entities aangemaakt:

- Sensor `Vulling`: waarde van `percentageFull`, als percentage.
- Binary sensor `Fout`: waarde van `error`.
- Binary sensor `Vol`: waarde van `isFull`.
- Binary sensor `Bijna vol`: waarde van `isNearlyFull`.
- Sensor `Straat`: waarde van `address.street`.
- Sensor `Afvaltype`: waarde van `fraction`.

De data wordt standaard elke 60 minuten opgehaald. Per update logt de coordinator in als dat nodig is en doet daarna een POST naar `getMyContainers` met de ontvangen token. Die containerlijst wordt een keer per update opgehaald en daarna verdeeld over de geselecteerde container-devices.

`address.latitude` en `address.longitude` worden als attributen `latitude` en `longitude` op de entities gezet.

## Beveiliging

Home Assistant custom integrations slaan config-entry data lokaal op in de Home Assistant-configuratie. Het wachtwoord wordt in de setup-flow als wachtwoordveld gevraagd, maar is geen aparte secret vault. Beperk toegang tot je Home Assistant-configuratiebestanden.

De integratie logt het wachtwoord niet, maakt er geen entities of attributen van, en neemt het niet op in de containerdata. Ook de ontvangen token wordt niet opgeslagen in de config entry; die blijft alleen in geheugen zolang Home Assistant draait.

## Updaten

### Updaten via HACS

Als de integratie via HACS is toegevoegd, verschijnt een update automatisch in HACS zodra er een nieuwe versie beschikbaar is op GitHub.

1. Open HACS.
2. Ga naar `Integrations`.
3. Open `Kliko Afvalcontainer Status`.
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
Instellingen > Apparaten & diensten > Kliko Afvalcontainer Status > Verwijderen
```

Stop Home Assistant daarna en verwijder de map:

```text
custom_components/kliko_status
```

## Meer informatie

- [Changelog](CHANGELOG.md)
- [Ontwikkel- en testinstructies](DEVELOPMENT.md)
