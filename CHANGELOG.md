# Changelog

## Unreleased

## 0.2.0

- Iconen toegevoegd voor de sensors `Vulling`, `Straat` en `Afvaltype`.
- Eerste ondersteuning voor de publieke Spaarnelanden-containerkaart, met vulling, afvaltype, wijk en lat/long.
- Spaarnelanden maakt geen `Vol` en `Bijna vol` entities aan, omdat die status niet expliciet door de bron wordt geleverd.
- Per geselecteerde container met coördinaten wordt een `geo_location` entity aangemaakt; latitude/longitude staan niet langer als attributen op de gewone sensors.

## 0.1.1

- Ondersteuning voor een of meer afvalcontainers onder dezelfde login.
- Verbeterde containerselectie: containers zijn niet meer standaard allemaal geselecteerd.
- De containerlijst wordt gesorteerd en kan in Home Assistant gericht worden doorzocht/gefilterd.
- Bestaande containerselecties blijven behouden bij het wijzigen van opties.

## 0.1.0

- Eerste versie van de integratie.
- Ondersteuning voor meerdere Kliko Container Manager-gemeenten.
- Ondersteuning voor login met kaartnummer/wachtwoord en adres, afhankelijk van gemeente.
- Per container een Home Assistant device met sensors voor vulling, straat en afvaltype.
- Binary sensors voor foutstatus, vol en bijna vol.
- HACS-installatieknop, integratie-icoon en social preview.
