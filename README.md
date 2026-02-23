# beets-multigenre

A [beets](https://beets.io) plugin that reads **all** GENRE tags from your audio files and stores them in a queryable flexible attribute.

## The Problem

Beets only stores a single `genre` field per track. When taggers like [Lidarr](https://lidarr.audio) or [MusicBrainz Picard](https://picard.musicbrainz.org) write multiple GENRE tags to your files (e.g. `Industrial Metal`, `Neue Deutsche HäRte`, `Alternative Metal`, `Electro-Industrial`), beets discards all but the first one.

This means queries and smart playlists based on genre are unreliable — a Rammstein track tagged with 5 genres including `Neue Deutsche HäRte` would only match on `Industrial Metal`.

## The Solution

`beets-multigenre` reads all GENRE tags directly from the audio file using mutagen and stores them as a semicolon-separated string in a flexible attribute (`multi_genres` by default). You can then query against this field using beets' regex query syntax.

**Before:**
```
$ beet list -f '$genre $album' artist:Rammstein
Industrial Metal Mutter
Industrial Metal Sehnsucht
```

**After:**
```
$ beet list -f '$multi_genres $album' artist:Rammstein
Industrial Metal;Neue Deutsche HäRte;Alternative Metal;Heavy Metal;Rock;Electronic;Industrial;Gothic Metal Mutter
Industrial Metal;Alternative Metal;Neue Deutsche HäRte;Rock;Industrial;Electronic;Metal Sehnsucht
```

## Supported Formats

- FLAC (Vorbis comments)
- MP3 (ID3 TCON frame)
- OGG / OPUS (Vorbis comments)
- M4A / AAC (MP4 atoms)
- WavPack, Musepack, AIFF

## Installation

### Via pip (recommended)
```bash
pip install beets-multigenre
```

### Docker (linuxserver.io)

The [linuxserver.io beets image](https://docs.linuxserver.io/images/docker-beets/) uses its own Python environment at `/lsiopy`. To install the plugin and have it persist across container recreates, use a custom init script:

```bash
mkdir -p /path/to/beets/custom-cont-init.d
cat > /path/to/beets/custom-cont-init.d/install-plugins.sh << 'EOF'
#!/bin/bash
/lsiopy/bin/pip install --upgrade beets-multigenre
EOF
chmod +x /path/to/beets/custom-cont-init.d/install-plugins.sh
```

Then mount it in your `docker-compose.yml`:

```yaml
volumes:
  - ./beets/custom-cont-init.d:/custom-cont-init.d
```

The plugin will install automatically every time the container starts.

## Configuration

Add to your `config.yaml`:

```yaml
plugins: multigenre

multigenre:
  field: multi_genres   # flexible attribute name (default: multi_genres)
  separator: ";"        # separator between genres (default: ;)
  auto: yes             # run automatically on import (default: yes)
```

## Usage

### Run manually across your library
```bash
beet multigenre
```

### Run on a subset
```bash
beet multigenre artist:Rammstein
beet multigenre album:"Mutter"
```

### Force update all tracks (ignore existing values)
```bash
beet multigenre --force
```

### Query by genre
```bash
# Regex match - catches any track with "Neue Deutsche" anywhere in multi_genres
beet list multi_genres::"Neue Deutsche"

# Exact substring match
beet list multi_genres:"Industrial Metal"

# Multiple genres (OR) using regex
beet list multi_genres::"Neue Deutsche|Industrial Metal|Electro-Industrial"
```

### Smart playlists

Use with the [smartplaylist plugin](https://beets.readthedocs.io/en/stable/plugins/smartplaylist.html):

```yaml
smartplaylist:
  playlists:
    - name: 'Neue Deutsche Harte.m3u'
      query: 'multi_genres::"Neue Deutsche"'

    - name: 'Industrial Night.m3u'
      query: 'multi_genres::"Industrial|EBM|Neue Deutsche|Electro-Industrial"'

    - name: 'Gothic & Darkwave.m3u'
      query: 'multi_genres::"Gothic|Dark Wave|Dark Ambient|Death Rock"'

    - name: 'Synthwave.m3u'
      query: 'multi_genres::"Synthwave|Darksynth|Synth-Pop"'
```

Note: Use regex OR syntax (`field::"A|B|C"`) for OR logic. Multiple separate `field::` terms are AND logic.

## Why not just use lastgenre?

The `lastgenre` plugin fetches genres from Last.fm and stores up to `count` genres as a comma-separated string. This works but:

- Last.fm genre data may differ from MusicBrainz
- Overwrites genres already written by Lidarr/Picard
- Requires API calls and an internet connection
- Still limited to a single concatenated string field

`beets-multigenre` reads what's **already in your files** — no API calls, no overwriting, works offline, and respects the work your tagger already did.

## Crontab / Automation

If you run beets imports on a schedule, add `beet multigenre` after the import. The plugin skips already-tagged tracks by default so hourly runs are efficient:

```crontab
0 * * * * (timeout 3600 beet import -A -q /music; beet multigenre; beet splupdate) > /dev/null 2>&1
```

## Contributing

Issues and PRs welcome at [github.com/mkaltner/beets-multigenre](https://github.com/mkaltner/beets-multigenre).

## License

MIT

