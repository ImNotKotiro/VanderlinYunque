"""Adaptador de Discord. Solo se importa al arrancar el modo discord."""

from __future__ import annotations

import asyncio
import io
import logging
import time

import discord
from discord import app_commands

from announcements import AnnouncementLog, message_belongs_to_bot
from app import App
from config import TOOL_ROOT, ConfigError
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


class YunqueDiscordBot(discord.Client):
    def __init__(self, app: App) -> None:
        super().__init__(intents=discord.Intents.default())
        self.app = app
        self.tree = app_commands.CommandTree(self)
        self.publish_task: asyncio.Task[None] | None = None
        self.announcements = AnnouncementLog(TOOL_ROOT / ".announcements.json")
        self.announcements.load()

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
                "El conteo se publicará en el canal %s cada %s segundos si hay más de %s jugadores.",
                self.app.config.discord_channel_id,
                interval,
                self.app.config.min_players_to_announce,
            )
        else:
            log.info("El aviso periódico está desactivado. Solo responden los comandos.")

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
                if result.announce:
                    previous = self.announcements.get(feature.id)
                    sent = await channel.send(**_payload(result))
                    self.announcements.remember(feature.id, sent.id)
                    await self._delete_previous(channel, previous)
            except Exception:
                log.exception("No se pudo publicar %s.", feature.id)
                continue
            self.app.mark_ran(feature, time.monotonic())
            if result.announce:
                log.info("Publicado %s.", feature.id)
            else:
                log.info(
                    "Aviso de %s omitido: hacen falta más de %s jugadores.",
                    feature.id,
                    self.app.config.min_players_to_announce,
                )

    async def _delete_previous(self, channel: discord.abc.Messageable, message_id: int | None) -> None:
        if message_id is None or self.user is None:
            return
        fetch = getattr(channel, "fetch_message", None)
        if fetch is None:
            return
        try:
            message = await fetch(message_id)
        except discord.DiscordException:
            log.info("El aviso anterior %s ya no está en el canal.", message_id)
            return
        if not message_belongs_to_bot(message.author.id, self.user.id):
            log.warning("No se borra el mensaje %s porque no lo escribió el bot.", message_id)
            return
        try:
            await message.delete()
        except discord.DiscordException:
            log.exception("No se pudo borrar el aviso anterior %s.", message_id)

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
    description = feature.command_description(name)
    argument = feature.command_argument(name)
    if argument:

        async def callback(interaction: discord.Interaction, titulo: str) -> None:
            await _answer_slash(interaction, app, feature, name, titulo)

    else:

        async def callback(interaction: discord.Interaction) -> None:
            await _answer_slash(interaction, app, feature, name, "")

    callback.__name__ = f"slash_{feature.id}_{name}"
    if argument:
        callback = app_commands.describe(titulo="Título del libro, o parte de él.")(callback)
    return app_commands.command(name=name, description=description)(callback)


async def _answer_slash(
    interaction: discord.Interaction,
    app: App,
    feature: Feature,
    name: str,
    argument: str,
) -> None:
    await interaction.response.defer(ephemeral=feature.reply_is_ephemeral(name))
    try:
        result = await asyncio.to_thread(feature.run, app.gateway, app.config, name, argument)
    except Exception:
        log.exception("Fallo el comando %s.", name)
        await interaction.followup.send("No se pudo completar la consulta.")
        return
    if result.private and result.attachment_text:
        sent = await _send_private_book(interaction, result)
        if not sent:
            return
        notice = result.embed_description or "Te envié el libro por mensaje privado."
        await interaction.followup.send(notice)
        return
    await interaction.followup.send(**_payload(result))


async def _send_private_book(interaction: discord.Interaction, result) -> bool:
    book = discord.File(
        io.BytesIO(result.attachment_text.encode("utf-8-sig")),
        filename=result.attachment_name or "libro.txt",
    )
    try:
        await interaction.user.send(content=result.embed_title or result.attachment_name, file=book)
    except discord.Forbidden:
        await interaction.followup.send(
            "No pude enviarte un mensaje privado. Permite los mensajes directos de miembros del servidor."
        )
        return False
    except discord.HTTPException:
        log.exception("No se pudo enviar el libro por privado.")
        await interaction.followup.send("No pude enviarte el archivo por mensaje privado.")
        return False
    return True


def _payload(result) -> dict[str, object]:
    if not result.embed_title and not result.embed_description:
        return {"content": clip(result.text)}
    embed = discord.Embed(
        title=result.embed_title or None,
        description=result.embed_description or None,
        color=result.embed_color,
    )
    for name, value in result.embed_fields:
        embed.add_field(name=name, value=value, inline=True)
    if result.embed_footer:
        embed.set_footer(text=result.embed_footer)
    return {"embed": embed}
