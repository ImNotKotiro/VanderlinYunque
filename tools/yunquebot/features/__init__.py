"""Registro de funciones. Añade aqui cada funcion nueva."""

from __future__ import annotations

from config import Config
from features.base import Feature, validate_features
from features.books import BooksFeature
from features.player_count import PlayerCountFeature


def build_features(config: Config) -> list[Feature]:
    features: list[Feature] = [
        PlayerCountFeature(config),
        BooksFeature(),
    ]
    validate_features(features)
    return features
