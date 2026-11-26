"""Adaptador de Discord. Solo se importa al arrancar el modo discord."""

from __future__ import annotations

import asyncio
import io
import logging
import time

import discord
from discord import app_commands

from bot.app import App
from bot.config import ANNOUNCEMENTS_PATH, LOGS_DIR, ConfigError
from bot.features.base import Feature, Requester
from bot.interfaces.announcements import AnnouncementLog, message_belongs_to_bot
from bot.interfaces.request_log import Request, RequestLog

log = logging.getLogger("yunquebot")
DISCORD_MESSAGE_LIMIT = 1900
RETRY_SECONDS = 30.0
MAX_TEXT_ATTACHMENT_BYTES = 64 * 1024
CAPTURED_REACTION = "✅"


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
        super().__init__(
            intents=discord.Intents.default(),
            allowed_mentions=discord.AllowedMentions.none(),
        )
        self.app = app
        self.tree = app_commands.CommandTree(self)
        self.publish_task: asyncio.Task[None] | None = None
        self.announcements = AnnouncementLog(ANNOUNCEMENTS_PATH)
        self.announcements.load()
        self.requests = RequestLog(LOGS_DIR)

    async def setup_hook(self) -> None:
        for feature in self.app.features:
            for name in feature.command_names:
                self.tree.add_command(_slash_command(self.app, feature, name, self.requests))
        self.publish_task = asyncio.create_task(self._publish_loop())
        await self._sync_commands()

    async def on_ready(self) -> None:
        log.info("YunqueBot conectado como %s. Funciona correctamente.", self.user)
        interval = self.app.config.update_interval_seconds
        if interval:
            log.debug(
                "El conteo se publicará en el canal %s cada %s segundos si hay más de %s jugadores.",
                self.app.config.discord_channel_id,
                interval,
                self.app.config.min_players_to_announce,
            )
        else:
            log.debug("El aviso periódico está desactivado. Solo responden los comandos.")
        permissions = self.app.config.permissions
        if permissions.channel_ids:
            log.debug(
                "Los comandos solo se aceptan en los canales: %s.",
                ", ".join(map(str, sorted(permissions.channel_ids))),
            )
        else:
            log.debug("Sin canales en configuracion/permisos.txt. Los comandos se aceptan en cualquier canal.")
        admin_commands = self.app.admin_command_names()
        if admin_commands:
            log.debug(
                "Comandos solo para administradores: %s. Administradores: %s.",
                ", ".join(admin_commands),
                len(permissions.admin_ids),
            )
            if not permissions.admin_ids:
                log.warning(
                    "No hay administradores en configuracion/permisos.txt. Nadie podrá usar: %s.",
                    ", ".join(admin_commands),
                )

    async def on_message(self, message: discord.Message) -> None:
        """Solo mensajes privados: ahí Discord deja leer el texto sin permisos especiales."""
        if message.author.bot or message.guild is not None:
            return
        requester = _requester(message.author)
        capture = self.app.capture_text(requester, await _message_text(message))
        if capture is None:
            return
        try:
            if capture.accepted:
                await message.add_reaction(CAPTURED_REACTION)
            else:
                await message.reply(capture.reply)
        except discord.DiscordException:
            log.exception("No se pudo contestar al mensaje de %s.", requester.key)

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
                log.debug("Comandos registrados en el servidor %s: %s.", guild_id, len(synced))
                log.debug(
                    "Con DISCORD_GUILD_ID los comandos solo existen en ese servidor y no aparecen "
                    "por mensaje privado. Déjalo vacío para usarlos también por privado."
                )
            else:
                synced = await self.tree.sync()
                log.debug(
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
                log.debug("Publicado %s.", feature.id)
            else:
                log.debug(
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
            log.debug("El aviso anterior %s ya no está en el canal.", message_id)
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


def _slash_command(
    app: App,
    feature: Feature,
    name: str,
    requests: RequestLog,
) -> app_commands.Command:
    description = feature.command_description(name)
    argument = feature.command_argument(name)
    if argument and feature.command_argument_is_user(name):

        async def callback(interaction: discord.Interaction, valor: discord.User) -> None:
            shown = f"{valor.display_name} (@{valor.name}, id {valor.id})"
            await _answer_slash(interaction, app, feature, name, str(valor.id), requests, shown)

    elif argument:

        async def callback(interaction: discord.Interaction, valor: str) -> None:
            await _answer_slash(interaction, app, feature, name, valor, requests)

    else:

        async def callback(interaction: discord.Interaction) -> None:
            await _answer_slash(interaction, app, feature, name, "", requests)

    callback.__name__ = f"slash_{feature.id}_{name}"
    if argument:
        callback = app_commands.rename(valor=argument)(callback)
        help_text = feature.command_argument_description(name)
        if help_text:
            callback = app_commands.describe(valor=help_text)(callback)
        choices = feature.command_choices(name)
        if choices:
            options = [app_commands.Choice(name=label, value=value) for value, label in choices]
            callback = app_commands.choices(valor=options)(callback)
    return app_commands.command(name=name, description=description)(callback)


async def _answer_slash(
    interaction: discord.Interaction,
    app: App,
    feature: Feature,
    name: str,
    argument: str,
    requests: RequestLog,
    shown_argument: str | None = None,
) -> None:
    label = feature.command_argument(name)
    request = Request(
        command=name,
        user=_who(interaction),
        place=_where(interaction),
        arguments={label: shown_argument or argument} if label else {},
    )
    permissions = app.config.permissions
    parent_id = getattr(interaction.channel, "parent_id", None)
    private = interaction.guild_id is None
    if not permissions.accepts_channel(interaction.channel_id, parent_id, private):
        channels = ", ".join(f"<#{channel_id}>" for channel_id in sorted(permissions.channel_ids))
        text = clip(f"Este comando solo se puede usar por mensaje privado o en: {channels}")
        await interaction.response.send_message(text, ephemeral=True)
        requests.record(request, "rechazado: canal no permitido", text)
        return
    if not app.allows_command(name, interaction.user.id):
        text = "Este comando es solo para administradores del bot."
        await interaction.response.send_message(text, ephemeral=True)
        requests.record(request, "rechazado: no es administrador", text)
        return
    await interaction.response.defer(ephemeral=feature.reply_is_ephemeral(name))
    try:
        result = await asyncio.to_thread(
            feature.run, app.gateway, app.config, name, argument, _requester(interaction.user)
        )
    except Exception as exc:
        log.exception("Fallo el comando %s.", name)
        text = "No se pudo completar la consulta."
        await interaction.followup.send(text)
        requests.record(request, "error", f"{text}\nDetalle: {exc!r}")
        return
    if result.private and (result.attachment_text or result.private_messages):
        failure = await _send_private_book(interaction, result)
        if failure:
            await interaction.followup.send(failure)
            requests.record(request, "error: no se pudo enviar por privado", failure)
            return
        notice = result.embed_description or "Te envié el libro por mensaje privado."
        await interaction.followup.send(notice)
        if result.attachment_text:
            sent = f"Adjunto por privado: {result.attachment_name} ({len(result.attachment_text)} caracteres)"
        else:
            total = sum(len(message) for message in result.private_messages)
            sent = f"Enviado por privado en {len(result.private_messages)} mensajes ({total} caracteres)"
        requests.record(request, "respondido", f"{notice}\n{sent}")
        return
    await interaction.followup.send(**_payload(result))
    requests.record(request, "respondido" if result.ok else "respondido sin éxito", result.text)


def _requester(user: discord.abc.User) -> Requester:
    return Requester(key=f"discord:{user.id}", name=user.display_name)


async def _message_text(message: discord.Message) -> str:
    """Discord convierte los mensajes muy largos en un adjunto message.txt."""
    parts = [message.content]
    for attachment in message.attachments:
        if not attachment.filename.lower().endswith(".txt") or attachment.size > MAX_TEXT_ATTACHMENT_BYTES:
            continue
        try:
            data = await attachment.read()
        except discord.DiscordException:
            log.exception("No se pudo leer el adjunto %s.", attachment.filename)
            continue
        parts.append(data.decode("utf-8-sig", errors="replace"))
    return "\n\n".join(part.strip() for part in parts if part.strip())


def _who(interaction: discord.Interaction) -> str:
    user = interaction.user
    return f"{user.display_name} (@{user.name}, id {user.id})"


def _where(interaction: discord.Interaction) -> str:
    if interaction.guild_id is None:
        return f"Mensaje privado (canal {interaction.channel_id})"
    guild = interaction.guild.name if interaction.guild else "?"
    channel = getattr(interaction.channel, "name", None) or "?"
    return f"{guild} (id {interaction.guild_id}) / #{channel} (id {interaction.channel_id})"


async def _send_private_book(interaction: discord.Interaction, result) -> str | None:
    """Devuelve el aviso de error, o None si el libro llegó."""
    try:
        if result.attachment_text:
            book = discord.File(
                io.BytesIO(result.attachment_text.encode("utf-8-sig")),
                filename=result.attachment_name or "libro.txt",
            )
            await interaction.user.send(content=result.embed_title or result.attachment_name, file=book)
        else:
            for message in result.private_messages:
                await interaction.user.send(message)
    except discord.Forbidden:
        return "No pude enviarte un mensaje privado. Permite los mensajes directos de miembros del servidor."
    except discord.HTTPException:
        log.exception("No se pudo enviar el libro por privado.")
        return "No pude enviarte el libro completo por mensaje privado."
    return None


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
