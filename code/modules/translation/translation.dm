/*
 * External real-time chat translation.
 *
 * Per-player feature toggled from the "IC.Speech" verb panel. When enabled:
 * - What the player types in Say / Me is translated to Spanish before being
 *   broadcast in-game.
 * - Preset emotes from the emote window are also translated for broadcast.
 * - Incoming speech and emotes are shown in English (normal chat styling).
 * - The original text is written to the game log in English for moderation.
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
/// Language shown to other players in Say / Me / emotes.
#define TRANSLATE_LANG_DISPLAY "es"
/// Language written to the game logs and shown to players with translation on.
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

/**
 * Google Translate defaults to masculine pronouns for Spanish reflexive emotes.
 * Rewrites he/him/his to she/her when the speaker presents as female.
 */
/proc/fix_translation_gender(text, atom/movable/speaker)
	if(!istext(text) || !length(text) || !ismob(speaker))
		return text
	var/mob/M = speaker
	var/gender = M.get_visible_gender()
	if(M.pronouns == SHE_HER)
		gender = FEMALE
	else if(M.pronouns == HE_HIM)
		gender = MALE
	if(gender != FEMALE)
		return text
	// Pad with spaces so we only replace whole words (avoids mangling "the", etc.).
	text = " [text] "
	text = replacetext(text, " He's ", " She's ")
	text = replacetext(text, " he's ", " she's ")
	text = replacetext(text, " His ", " Her ")
	text = replacetext(text, " his ", " her ")
	text = replacetext(text, " Him ", " Her ")
	text = replacetext(text, " him ", " her ")
	text = replacetext(text, " He ", " She ")
	text = replacetext(text, " he ", " she ")
	return copytext(text, 2, length(text))

/// Toggle button that lives in the IC -> Speech verb panel.
/mob/verb/toggle_chat_translation()
	set name = "Toggle Translation"
	set category = "IC.Speech"
	set hidden = TRUE

	if(!client)
		return
	client.translate_chat_enabled = !client.translate_chat_enabled
	if(client.translate_chat_enabled)
		to_chat(src, span_notice("Chat translation ENABLED: Say/Me and emotes are translated for you and others see Spanish."))
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
 * Async handler for preset emotes triggered from the emote window (or any
 * intentional emote). Translates the text for IC broadcast and logging.
 */
/mob/proc/handle_translated_preset_emote(datum/emote/emote, params, type_override, intentional, targeted)
	set waitfor = FALSE
	if(QDELETED(src) || !emote)
		return
	var/msg = emote.select_message_type(src, intentional)
	if(params && emote.message_param)
		msg = emote.select_param(src, params)
	msg = emote.replace_pronoun(src, msg)
	if(!msg && emote.nomsg == FALSE)
		return
	if(length(msg) && copytext(msg, 1, 2) == "*")
		emote.run_emote(src, params, type_override, intentional, targeted)
		return
	var/display_msg = external_translate(msg, TRANSLATE_LANG_DISPLAY)
	var/english_msg = external_translate(msg, TRANSLATE_LANG_LOG)
	if(QDELETED(src))
		return
	emote.run_emote(src, params, type_override, intentional, targeted, display_msg || msg, english_msg || msg)

/**
 * Async handler for the RECEIVER side. When a listener has translation enabled,
 * the message they hear is translated to English and shown with normal chat
 * styling instead of the original Spanish text.
 */
/mob/proc/handle_translated_hear(raw_message, atom/movable/speaker, is_emote = FALSE, english_third_person = null, datum/language/message_language = null, list/spans = list(), list/message_mods = list(), radio_freq = null)
	set waitfor = FALSE
	if(!length(raw_message) || copytext(raw_message, 1, 2) == "*")
		return
	var/english
	if(english_third_person)
		english = english_third_person
	else
		english = external_translate(raw_message, TRANSLATE_LANG_LOG)
		english = fix_translation_gender(english, speaker)
	if(QDELETED(src) || !client)
		return
	if(!length(english))
		english = raw_message
	if(is_emote)
		to_chat(src, span_emote("<b>[speaker]</b> [english]"))
		log_message("(TRANSLATED) emote [key_name(speaker)]: [english]", LOG_EMOTE, log_globally = FALSE)
		return
	var/deaf_message
	var/deaf_type
	if(speaker != src)
		deaf_message = "<span class='name'>[speaker]</span> [speaker.verb_say] something but you cannot hear [speaker.p_them()]."
		deaf_type = 1
	var/translated = compose_message(speaker, message_language, english, radio_freq, spans, message_mods)
	if(isliving(src) && (stat == UNCONSCIOUS || stat == HARD_CRIT))
		translated = "<I>... You can almost hear something ...</I>"
	show_message(translated, MSG_AUDIBLE, deaf_message, deaf_type)
	log_message("(TRANSLATED) heard [key_name(speaker)]: [english]", LOG_SAY, log_globally = FALSE)

#undef TRANSLATE_API_URL
#undef TRANSLATE_TIMEOUT
#undef TRANSLATE_LANG_DISPLAY
#undef TRANSLATE_LANG_LOG
