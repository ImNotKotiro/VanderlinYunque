# YunqueBot

Bot independiente del código del juego. Pregunta al servidor DreamDaemon cuántos jugadores hay y puede publicarlo en Discord cada 15 minutos, o al momento si alguien usa un comando.

No importa nada del repositorio del juego. Habla con el puerto del servidor por `world.Topic` (`?status`).

## Carpetas

```text
Iniciar YunqueBot.bat   Arranca el bot de Discord
Probar YunqueBot.bat    Ejecuta el selftest
yunquebot.py            Punto de entrada por línea de comandos
configuracion/          .env y permisos.txt, con sus plantillas .example
datos/                  Lo que guarda el bot mientras funciona. No se sube al repositorio
logs/                   Un fichero por comando con cada petición. No se sube al repositorio
scripts/                Ayudantes de los .bat
bot/                    Código
  app.py                Núcleo: comandos y agenda de avisos
  config.py             Lectura de .env y permisos.txt
  formatting.py         Texto y embeds del estado del servidor
  server/               Conexión con DreamDaemon (world.Topic)
  game/                 Lectura de archivos del juego, como los libros
  features/             Un archivo por función del bot
  interfaces/           Consola y Discord
tests/                  Pruebas del selftest
```

## Arrancar con doble clic (Windows)

- `Probar YunqueBot.bat` ejecuta el selftest.
- `Iniciar YunqueBot.bat` arranca el bot de Discord. La primera vez crea `configuracion/.env` a partir de `.env.example` y lo abre para rellenarlo. Si falta `discord.py`, lo instala.

Buscan Python 3.10 o superior en este orden: la variable `YUNQUEBOT_PYTHON` con la ruta de `python.exe`, un `.venv` en esta carpeta, `py` y `python`.

## Probar sin Discord

Hace falta Python 3.10 o superior. No hace falta instalar nada para la consola ni para el selftest.

Desde `tools/yunquebot`:

```bash
python yunquebot.py selftest
python yunquebot.py console --demo
```

En la consola:

```text
> estado
> agenda
> salir
```

`agenda` enseña que el aviso es cada 15 minutos, sin esperar esos 15 minutos. `--demo` usa un conteo de ejemplo y no abre ninguna conexión.

Para consultar un servidor de verdad, sin Discord:

```bash
python yunquebot.py run estado --host 127.0.0.1 --port 1337
```

El servidor tiene que tener `COMMS_KEY` definida en `config/comms.txt`. Si está vacía, DreamDaemon rechaza todas las consultas. El bot no envía ni necesita esa clave: `status` es público en cuanto la clave existe.

## Discord

```bash
pip install -r requirements.txt
copy configuracion\.env.example configuracion\.env
python yunquebot.py discord
```

En `configuracion/.env`:

| Variable | Uso |
| --- | --- |
| `BYOND_HOST`, `BYOND_PORT` | Host y puerto de DreamDaemon |
| `UPDATE_INTERVAL_SECONDS` | `900` = 15 minutos. `0` deja solo los comandos |
| `DISCORD_TOKEN` | Token del bot |
| `DISCORD_CHANNEL_ID` | Canal donde se publica el conteo |
| `DISCORD_GUILD_ID` | Opcional. Si está, los comandos de barra aparecen al momento en ese servidor |
| `SERVER_NAME` | Nombre del mensaje. Por defecto `Yunque` |
| `MIN_PLAYERS_TO_ANNOUNCE` | El aviso automático solo sale si hay más jugadores que este número. Por defecto `5` |
| `PLAYER_BOOKS_DIR` | Carpeta de los libros de jugadores. Vacío: `data/player_generated_books` del repositorio. Una ruta relativa se toma desde la raíz del repositorio |

### Permisos

`configuracion/permisos.txt` dice dónde y quién puede usar los comandos de barra. No se sube al repositorio; para crearlo:

```bash
copy configuracion\permisos.example.txt configuracion\permisos.txt
```

Tiene tres secciones, con un valor por línea. Lo que va detrás de `#` se ignora.

| Sección | Contenido | Si está vacía |
| --- | --- | --- |
| `[canales]` | Ids de los canales donde se aceptan los comandos. Los hilos de esos canales también valen. Por mensaje privado se aceptan siempre | Cualquier canal |
| `[administradores]` | Ids de usuario de Discord | Nadie es administrador, y nadie puede usar los comandos de administrador |
| `[comandos_admin]` | Otros comandos que solo podrán usar los administradores, sin la barra | El resto de comandos son públicos |

`/banear_escritor`, `/desbanear_escritor` y `/escritores_baneados` son siempre de administrador, estén o no en `[comandos_admin]`.

Para hacer administrador a alguien:

1. En Discord, Ajustes de usuario > Avanzado > activa el Modo desarrollador.
2. Clic derecho sobre su nombre (en el chat o en la lista de miembros) > Copiar ID de usuario.
3. Pega el número en una línea debajo de `[administradores]`, sin `#` delante. Detrás puedes poner `# Nombre` para recordar quién es.
4. Reinicia el bot.

Si alguien usa un comando fuera de los canales permitidos, o un comando de administrador sin serlo, el bot se lo dice solo a esa persona. Por mensaje privado, los comandos de administrador siguen siendo solo para administradores. Con `DISCORD_GUILD_ID` los comandos solo existen en ese servidor, así que no aparecen por privado. Un comando de `[comandos_admin]` que no existe impide arrancar el bot. Reinicia el bot después de cambiar el fichero. La consola no aplica estos permisos.

El aviso automático no depende de estos permisos: siempre sale en `DISCORD_CHANNEL_ID`.

En el portal de Discord, invita el bot con los scopes `bot` y `applications.commands`, y con permiso para ver y escribir en el canal.

