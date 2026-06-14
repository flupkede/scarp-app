# Handmatig ijsfront intekenen — werkgids voor Filip

> Praktische gids voor het met de hand intekenen van gletsjer-ijsfronten op
> satellietbeelden. Dit is de **ground truth** waartegen we later de automatische
> retreat-detectie toetsen (Fase 2, "hand → automate → verify"). Je hoeft geen
> geoloog te zijn — dit is kijken + een lijntje trekken, en je leert er
> gletsjerdynamiek mee.
>
> Status: tekst-gids (Fase 1 levert hierbij geannoteerde voorbeelden + een
> validator/visualisatie-script + evt. een ruwe eerste schatting om te corrigeren).

---

## 1. Wat je gaat doen (in één zin)

Voor een paar gletsjers trek je op satellietbeelden van **verschillende jaren**
telkens één lijn langs het **ijsfront** (waar het ijs eindigt en het water/de
fjord begint). Door die lijnen te vergelijken zie je **hoeveel en wanneer** de
gletsjer is teruggetrokken.

---

## 2. Het ijsfront herkennen (de enige echte vaardigheid)

Op een satellietbeeld:

- **Gletsjerijs** = helder tot wit, met **textuur**: scheuren (crevasses),
  vuil-/puinstrepen die meebuigen met de stroming.
- **Water (fjord)** = egaal donker.
- **Ervoor drijven vaak ijsbergen / brokijs** (een rommelige "mélange" van witte
  stippen op donker water) — dat hoort bij het wáter, niet bij de gletsjer. Het
  **front** is de scherpe rand waar het *aaneengesloten* ijs ophoudt.

Je trekt je lijn op die scherpe rand tussen aaneengesloten ijs en water.

### Valkuilen
- **Seizoenssneeuw / winterbeeld**: sneeuw op het water of bevroren fjord maakt de
  rand onduidelijk → kies **zomerbeelden** (juli–september), wolkenvrij.
- **Schaduw** van bergwanden kan op water lijken → check met een ander beeld.
- **Mélange**: dichte ijsberg-brij kan lijken alsof de gletsjer verder reikt →
  zoek de scherpe textuur-grens, niet de losse brokken.
- **Wolken**: sla dat beeld over, neem een andere datum dichtbij.

---

## 3. Wat je nodig hebt

- **QGIS** (gratis, open source) — https://qgis.org. Eenmalig installeren.
- Internet (de satellietbeelden komen als online tile-lagen binnen, niets downloaden).
- Deze gids + (zodra Fase 1 draait) het validator-script in de repo.

---

## 4. Welke gletsjers en welke jaren

**Start (Fase 1):** Tracy Arm en Barry Arm — de twee waar Hig de "double retreat"
ziet.

**Datums:** kies per gletsjer ~5–8 momenten, gespreid over de tijd, telkens een
**wolkenvrij zomerbeeld**. Bruikbare bronnen per tijdvak:
- **2015 → nu:** Sentinel-2 (10 m, scherp) — beste keuze voor recent.
- **1984 → 2015:** Landsat (grover, 30 m, maar genoeg voor frontpositie).
- **1978–1986 (Alaska):** historische luchtfoto's (AHAP) — voor de oudste rand.

Mik op datums rond bekende retreat-episodes (bv. Barry Arm grote terugtrekking,
Tracy Arm rond de jaren waarin de velocity-sawtooth piekt — die lever ik aan uit
de ITS_LIVE-analyse in Fase 1).

---

## 5. Stap-voor-stap in QGIS

### Stap A — Satellietbeeld laden
1. In QGIS: **Browser** → rechtsklik **XYZ Tiles** → **New Connection**.
2. Voeg de bronnen toe die ik in Fase 1 als kant-en-klare lijst lever
   (Sentinel-2, USGS Imagery, historisch). Voorlopig kan je starten met de
   standaard satelliet-laag.
3. Zoom naar de gletsjer (ik geef je de coördinaten van Tracy Arm + Barry Arm).

### Stap B — Een lijn-laag maken
1. **Layer → Create Layer → New GeoJSON Layer** (of Shapefile).
2. Geometrie: **LineString**. CRS: **EPSG:4326** (WGS84, lon/lat) — het script
   herprojecteert zelf naar EPSG:3338 om de afstand correct te meten.
3. Voeg deze velden toe (exact deze namen, zie schema §6):
   `glacier`, `date`, `source_imagery`, `confidence`, `notes`.

### Stap C — Het front intekenen
1. Zet de laag op **Edit** (potlood-icoon) → **Add Line Feature**.
2. Klik punten langs het ijsfront, van de ene oever naar de andere. Niet te grof:
   volg de bochten van de rand. Dubbelklik / rechtsklik om af te sluiten.
3. Vul de velden in (welke gletsjer, datum van het beeld, welke bron, hoe zeker).

### Stap D — Opslaan
- Eén bestand per gletsjer is prima (meerdere lijnen, elk met hun eigen `date`),
  of één bestand per datum — als de velden maar kloppen.
- Opslaan in de repo onder **`data/manual/ice_fronts/`**
  (bv. `tracy_arm.geojson`, `barry_arm.geojson`).

### Stap E — Herhalen
- Volgende datum → nieuw beeld laden → nieuwe lijn → velden invullen.
- Daarna de andere gletsjer.

---

## 6. Schema (exact deze veldnamen)

Elke lijn (LineString-feature) heeft:

| Veld | Type | Voorbeeld | Uitleg |
|---|---|---|---|
| `glacier` | tekst | `"tracy_arm"` | vaste id van de gletsjer (ik geef de lijst) |
| `date` | tekst (ISO) | `"2020-08-15"` | datum van het **beeld**, niet van vandaag |
| `source_imagery` | tekst | `"Sentinel-2"` | welke bron/satelliet |
| `confidence` | tekst | `"high"` / `"med"` / `"low"` | hoe zeker je van de rand bent |
| `notes` | tekst | `"mélange, rand wat onzeker links"` | vrije opmerking |

Geometrie: **LineString** in **EPSG:4326**.

---

## 7. Wat ik (Claude) erbij lever in Fase 1

- **Geannoteerde voorbeelden** ("zó ziet het front van Tracy Arm eruit, dít is de
  rand") met de exacte coördinaten en aanbevolen datums.
- De **XYZ-bronlijst** om in QGIS te plakken (Sentinel-2 / USGS / historisch).
- Een **validator/visualisatie-script** (`glacier/17_icefront_check.py`) dat:
  - checkt of je velden + geometrie kloppen,
  - alle fronten van een gletsjer over elkaar tekent (zo zie je de retreat),
  - de **afstand tussen opeenvolgende fronten** berekent (= hoeveel teruggetrokken).
- Eventueel een **ruwe eerste schatting** van de fronten (uit imagery + ITS_LIVE-
  dekking), zodat jij alleen hoeft te **corrigeren** in plaats van van nul te starten.

---

## 8. Bij twijfel

- Liever een front overslaan dan gokken: zet `confidence: "low"` en een `notes`.
- Onduidelijk beeld? Markeer het en stuur door — wij (of Hig) kijken mee.
- Dit is leerwerk: de eerste paar zijn traag, daarna gaat het snel. 🙂
