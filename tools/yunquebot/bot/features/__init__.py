"""Registro de funciones. Añade aqui cada funcion nueva."""

from __future__ import annotations

from bot.config import Config
from bot.features.base import Feature, validate_features
from bot.features.book_writing import BookWritingFeature
from bot.features.books import BooksFeature, default_libraries
from bot.features.player_count import PlayerCountFeature
from bot.features.writer_bans import WriterBans
from bot.game.player_books import PlayerBookLibrary


def build_features(config: Config) -> list[Feature]:
    features: list[Feature] = [
        PlayerCountFeature(config),
        BooksFeature(default_libraries(config)),
        BookWritingFeature(PlayerBookLibrary(config.player_books_dir), WriterBans(config.writer_bans_path)),
    ]
    validate_features(features)
    return features
