"""beets-multigenre: Read all GENRE tags from audio files into a searchable field.

Beets only stores a single genre tag per track, discarding any additional
GENRE tags written by taggers like Lidarr/MusicBrainz. This plugin reads
all GENRE tags directly from the audio file using mutagen and stores them
as a semicolon-separated string in a flexible attribute (default: multi_genres),
making all genres available for querying and smart playlists.

Supported formats: FLAC, MP3, OGG, M4A, OPUS, WavPack, Musepack, AIFF
"""

from beets.plugins import BeetsPlugin
from beets import ui


class MultiGenrePlugin(BeetsPlugin):
    def __init__(self):
        super().__init__()
        self.config.add({
            'field': 'multi_genres',
            'separator': ';',
            'auto': True,
        })

        if self.config['auto'].get(bool):
            self.register_listener('album_imported', self.album_imported)
            self.register_listener('item_imported', self.item_imported)

    def commands(self):
        cmd = ui.Subcommand(
            'multigenre',
            help='read all GENRE tags from files and store in multi_genres field'
        )
        cmd.parser.add_option(
            '-f', '--force',
            action='store_true', default=False,
            help='overwrite existing multi_genres values'
        )
        cmd.func = self.command
        return [cmd]

    def command(self, lib, opts, args):
        force = opts.force
        items = lib.items(list(args))
        updated = 0
        skipped = 0
        for item in items:
            field_name = self.config['field'].as_str()
            if not force and item.get(field_name):
                skipped += 1
                continue
            if self._update_item(item):
                item.store()
                updated += 1
        self._log.info(f'updated {updated} items, skipped {skipped} already tagged')

    def album_imported(self, lib, album):
        for item in album.items():
            if self._update_item(item):
                item.store()

    def item_imported(self, lib, item):
        if self._update_item(item):
            item.store()

    def _update_item(self, item):
        """Read all GENRE tags from the file and store as separator-joined string."""
        try:
            path = item.path
            if isinstance(path, bytes):
                path = path.decode('utf-8', errors='replace')

            genres = self._read_all_genres(path)
            if genres:
                separator = self.config['separator'].as_str()
                field_name = self.config['field'].as_str()
                item[field_name] = separator.join(genres)
                return True
        except Exception as e:
            self._log.warning(f'error processing {item}: {e}')
        return False

    def _read_all_genres(self, path):
        """Read multiple GENRE tags from audio files using mutagen."""
        try:
            import mutagen
            f = mutagen.File(path)
            if f is None or f.tags is None:
                return []

            tags = f.tags

            # Vorbis comments: FLAC, OGG, OPUS - multiple GENRE fields supported
            if hasattr(tags, 'keys'):
                genres = []
                for key in tags.keys():
                    if key.upper() == 'GENRE':
                        val = tags[key]
                        if isinstance(val, list):
                            genres.extend([str(v).strip() for v in val if str(v).strip()])
                        else:
                            s = str(val).strip()
                            if s:
                                genres.append(s)
                if genres:
                    return genres

            # ID3 tags: MP3, AIFF - TCON frame holds genres
            if 'TCON' in tags:
                tcon = tags['TCON']
                if hasattr(tcon, 'genres'):
                    return [g.strip() for g in tcon.genres if g.strip()]
                s = str(tcon).strip()
                return [s] if s else []

            # MP4/M4A - freeform atom
            if '\xa9gen' in tags:
                val = tags['\xa9gen']
                if isinstance(val, list):
                    return [str(v).strip() for v in val if str(v).strip()]
                s = str(val).strip()
                return [s] if s else []

            return []
        except Exception as e:
            self._log.debug(f'mutagen error for {path}: {e}')
            return []