Al conectar, si hay más jugadores que `MIN_PLAYERS_TO_ANNOUNCE`, publica el conteo y lo repite cada 15 minutos. Cada aviso nuevo borra solo el aviso automático anterior. Los mensajes de la gente y las respuestas de `/estado` se quedan. Con ese número o menos no escribe en el canal. `/estado` responde siempre, en el canal donde se usa, si ese canal está permitido en `permisos.txt`. Si el servidor no contesta, el comando dice que no se pudo consultar y el aviso automático se omite.

`/biblioteca` pide elegir un listado y lo enseña:

| Opción | Valor en la consola | Origen |
| --- | --- | --- |
| Libros del código | `codigo` | `code/game/objects/items/books.dm` y `strings/books/` |
| Libros de trabajos | `trabajos` | Pendiente de ruta |
| Libros de jugadores | `jugadores` | `PLAYER_BOOKS_DIR` en `configuracion/.env`. Por defecto `data/player_generated_books` |

Un listado sin ruta responde que todavía no está disponible. Las rutas se definen en `default_libraries()` de `bot/features/books.py`.

Los libros de jugadores se leen como los guarda el juego: un `.json` por libro (`book_title`, `author`, `text`, `category`…) y el índice `_book_titles.json`. Si hay índice, solo cuentan los libros que aparecen en él, como dentro del juego; si no, se leen todos los `.json` de la carpeta. Los cambios se ven sin reiniciar el bot.

`/libro` y el título buscan en los libros del código y en los de jugadores. Basta con algunas palabras del título, en cualquier orden y sin tildes. Si hay varios, el bot pide precisar e indica de qué listado es cada uno.

- Un libro del código llega por mensaje privado como `.txt`, con el texto como se lee dentro del juego.
- Un libro de jugador llega por mensaje privado en varios mensajes de 500 caracteres como mucho: el primero con el título, el autor y la categoría, y los siguientes con el texto, cortado por párrafos o frases.

### Escribir un libro de jugador

1. `/escribir_libro` y el título (80 caracteres como mucho, que no exista ya). El bot escribe por mensaje privado.
2. Cada mensaje privado que se le envíe se añade al libro como un párrafo, y el bot lo marca con ✅. También vale un `.txt`; Discord convierte así los mensajes muy largos. Máximo 6000 caracteres en total, el `MAX_BOOK_LEN` del juego.
3. `/terminar_libro` y la categoría (Apocrypha & Grimoires, Myths & Tales, Legends & Accounts, Thesis o Eoratica) lo guarda. `/cancelar_libro` lo descarta.

Se guarda en `PLAYER_BOOKS_DIR` igual que lo haría la imprenta del juego: `<título codificado>.json` con `book_title`, `author` (nombre en Discord), `author_ckey` (`discord:<id>`), `icon` (`basic_book`), `text` en HTML y `category`, y el título se añade a `_book_titles.json`. Si no había índice, se crea con los libros que ya había en la carpeta. Sale al momento en `/biblioteca`; el juego lo carga al empezar la siguiente ronda.

El texto solo se recoge por mensaje privado: en los canales, Discord no deja leer los mensajes sin el permiso de contenido de mensajes. Cada persona tiene un borrador a la vez, y los borradores se pierden si el bot se reinicia. En la consola, las líneas que no son comandos van al borrador.

Los administradores pueden prohibir a alguien añadir libros:

- `/banear_escritor` y el usuario: ya no puede empezar ni terminar libros, y si estaba escribiendo uno se descarta. Sus libros ya publicados se quedan; se borran desde el juego. A un administrador no se le puede banear.
- `/desbanear_escritor` y el usuario: vuelve a poder.
- `/escritores_baneados`: quién está baneado, quién lo baneó y cuándo.

La lista se guarda en `datos/baneados_libros.json` y se mantiene al reiniciar. Seguir leyendo libros con `/biblioteca` y `/libro` lo pueden todos. En la consola se indica el id de Discord en lugar de elegir el usuario.

### Logs

Cada petición por Discord se añade al final de `logs/<comando>.txt`: `/biblioteca` en `biblioteca.txt`, `/libro` en `libro.txt`, `/estado` en `estado.txt`. Un comando nuevo crea su fichero solo. Los ficheros nunca se vacían ni se rotan.

Cada entrada lleva la fecha, el resultado (respondido, rechazado por canal o por administrador, o error), quién la hizo, el servidor y canal o mensaje privado, los parámetros y la respuesta. De `/libro` se guarda el aviso y el nombre del archivo enviado, no el texto completo del libro. Ni la consola ni el aviso automático escriben en los logs.

```text
[2026-11-18 12:45:03 +0100] respondido
Usuario: Pepe (@pepe, id 123456789012345678)
Lugar: Yunque (id 111) / #general (id 222)
Parámetros: titulo = Tome of Justice
Respuesta:
    Te envié **Tome of Justice** por mensaje privado.
    Adjunto por privado: Tome of Justice.txt (5321 caracteres)
```

## Añadir una función

1. Crea una clase en `bot/features/` que herede de `Feature`.
2. Define `id`, `command_names`, `description` y `run()`.
3. Pon `interval_seconds` en segundos si también debe publicarse sola, o déjalo en `None` si solo responde a un comando.
4. Regístrala en `build_features()` dentro de `bot/features/__init__.py`.

La consola, los comandos de barra y el aviso periódico la recogen solos. `run()` devuelve un `FeatureResult` con el texto. Ese mismo texto lo usan la consola y Discord.

Si la función necesita otro dato del servidor, añade un método a `ServerGateway` (en `bot/server/gateway.py`) e impleméntalo en `LiveServerGateway` y en `DemoServerGateway`, para que `--demo` y el selftest sigan pudiendo probarla sin Discord.
