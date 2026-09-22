/*
 * External real-time chat translation.
 *
 * Per-player feature toggled from the "IC.Speech" verb panel. When enabled:
 * - What the player types in Say / Me is translated to Spanish before being
 *   broadcast in-game.
 * - The original text is also translated to English and written to the game
 *   log, so staff can moderate in English regardless of the spoken language.
 *
 * Uses the free Google Translate endpoint through rust_g's async HTTP so the
 * game loop is never blocked (the calling verb simply yields until the reply
 * arrives or the request times out).
 */

/// Base endpoint used for translation requests. Swap this if you host your own
/// (e.g. a LibreTranslate instance) and adapt parse_external_translation().
#define TRANSLATE_API_URL "https://translate.googleapis.com/translate_a/single"
/// How long we are willing to wait for a single translation before giving up.
#define TRANSLATE_TIMEOUT (5 SECONDS)
/// Language shown to other players in Say / Me.
#define TRANSLATE_LANG_DISPLAY "es"
/// Language written to the game logs.
#define TRANSLATE_LANG_LOG "en"

/**
 * Translates a piece of text using the external API.
 * MUST be called from a context that is allowed to sleep (verbs, async procs).
 * Returns the translated text, or the original text on any failure/timeout.
 */
/proc/external_translate(text, target_lang = TRANSLATE_LANG_DISPLAY, source_lang = "auto")
	if(!istext(text) || !length(trim(text)))
		return text

	var/url = "[TRANSLATE_API_URL]?client=gtx&sl=[source_lang]&tl=[target_lang]&dt=t&q=[url_encode(text)]"
	var/datum/http_request/request = new(RUSTG_HTTP_METHOD_GET, url)
	request.begin_async()
	UNTIL_OR_TIMEOUT(request.is_complete(), TRANSLATE_TIMEOUT)
	if(!request.is_complete())
		return text

	var/datum/http_response/response = request.into_response()
	if(response.errored || response.status_code != 200 || !length(response.body))
		return text

	var/translated = parse_external_translation(response.body)
	return length(translated) ? translated : text

/**
 * Parses the JSON returned by the Google Translate endpoint.
 * The payload looks like: [[["translated","original",...],["seg2",...]], ...]
 * Returns the concatenated translated text, or null on failure.
 */
/proc/parse_external_translation(body)
	var/list/decoded
	try
		decoded = json_decode(body)
	catch
		return null
	if(!islist(decoded) || !length(decoded))
		return null

	var/list/segments = decoded[1]
	if(!islist(segments))
		return null

	var/result = ""
	for(var/list/segment in segments)
		if(islist(segment) && length(segment) && istext(segment[1]))
			result += segment[1]
	return length(result) ? result : null

/// Toggle button that lives in the IC -> Speech verb panel.
/mob/verb/toggle_chat_translation()
	set name = "Toggle Translation"
	set category = "IC.Speech"
	set hidden = TRUE

	if(!client)
		return
	client.translate_chat_enabled = !client.translate_chat_enabled
	if(client.translate_chat_enabled)
		to_chat(src, span_notice("Chat translation ENABLED: your Say/Me will be shown in Spanish and logged in English."))
	else
		to_chat(src, span_notice("Chat translation DISABLED."))

/**
 * Async handler for a translated Say. Translates the original message to the
 * display language for broadcast, and to the log language for the game log.
 */
/mob/proc/handle_translated_say(message)
	set waitfor = FALSE
	if(!message)
		return
	var/spanish = external_translate(message, TRANSLATE_LANG_DISPLAY)
	var/english = external_translate(message, TRANSLATE_LANG_LOG)
	if(QDELETED(src))
		return
	if(english)
		log_talk("(TRANSLATED) said: [english]", LOG_SAY)
	say(spanish || message)

/**
 * Async handler for a translated Me emote. Same behaviour as Say, but routed
 * through the custom emote system.
 */
/mob/proc/handle_translated_me(message, message_type = NONE)
	set waitfor = FALSE
	if(!message)
		return
	var/spanish = external_translate(message, TRANSLATE_LANG_DISPLAY)
	var/english = external_translate(message, TRANSLATE_LANG_LOG)
	if(QDELETED(src))
		return
	if(english)
		log_message("(TRANSLATED) me: [english]", LOG_EMOTE)
	emote("me", message_type, spanish || message, intentional = TRUE)

/**
 * Async handler for the RECEIVER side. When a listener has translation enabled,
 * the message they hear is translated to English and shown to them, so they can
 * read incoming Spanish speech/emotes in English.
 */
/mob/proc/handle_translated_hear(raw_message, atom/movable/speaker, is_emote = FALSE)
	set waitfor = FALSE
	if(!length(raw_message))
		return
	var/english = external_translate(raw_message, TRANSLATE_LANG_LOG)
	if(QDELETED(src) || !client)
		return
	if(!length(english) || english == raw_message)
		return
	to_chat(src, span_notice("<i>[speaker]: [english]</i>"))
	if(is_emote)
		log_message("(TRANSLATED) emote [key_name(speaker)]: [english]", LOG_EMOTE, log_globally = FALSE)
	else
		log_message("(TRANSLATED) heard [key_name(speaker)]: [english]", LOG_SAY, log_globally = FALSE)

#undef TRANSLATE_API_URL
#undef TRANSLATE_TIMEOUT
#undef TRANSLATE_LANG_DISPLAY
#undef TRANSLATE_LANG_LOG
