# YunqueBot

Bot independiente del código del juego. Pregunta al servidor DreamDaemon cuántos jugadores hay y puede publicarlo en Discord cada 15 minutos, o al momento si alguien usa un comando.

No importa nada del repositorio del juego. Habla con el puerto del servidor por `world.Topic` (`?status`).

## Probar sin Discord

Hace falta Python 3.10 o superior. No hace falta instalar nada para la consola ni para el selftest.

Desde `tools/yunquebot`:

```bash
python yunquebot.py selftest
python yunquebot.py console --demo
```

En la consola:

```text
> jugadores
> players
> agenda
> salir
```

`agenda` enseña que el aviso es cada 15 minutos, sin esperar esos 15 minutos. `--demo` usa un conteo de ejemplo y no abre ninguna conexión.

Para consultar un servidor de verdad, sin Discord:

```bash
python yunquebot.py run jugadores --host 127.0.0.1 --port 1337
```

El servidor tiene que tener `COMMS_KEY` definida en `config/comms.txt`. Si está vacía, DreamDaemon rechaza todas las consultas. El bot no envía ni necesita esa clave: `status` es público en cuanto la clave existe.

## Discord

```bash
pip install -r requirements.txt
copy .env.example .env
python yunquebot.py discord
```

En `.env`:

| Variable | Uso |
| --- | --- |
| `BYOND_HOST`, `BYOND_PORT` | Host y puerto de DreamDaemon |
| `UPDATE_INTERVAL_SECONDS` | `900` = 15 minutos. `0` deja solo los comandos |
| `DISCORD_TOKEN` | Token del bot |
| `DISCORD_CHANNEL_ID` | Canal donde se publica el conteo |
| `DISCORD_GUILD_ID` | Opcional. Si está, `/jugadores` aparece al momento en ese servidor |
| `SERVER_NAME` | Nombre del mensaje. Por defecto `Yunque` |
| `MIN_PLAYERS_TO_ANNOUNCE` | El aviso automático solo sale si hay más jugadores que este número. Por defecto `5` |

En el portal de Discord, invita el bot con los scopes `bot` y `applications.commands`, y con permiso para ver y escribir en el canal.

Al conectar, si hay más jugadores que `MIN_PLAYERS_TO_ANNOUNCE`, publica el conteo y lo repite cada 15 minutos. Con 5 o menos no escribe en el canal. `/jugadores` y `/players` responden siempre, en el canal donde se usan. Si el servidor no contesta, el comando dice que no se pudo consultar y el aviso automático se omite.

## Añadir una función

1. Crea una clase en `features/` que herede de `Feature`.
2. Define `id`, `command_names`, `description` y `run()`.
3. Pon `interval_seconds` en segundos si también debe publicarse sola, o déjalo en `None` si solo responde a un comando.
4. Regístrala en `build_features()` dentro de `features/__init__.py`.

La consola, los comandos de barra y el aviso periódico la recogen solos. `run()` devuelve un `FeatureResult` con el texto. Ese mismo texto lo usan la consola y Discord.

Si la función necesita otro dato del servidor, añade un método a `ServerGateway` e impleméntalo en `LiveServerGateway` y en `DemoServerGateway`, para que `--demo` y el selftest sigan pudiendo probarla sin Discord.
