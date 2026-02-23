"""Tests for beets-multigenre plugin."""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from beets_multigenre import MultiGenrePlugin


class TestMultiGenrePlugin(unittest.TestCase):

    def setUp(self):
        self.plugin = MultiGenrePlugin()

    def test_read_flac_multiple_genres(self):
        """Test reading multiple GENRE tags from a FLAC file."""
        mock_tags = MagicMock()
        mock_tags.keys.return_value = ['GENRE', 'GENRE', 'ARTIST', 'TITLE']

        # Simulate mutagen returning list for repeated GENRE keys
        def getitem(key):
            if key.upper() == 'GENRE':
                return ['Industrial Metal', 'Neue Deutsche HäRte', 'Alternative Metal']
            return []

        mock_tags.__getitem__ = getitem
        mock_tags.keys = lambda: ['GENRE']

        mock_file = MagicMock()
        mock_file.tags = mock_tags

        with patch('mutagen.File', return_value=mock_file):
            genres = self.plugin._read_all_genres('/fake/path/test.flac')

        self.assertIn('Industrial Metal', genres)
        self.assertIn('Neue Deutsche HäRte', genres)
        self.assertIn('Alternative Metal', genres)
        self.assertEqual(len(genres), 3)

    def test_read_mp3_tcon(self):
        """Test reading TCON frame from MP3."""
        mock_tcon = MagicMock()
        mock_tcon.genres = ['Rock', 'Alternative Rock', 'Grunge']

        mock_tags = MagicMock()
        mock_tags.keys.return_value = []
        mock_tags.__contains__ = lambda self, key: key == 'TCON'
        mock_tags.__getitem__ = lambda self, key: mock_tcon

        mock_file = MagicMock()
        mock_file.tags = mock_tags

        with patch('mutagen.File', return_value=mock_file):
            genres = self.plugin._read_all_genres('/fake/path/test.mp3')

        self.assertIn('Rock', genres)
        self.assertIn('Grunge', genres)

    def test_empty_file(self):
        """Test handling file with no tags."""
        with patch('mutagen.File', return_value=None):
            genres = self.plugin._read_all_genres('/fake/path/test.flac')
        self.assertEqual(genres, [])

    def test_update_item_stores_joined_genres(self):
        """Test that _update_item joins genres with separator."""
        mock_item = MagicMock()
        mock_item.path = b'/fake/path/test.flac'

        with patch.object(self.plugin, '_read_all_genres',
                          return_value=['Industrial Metal', 'Neue Deutsche HäRte']):
            result = self.plugin._update_item(mock_item)

        self.assertTrue(result)
        mock_item.__setitem__.assert_called_once_with(
            'multi_genres',
            'Industrial Metal;Neue Deutsche HäRte'
        )

    def test_update_item_no_genres(self):
        """Test that _update_item returns False when no genres found."""
        mock_item = MagicMock()
        mock_item.path = b'/fake/path/test.flac'

        with patch.object(self.plugin, '_read_all_genres', return_value=[]):
            result = self.plugin._update_item(mock_item)

        self.assertFalse(result)

    def test_strips_whitespace(self):
        """Test that genre values are stripped of whitespace."""
        mock_tags = MagicMock()
        mock_tags.keys = lambda: ['GENRE']
        mock_tags.__getitem__ = lambda self, key: ['  Rock  ', ' Metal ']

        mock_file = MagicMock()
        mock_file.tags = mock_tags

        with patch('mutagen.File', return_value=mock_file):
            genres = self.plugin._read_all_genres('/fake/path/test.flac')

        self.assertIn('Rock', genres)
        self.assertIn('Metal', genres)


if __name__ == '__main__':
    unittest.main()
