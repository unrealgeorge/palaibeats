<div align="center">

# PalaiBeats

A self-hosted Discord music bot for a single server. Runs 24/7 on a Raspberry Pi via Docker.

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.7%2B-5865F2)](https://github.com/Rapptz/discord.py)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED)](docker-compose.yml)

[![English](https://img.shields.io/badge/lang-English-black)](README.md)
[![Ελληνικά](https://img.shields.io/badge/lang-Ελληνικά-0D1B2A)](README.el.md)

</div>

---

Plays music from a local folder, from a link (YouTube, SoundCloud, and most
other sites, via yt-dlp), or from an internet radio stream — all through
Discord slash commands. No paid hosting, no Lavalink node: it's one Docker
container plus your own files.

## Contents

- [Features](#features)
- [Requirements](#requirements)
- [Setup](#setup)
  - [1. Get the code](#1-get-the-code)
  - [2. Create the Discord bot](#2-create-the-discord-bot)
  - [3. Create the DJ role](#3-create-the-dj-role)
  - [4. Configure](#4-configure)
  - [5. Add your music](#5-add-your-music)
  - [6. Run it](#6-run-it)
- [Commands](#commands)
- [Using radio stations](#using-radio-stations)
- [Updating](#updating)
- [Troubleshooting](#troubleshooting)
- [Project structure](#project-structure)
- [License](#license)

## Features

- **Local library** — browse your music by folder straight in Discord
  (`/browse`: pick a folder, pick a song, it plays). No typing song names.
- **Links** — `/play <link>` plays YouTube, SoundCloud, and most other
  sites yt-dlp supports. Plain text works too (it searches YouTube).
- **Radio** — save stream URLs with `/radio add` and play them with
  `/radio play`. Reconnects automatically if a stream drops.
- **Playback controls** — pause, resume, skip, stop, volume, loop, queue,
  a now-playing panel with buttons.
- **DJ role** — anyone can browse and see what's playing; only members
  with a role you choose can actually control playback.
- **Leaves on its own** — disconnects when everyone leaves the voice
  channel, or after sitting idle for a while.

## Requirements

- A Linux host with Docker and Docker Compose (a Raspberry Pi 4 works fine).
- A Discord account and a server you manage.
- Your music files.

## Setup

### 1. Get the code

```bash
git clone https://github.com/<your-username>/palaibeats.git
cd palaibeats
```

(Or download and extract the ZIP from GitHub.)

### 2. Create the Discord bot

1. Open the [Discord Developer Portal](https://discord.com/developers/applications) and click **New Application**. Name it whatever you like.
2. Go to **Bot** (left sidebar). Click **Reset Token** and copy it somewhere safe — you'll paste it into `.env` in a moment. Anyone with this token can control your bot, so don't share it or commit it to Git.
3. Still on the **Bot** page, leave **Presence Intent**, **Server Members Intent**, and **Message Content Intent** all switched **off**. PalaiBeats doesn't use them.
4. Go to **OAuth2 → URL Generator**.
   - Under **Scopes**, check `bot` and `applications.commands`.
   - A **Bot Permissions** box appears below. Check: `View Channels`, `Send Messages`, `Embed Links`, `Connect`, `Speak`.
   - Scroll down to **Generated URL**, copy it.
5. Paste that URL into your browser, pick your server, click **Authorize**.
6. Turn on Developer Mode in Discord (User Settings → Advanced), then right-click your server's icon and **Copy Server ID**. That's your `GUILD_ID`.

### 3. Create the DJ role

In your server: **Server Settings → Roles → Create Role**. Name it `DJ`
(or anything — you'll set the name in `.env`). Assign it to whoever
should be allowed to control playback. Server admins and the server
owner can always control the bot, with or without the role.

### 4. Configure

```bash
cp .env.example .env
```

Open `.env` and fill in at least `DISCORD_TOKEN` and `GUILD_ID`. Every
other setting has a sensible default — see the comments in
`.env.example` for what each one does (DJ role name, default volume,
idle timeout, etc).

### 5. Add your music

Create a `music` folder next to `docker-compose.yml` and organize it
like this:

```
music/
  Some Artist/
    song1.mp3
    song2.flac
  Chill Playlist/
    song3.m4a
```

Each top-level folder becomes one browsable category in `/browse`.
Files can be nested deeper inside a folder too — they still belong to
that top-level folder. Supported formats: mp3, flac, wav, m4a, ogg,
opus, aac, wma.

If your music already lives somewhere else on the host, set
`MUSIC_PATH` in `.env` to that folder's path instead of creating a new
one.

### 6. Run it

```bash
docker compose up -d --build
docker compose logs -f palaibeats
```

Once you see it log in and sync commands, the slash commands should
show up in Discord within a minute or two.

## Commands

| Command | Who can use it | What it does |
|---|---|---|
| `/browse` | anyone | Browse the local library by folder |
| `/play <link or text>` | DJ | Play a link or search |
| `/queue` | anyone | Show what's queued |
| `/nowplaying` | anyone | Current track/station, with control buttons |
| `/skip` | DJ | Skip the current track |
| `/pause` / `/resume` | DJ | Pause / resume |
| `/stop` | DJ | Stop and clear the queue |
| `/leave` | DJ | Disconnect from voice |
| `/volume <0-200>` | DJ | Set volume percentage |
| `/loop` | DJ | Toggle looping the current track |
| `/refresh-library` | DJ | Rescan the music folder for new files |
| `/radio add <name> <url>` | DJ | Save a station |
| `/radio remove <name>` | DJ | Delete a saved station |
| `/radio list` | anyone | List saved stations |
| `/radio play <name>` | DJ | Stream a saved station |
| `/radio stop` | DJ | Stop the radio stream |

## Using radio stations

`/radio add` needs the **direct audio stream URL**, not a station's
website and not a `.pls`/`.m3u` playlist link. Many stations only
publish a playlist file — open it in a text editor and look for a line
like `File1=https://...`; that's the URL you want.

## Updating

```bash
git pull
docker compose up -d --build
```

## Troubleshooting

**`RuntimeError: davey library needed in order to use voice`**
Discord now requires the DAVE end-to-end encryption protocol for voice
connections, and discord.py needs a separate package for it. Make sure
`requirements.txt` includes `davey>=0.1.6`, then rebuild:
```bash
docker compose build --no-cache palaibeats && docker compose up -d
```

**Port already in use (health check)**
`HEALTH_CHECK_PORT` binds directly on the host (the container uses
`network_mode: host`), so it has to be free across *all* your
containers, not just this one. Pick a different port in `.env`, or
leave it blank to disable the health endpoint entirely.

**Slash commands don't appear**
They sync to the single server set by `GUILD_ID` on startup, which can
take a minute or two to show up client-side. Check the logs for a
"Synced N application command(s)" line — if it's missing, double-check
`GUILD_ID` and that the bot was actually invited to that server.

**"Only members with the DJ role can do that"**
Expected — give yourself (or whoever should control playback) the role
named in `DJ_ROLE_NAME` (default `DJ`). Server admins and the owner
bypass this automatically.

**No sound / bot joins but stays silent**
Usually ffmpeg or libopus. Check the logs right after `/play` for an
ffmpeg error, and confirm the container logged something like `Loaded
libopus via ...` on startup.

## Project structure

```
src/palaibeats/
  config.py        settings, loaded from .env
  bot.py            wiring: cogs, intents, command sync
  core/
    audio.py          opus loading, yt-dlp, ffmpeg sources
    database.py         SQLite (radio stations, volume)
    library.py           local music folder scanning
    permissions.py        DJ role check
  player/
    guild_player.py       playback state machine (per server)
  cogs/
    music.py                browsing, links, controls
    radio.py                  /radio commands
  ui/
    browse_views.py           folder/song menus
    now_playing_view.py         control buttons
```

## License

MIT — see [LICENSE](LICENSE).
