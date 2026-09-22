"""Adaptador de Discord. Solo se importa al arrancar el modo discord."""

from __future__ import annotations

import asyncio
import logging
import time

import discord
from discord import app_commands

from app import App
from config import ConfigError
from features.base import Feature

log = logging.getLogger("yunquebot")
DISCORD_MESSAGE_LIMIT = 1900
RETRY_SECONDS = 30.0


def clip(text: str, limit: int = DISCORD_MESSAGE_LIMIT) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def run_discord(app: App) -> None:
    if not app.config.discord_token:
        raise ConfigError("Falta DISCORD_TOKEN. Hace falta para el modo discord, no para la consola.")
    if app.config.discord_channel_id is None:
        raise ConfigError("Falta DISCORD_CHANNEL_ID. Es el canal donde se publica el conteo.")
    bot = YunqueDiscordBot(app)
    try:
        bot.run(app.config.discord_token, log_handler=None)
    except discord.LoginFailure as exc:
        raise ConfigError("DISCORD_TOKEN fue rechazado. Revisa el token del bot.") from exc
    except discord.PrivilegedIntentsRequired as exc:
        raise ConfigError(
            "Discord rechazó un intent privilegiado. "
            "Deja DISCORD_MESSAGE_CONTENT=0 o activa Message Content Intent en el portal."
        ) from exc


class YunqueDiscordBot(discord.Client):
    def __init__(self, app: App) -> None:
        intents = discord.Intents.default()
        intents.message_content = app.config.discord_message_content
        super().__init__(intents=intents)
        self.app = app
        self.tree = app_commands.CommandTree(self)
        self.publish_task: asyncio.Task[None] | None = None

    async def setup_hook(self) -> None:
        for feature in self.app.features:
            for name in feature.command_names:
                self.tree.add_command(_slash_command(self.app, feature, name))
        self.publish_task = asyncio.create_task(self._publish_loop())
        await self._sync_commands()

    async def on_ready(self) -> None:
        user = self.user
        log.info("Conectado como %s.", user)
        interval = self.app.config.update_interval_seconds
        if interval:
            log.info(
                "El conteo se publicará en el canal %s cada %s segundos.",
                self.app.config.discord_channel_id,
                interval,
            )
        else:
            log.info("El aviso periódico está desactivado. Solo responden los comandos.")

    async def on_message(self, message: discord.Message) -> None:
        if not self.app.config.discord_message_content:
            return
        if message.author.bot or not message.content:
            return
        prefix = self.app.config.command_prefix
        content = message.content.strip()
        if not content.startswith(prefix):
            return
        remainder = content[len(prefix) :].strip()
        if not remainder:
            return
        command = remainder.split(maxsplit=1)[0]
        if self.app.feature_for(command) is None:
            return
        async with message.channel.typing():
            result = await asyncio.to_thread(self.app.run_command, command)
        await message.channel.send(clip(result.text))

    async def close(self) -> None:
        task = self.publish_task
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        await super().close()

    async def _sync_commands(self) -> None:
        try:
            guild_id = self.app.config.discord_guild_id
            if guild_id:
                guild = discord.Object(id=guild_id)
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                log.info("Comandos registrados en el servidor %s: %s.", guild_id, len(synced))
            else:
                synced = await self.tree.sync()
                log.info(
                    "Comandos globales registrados: %s. Pueden tardar en aparecer.",
                    len(synced),
                )
        except discord.DiscordException:
            log.exception("No se pudieron registrar los comandos. El aviso periódico sigue activo.")

    async def _publish_loop(self) -> None:
        await self.wait_until_ready()
        while not self.is_closed():
            await self._publish_due()
            delay = self.app.seconds_until_next(time.monotonic())
            if delay <= 0:
                delay = RETRY_SECONDS
            await asyncio.sleep(delay)

    async def _publish_due(self) -> None:
        now = time.monotonic()
        due = self.app.due_features(now)
        if not due:
            return
        try:
            channel = await self._channel()
        except discord.DiscordException:
            log.exception("No se pudo abrir el canal %s.", self.app.config.discord_channel_id)
            return
        for feature in due:
            try:
                result = await asyncio.to_thread(feature.run, self.app.gateway, self.app.config)
                await channel.send(clip(result.text))
            except Exception:
                log.exception("No se pudo publicar %s.", feature.id)
                continue
            self.app.mark_ran(feature, time.monotonic())
            log.info("Publicado %s.", feature.id)

    async def _channel(self) -> discord.abc.Messageable:
        channel_id = self.app.config.discord_channel_id
        if channel_id is None:
            raise discord.DiscordException("Falta el canal.")
        channel = self.get_channel(channel_id)
        if channel is None:
            channel = await self.fetch_channel(channel_id)
        if not isinstance(channel, discord.abc.Messageable):
            raise discord.DiscordException(f"El canal {channel_id} no admite mensajes.")
        return channel


def _slash_command(app: App, feature: Feature, name: str) -> app_commands.Command:
    async def callback(interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        try:
            result = await asyncio.to_thread(feature.run, app.gateway, app.config)
        except Exception:
            log.exception("Fallo el comando %s.", name)
            await interaction.followup.send("No se pudo completar la consulta.")
            return
        await interaction.followup.send(clip(result.text))

    callback.__name__ = f"slash_{feature.id}_{name}"
    return app_commands.command(name=name, description=feature.description)(callback)
