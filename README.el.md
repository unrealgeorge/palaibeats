<div align="center">

<img src="assets/logo.png" width="200" alt="PalaiBeats logo">

# PalaiBeats

Ένα Discord music bot για έναν server, self-hosted. Τρέχει 24/7 σε Raspberry Pi με Docker.

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.7%2B-5865F2)](https://github.com/Rapptz/discord.py)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED)](docker-compose.yml)

[![English](https://img.shields.io/badge/lang-English-black)](README.md)
[![Ελληνικά](https://img.shields.io/badge/lang-Ελληνικά-0D1B2A)](README.el.md)

</div>

---

Παίζει μουσική από τοπικό φάκελο, από link (YouTube, SoundCloud και
σχεδόν οτιδήποτε άλλο υποστηρίζει το yt-dlp), ή από ραδιοφωνικό stream —
όλα μέσα από slash commands στο Discord. Χωρίς πληρωμένο hosting, χωρίς
Lavalink: μόνο ένα Docker container και τα δικά σου αρχεία.

## Περιεχόμενα

- [Δυνατότητες](#δυνατότητες)
- [Τι χρειάζεσαι](#τι-χρειάζεσαι)
- [Εγκατάσταση](#εγκατάσταση)
  - [1. Κατέβασε τον κώδικα](#1-κατέβασε-τον-κώδικα)
  - [2. Φτιάξε το bot στο Discord](#2-φτιάξε-το-bot-στο-discord)
  - [3. Φτιάξε τον ρόλο DJ](#3-φτιάξε-τον-ρόλο-dj)
  - [4. Ρύθμιση](#4-ρύθμιση)
  - [5. Βάλε τη μουσική σου](#5-βάλε-τη-μουσική-σου)
  - [6. Τρέξε το](#6-τρέξε-το)
- [Εντολές](#εντολές)
- [Ραδιοφωνικοί σταθμοί](#ραδιοφωνικοί-σταθμοί)
- [Ενημέρωση](#ενημέρωση)
- [Προβλήματα &amp; λύσεις](#προβλήματα--λύσεις)
- [Δομή project](#δομή-project)
- [Άδεια χρήσης](#άδεια-χρήσης)

## Δυνατότητες

- **Τοπική μουσική** — περιήγηση ανά φάκελο μέσα από το Discord
  (`/browse`: διαλέγεις φάκελο, διαλέγεις τραγούδι, παίζει). Δεν
  χρειάζεται να γράψεις όνομα τραγουδιού.
- **Links** — `/play <link>` παίζει YouTube, SoundCloud και σχεδόν
  οτιδήποτε άλλο υποστηρίζει το yt-dlp. Δουλεύει και με απλό κείμενο
  (κάνει αναζήτηση στο YouTube).
- **Ραδιόφωνο** — αποθήκευσε stream URLs με `/radio add` και παίξε τα
  με `/radio play`. Ξανασυνδέεται μόνο του αν κοπεί το stream.
- **Έλεγχος αναπαραγωγής** — pause, resume, skip, stop, ένταση, loop,
  ουρά, και ένα πάνελ now-playing με κουμπιά.
- **Ρόλος DJ** — όλοι μπορούν να κάνουν browse και να δουν τι παίζει·
  μόνο όσοι έχουν τον ρόλο που θα διαλέξεις μπορούν να ελέγξουν την
  αναπαραγωγή.
- **Φεύγει μόνο του** — αποσυνδέεται όταν αδειάσει το κανάλι φωνής, ή
  όταν μείνει αδρανές για κάποια ώρα.

## Τι χρειάζεσαι

- Linux με Docker και Docker Compose (ένα Raspberry Pi 4 είναι αρκετό).
- Λογαριασμό Discord και server που διαχειρίζεσαι εσύ.
- Τα αρχεία μουσικής σου.

## Εγκατάσταση

### 1. Κατέβασε τον κώδικα

```bash
git clone https://github.com/unrealgeorge/palaibeats.git
cd palaibeats
```

(Ή κατέβασε το ZIP από το GitHub και κάνε extract.)

### 2. Φτιάξε το bot στο Discord

1. Άνοιξε το [Discord Developer Portal](https://discord.com/developers/applications) και πάτα **New Application**. Δώσε όποιο όνομα θες.
2. Πήγαινε στο **Bot** (αριστερά). Πάτα **Reset Token** και αντίγραψέ το κάπου ασφαλές — θα το βάλεις στο `.env` σε λίγο. Όποιος έχει αυτό το token μπορεί να ελέγξει το bot σου, οπότε μην το μοιραστείς και μην το ανεβάσεις στο Git.
3. Στην ίδια σελίδα **Bot**, άσε τα **Presence Intent**, **Server Members Intent** και **Message Content Intent** όλα **κλειστά**. Το PalaiBeats δεν τα χρειάζεται.
4. Πήγαινε στο **OAuth2 → URL Generator**.
   - Στα **Scopes**, τσέκαρε `bot` και `applications.commands`.
   - Θα εμφανιστεί ένα κουτί **Bot Permissions** από κάτω. Τσέκαρε: `View Channels`, `Send Messages`, `Embed Links`, `Connect`, `Speak`.
   - Κατέβα στο **Generated URL** και αντίγραψέ το.
5. Άνοιξε αυτό το URL στον browser, διάλεξε το server σου, πάτα **Authorize**.
6. Ενεργοποίησε το Developer Mode στο Discord (User Settings → Advanced), μετά κάνε δεξί κλικ στο εικονίδιο του server σου και **Copy Server ID**. Αυτό είναι το `GUILD_ID`.

### 3. Φτιάξε τον ρόλο DJ

Στο server σου: **Server Settings → Roles → Create Role**. Ονόμασέ τον
`DJ` (ή όπως θες — το όνομα το βάζεις στο `.env`). Δώσε τον σε όποιον
θέλεις να μπορεί να ελέγχει την αναπαραγωγή. Οι admins και ο owner του
server μπορούν πάντα να ελέγχουν το bot, με ή χωρίς τον ρόλο.

### 4. Ρύθμιση

```bash
cp .env.example .env
```

Άνοιξε το `.env` και συμπλήρωσε τουλάχιστον το `DISCORD_TOKEN` και το
`GUILD_ID`. Όλες οι υπόλοιπες ρυθμίσεις έχουν λογικές προεπιλογές — δες
τα σχόλια μέσα στο `.env.example` για το τι κάνει η καθεμία (όνομα
ρόλου DJ, προεπιλεγμένη ένταση, χρόνος αδράνειας κτλ).

### 5. Βάλε τη μουσική σου

Φτιάξε έναν φάκελο `music` δίπλα στο `docker-compose.yml` και οργάνωσέ
τον έτσι:

```
music/
  Κάποιος Καλλιτέχνης/
    tragoudi1.mp3
    tragoudi2.flac
  Playlist για χαλάρωση/
    tragoudi3.m4a
```

Κάθε φάκελος στο πρώτο επίπεδο γίνεται μία κατηγορία στο `/browse`. Τα
αρχεία μπορούν να είναι και πιο βαθιά μέσα σε υποφακέλους — παραμένουν
στην ίδια κατηγορία. Υποστηριζόμενες μορφές: mp3, flac, wav, m4a, ogg,
opus, aac, wma.

Αν η μουσική σου βρίσκεται ήδη κάπου αλλού στο μηχάνημα, βάλε στο
`.env` το `MUSIC_PATH` να δείχνει εκεί, αντί να φτιάξεις καινούριο
φάκελο.

### 6. Τρέξε το

```bash
docker compose up -d --build
docker compose logs -f palaibeats
```

Μόλις δεις στα logs ότι συνδέθηκε και συγχρόνισε τις εντολές, τα slash
commands θα εμφανιστούν στο Discord μέσα σε ένα-δύο λεπτά.

## Εντολές

| Εντολή | Ποιος τη χρησιμοποιεί | Τι κάνει |
|---|---|---|
| `/browse` | όλοι | Περιήγηση στην τοπική μουσική ανά φάκελο |
| `/play <link ή κείμενο>` | DJ | Παίζει link ή κάνει αναζήτηση |
| `/queue` | όλοι | Δείχνει την ουρά αναπαραγωγής |
| `/nowplaying` | όλοι | Τι παίζει τώρα, με κουμπιά ελέγχου |
| `/skip` | DJ | Παραλείπει το τρέχον τραγούδι |
| `/pause` / `/resume` | DJ | Παύση / συνέχεια |
| `/stop` | DJ | Σταματάει και αδειάζει την ουρά |
| `/leave` | DJ | Αποσύνδεση από το voice |
| `/volume <0-200>` | DJ | Ρυθμίζει την ένταση (%) |
| `/loop` | DJ | Επανάληψη τρέχοντος τραγουδιού on/off |
| `/refresh-library` | DJ | Ξανασκανάρει τον φάκελο μουσικής |
| `/radio add <όνομα> <url>` | DJ | Αποθηκεύει έναν σταθμό |
| `/radio remove <όνομα>` | DJ | Διαγράφει έναν σταθμό |
| `/radio list` | όλοι | Λίστα αποθηκευμένων σταθμών |
| `/radio play <όνομα>` | DJ | Παίζει έναν αποθηκευμένο σταθμό |
| `/radio stop` | DJ | Σταματάει το ραδιόφωνο |

## Ραδιοφωνικοί σταθμοί

Το `/radio add` θέλει το **απευθείας URL του stream** — link που πάει
κατευθείαν στον ήχο, όχι το site του σταθμού και όχι link σε playlist
αρχείο (`.pls`/`.m3u`). Δες πώς το βρίσκεις.

**Πιο εύκολο: [radio-browser.info](https://www.radio-browser.info)**
— δωρεάν, searchable λίστα με stream URLs ραδιοφώνων. Ψάξε τον σταθμό
με το όνομά του και αντίγραψε το link που δείχνει.

**Από το site του ίδιου του σταθμού:** δεξί κλικ στο κουμπί "Listen
live" / play και *Copy link address*. Αν αυτό δουλέψει κατευθείαν,
χρησιμοποίησέ το.

**Αν δεν δουλέψει, μέσω DevTools του browser:**
1. Άνοιξε το site του σταθμού, πάτα `F12` (DevTools), πήγαινε στο tab
   **Network**.
2. Γράψε `audio` (ή `mp3`, `aac`) στο filter.
3. Πάτα play στο player του σταθμού.
4. Ένα request που συνεχίζει να "τρέχει" (δεν τελειώνει το download)
   είναι το stream — δεξί κλικ πάνω του → *Copy* → *Copy URL*. Αυτό
   είναι το link που θες.

**Αν το μόνο link που έχεις τελειώνει σε `.pls` ή `.m3u`:** αυτό το
αρχείο δεν είναι το ίδιο το stream, είναι ένα κείμενο που δείχνει σε
αυτό. Άνοιξέ το σε browser ή με `curl -sL <url>` — μέσα θα δεις κάτι
σαν:
```
[playlist]
File1=http://real-stream-url:8000/stream
```
Χρησιμοποίησε αυτό το `File1=` URL, όχι το ίδιο το `.pls` link.

**Δοκίμασε το link πριν το προσθέσεις:**
```bash
ffplay "https://το-url-που-βρήκες"
```
Αν ακούσεις ήχο, είναι καλό. (Τα `.m3u8` HLS links συνήθως δουλεύουν
κανονικά κιόλας — μόνο τα `.pls`/`.m3u` playlist αρχεία δεν παίζουν
απευθείας.)

## Ενημέρωση

```bash
git pull
docker compose up -d --build
```

## Προβλήματα & λύσεις

**`RuntimeError: davey library needed in order to use voice`**
Το Discord απαιτεί πλέον το πρωτόκολλο κρυπτογράφησης DAVE για τις
συνδέσεις φωνής, και το discord.py χρειάζεται ένα ξεχωριστό πακέτο για
αυτό. Βεβαιώσου ότι το `requirements.txt` έχει τη γραμμή
`davey>=0.1.6`, μετά:
```bash
docker compose build --no-cache palaibeats && docker compose up -d
```

**Το port είναι ήδη σε χρήση (health check)**
Το `HEALTH_CHECK_PORT` δένει απευθείας στο host (το container τρέχει
με `network_mode: host`), άρα πρέπει να είναι ελεύθερο ανάμεσα σε *όλα*
τα containers σου, όχι μόνο σε αυτό. Διάλεξε άλλο port στο `.env`, ή
άσ' το κενό για να απενεργοποιηθεί εντελώς το health endpoint.

**Δεν εμφανίζονται τα slash commands**
Συγχρονίζονται μόνο στο server με το συγκεκριμένο `GUILD_ID` κατά την
εκκίνηση, και μπορεί να αργήσουν ένα-δύο λεπτά να φανούν. Κοίτα στα
logs για γραμμή τύπου "Synced N application command(s)" — αν λείπει,
έλεγξε το `GUILD_ID` και ότι το bot έχει γίνει πραγματικά invite σε
αυτό το server.

**"Only members with the DJ role can do that"**
Αναμενόμενο — δώσε στον εαυτό σου (ή σε όποιον θες να ελέγχει την
αναπαραγωγή) τον ρόλο με το όνομα που έχεις στο `DJ_ROLE_NAME`
(προεπιλογή `DJ`). Οι admins και ο owner το παρακάμπτουν αυτόματα.

**Δεν βγάζει ήχο / το bot μπαίνει αλλά μένει σιωπηλό**
Συνήθως θέμα ffmpeg ή libopus. Κοίτα στα logs αμέσως μετά το `/play`
για κάποιο σφάλμα ffmpeg, και επιβεβαίωσε ότι στην εκκίνηση βλέπεις
κάτι σαν `Loaded libopus via ...`.

## Δομή project

```
src/palaibeats/
  config.py        ρυθμίσεις, από το .env
  bot.py            σύνδεση: cogs, intents, sync εντολών
  core/
    audio.py          φόρτωση opus, yt-dlp, πηγές ffmpeg
    database.py         SQLite (σταθμοί, ένταση)
    library.py           σκανάρισμα τοπικής μουσικής
    permissions.py        έλεγχος ρόλου DJ
  player/
    guild_player.py       η "μηχανή" αναπαραγωγής (ανά server)
  cogs/
    music.py                browsing, links, έλεγχος
    radio.py                  εντολές /radio
  ui/
    browse_views.py           μενού φακέλου/τραγουδιού
    now_playing_view.py         κουμπιά ελέγχου
```

## Άδεια χρήσης

MIT — δες το [LICENSE](LICENSE).
