
/* EMOTE DATUMS */
/datum/emote/living
	mob_type_allowed_typecache = /mob/living
	mob_type_blacklist_typecache = list(/mob/living/brain)

// ............... Pray ..................
/datum/emote/living/pray
	key = "pray"
	key_third_person = "reza"
	message = "se pone a rezar."
	restraint_check = FALSE
	emote_type = EMOTE_VISIBLE

/mob/living/carbon/human/verb/emote_pray()
	set name = "Pray"
	set category = "Emotes.Actions"

	emote("pray", intentional = TRUE)

/datum/emote/living/pray/run_emote(mob/user, params, type_override, intentional, targeted)
	if(HAS_TRAIT(user, TRAIT_ATHEISM_CURSE))
		to_chat(user, span_danger("Rezar es para idiotas."))
		return

	if(!intentional || (!ishuman(user) && !isroguespirit(user)))
		return ..() //they get to do a fake prayer cause they SUCK

	var/mob/living/carbon/follower = user
	var/datum/patron/patron = follower.patron

	var/in_literal_hell = ( istype(get_area(user), /area/underworld) )
	if(!in_literal_hell && !patron?.can_pray(follower))
		return

	INVOKE_ASYNC(src, PROC_REF(async_pray), user, patron)

/datum/emote/living/pray/proc/async_pray(mob/living/carbon/follower, datum/patron/patron)

	var/prayer = tgui_input_text(follower, "Whisper your Prayer", "Prayer", multiline = TRUE)
	if(!prayer)
		return

	/* admin stuff */
	send_prayer(follower, prayer, patron.name)
	follower.log_message("(follower of [patron]) prays: [prayer]", LOG_GAME)

	follower.whisper(prayer)

	if(SEND_SIGNAL(follower, COMSIG_EMOTE_PRAY, prayer) & CARBON_PRAY_CANCEL)
		return

	SEND_SIGNAL(follower, COMSIG_PRAYER_COMPLETED)

	for(var/mob/living/crit_guy in hearers(2, follower)) //as of writing succumb_timer does literally nothing btw
		crit_guy.succumb_timer = world.time

/proc/send_prayer(mob/living/follower, prayer, patron_name)
	var/ident_string = "[follower.key]/([follower.real_name]) (follower of [patron_name])"
	var/bigger = FALSE
	if((follower.job == JOB_PRIEST) || (follower.job == JOB_PRIEST_FEM))
		ident_string += "[SPAN_GOD_ASTRATA("(PRIEST)")]"
		bigger = TRUE
	if(follower.has_quirk(/datum/quirk/vice/addiction/godfearing))
		ident_string += "[SPAN_GOD_GENERIC("(GODFEARING)")]"
	/// Usually I hate not using spans properly, but in this case it's going to make my life easier.
	var/lowercase_god = "generic"
	if(patron_name in COLORFUL_PATRONS)
		lowercase_god = ckey(patron_name)//Getting the game to correctly pull this has been the biggest pain in the butt.
	var/message = SPAN_PRAYER_WRAPPER(span_admin("[span_prefix("PRAYER: ")][ident_string] [ADMIN_SM(follower)] [ADMIN_NRT(follower)] [ADMIN_FLW(follower)] prays: <span class='god_[lowercase_god]'>[html_encode(prayer)]</span>"))
	if(bigger)
		message = span_slightlylarger(message)
	for(var/client/admin_client in GLOB.admins)
		if(check_rights_for(admin_client, R_ADMIN))
			to_chat(admin_client, message)
			if(admin_client.prefs.read_preference(/datum/preference/bitwise/toggles) & SOUND_PRAYERS)
				admin_client.mob.playsound_local(admin_client, 'sound/misc/yeoldebwoink.ogg', 100)


// ............... Me (custom emote) ..................
/datum/emote/living/custom
	key = "me"
	key_third_person = "custom"
	message_param = "%t"
	mute_time = 0
	ignore_mute_time = TRUE

/datum/emote/living/custom/can_run_emote(mob/user, status_check, intentional)
	. = ..()
	if(!. || !intentional)
		return FALSE

	if(!isnull(user.ckey) && is_banned_from(user.ckey, "Emote"))
		to_chat(user, span_boldwarning("You cannot send custom emotes (banned)."))
		return FALSE

	if(QDELETED(user))
		return FALSE

	if(user.client?.prefs.muted & MUTE_IC)
		to_chat(user, span_boldwarning("I cannot send IC messages (muted)."))
		return FALSE

	#ifdef USES_PQ
	if(get_playerquality(user.client?.ckey) <= -10)
		to_chat(user, span_boldwarning("Unrecognized emote."))
		return
		#endif

/datum/emote/living/custom/proc/check_invalid(mob/user, input)
	. = TRUE
	if(copytext(input,1,5) == "says")
		to_chat(user, "<span class='danger'>Invalid emote.</span>")
	else if(copytext(input,1,9) == "exclaims")
		to_chat(user, "<span class='danger'>Invalid emote.</span>")
	else if(copytext(input,1,6) == "yells")
		to_chat(user, "<span class='danger'>Invalid emote.</span>")
	else if(copytext(input,1,5) == "asks")
		to_chat(user, "<span class='danger'>Invalid emote.</span>")
	else
		. = FALSE

/datum/emote/living/custom/run_emote(mob/user, params, type_override = null, intentional = FALSE, targeted)
	if(QDELETED(user))
		return FALSE

	message = params
	if(type_override)
		emote_type = type_override
	. = ..()
	message = null
	emote_type = EMOTE_VISIBLE

/datum/emote/living/custom/replace_pronoun(mob/user, message)
	return message

/* A terrible idea, commenting out subtler
// ............... Subtle ..................
/datum/emote/living/subtle
	key = "subtle"
	key_third_person = "subtleemote"
	message_param = "%t"
	restraint_check = TRUE

/datum/emote/living/subtle/can_run_emote(mob/user, status_check, intentional)
	. = ..() && intentional

/datum/emote/living/subtle/run_emote(mob/user, params, type_override = null, intentional = FALSE)
	if(!can_run_emote(user, TRUE, intentional))
		return FALSE
	if(is_banned_from(user.ckey, "Emote"))
		to_chat(user, "<span class='boldwarning'>I cannot send custom emotes (banned).</span>")
		return FALSE
	else if(QDELETED(user))
		return FALSE
	else if(user.client && user.client.prefs.muted & MUTE_IC)
		to_chat(user, "<span class='boldwarning'>I cannot send IC messages (muted).</span>")
		return FALSE
	else if(!params)
		var/custom_emote = copytext(sanitize(input("What does your character subtly do?") as text|null), 1, MAX_MESSAGE_LEN)
		if(custom_emote)
			message = custom_emote
			emote_type = EMOTE_VISIBLE
	else
		message = params
		if(type_override)
			emote_type = type_override

	user.log_message("SUBTLE - " + message, LOG_EMOTE)
	message = "<b>[user]</b> " + message

	for(var/mob/M in GLOB.dead_mob_list)
		if(!M.client || isnewplayer(M))
			continue
		var/T = get_turf(user)
		if(M.stat == DEAD && M.client && (M.client.prefs?.read_preference(/datum/preference/bitwise/chat_toggles) & CHAT_GHOSTSIGHT) && !(M in viewers(T, null)))
			M.show_message(message)

	user.visible_message("<i>[message]</i>", vision_distance = 1)
*/

// ............... A ..................
/datum/emote/living/attnwhistle
	key = "attnwhistle"
	message = "chifla para llamar la atención!"
	message_muffled = "hace un ruido sordo."
	emote_type = EMOTE_AUDIBLE
/mob/living/carbon/human/verb/emote_attnwhistle()
	set name = "Attnwhistle"
	set category = "Emotes.Noises"
	emote("attnwhistle", intentional = TRUE)

/datum/emote/living/scream/agony
	key = "agony"
	message = "grita en agonía!"
	emote_type = EMOTE_AUDIBLE
	only_forced_audio = TRUE

/datum/emote/living/aggro
	key = "aggro"
	key_third_person = "aggro"
	message = ""
	nomsg = TRUE
	emote_type = EMOTE_AUDIBLE
	only_forced_audio = TRUE

// ............... B ..................
/datum/emote/living/blush
	key = "blush"
	key_third_person = "blushes"
	message = "se sonroja."

/datum/emote/living/breathgasp
	key = "breathgasp"
	key_third_person = "breathgasps"
	message = "se queda sin aliento!"
	emote_type = EMOTE_AUDIBLE

/datum/emote/living/bow
	key = "bow"
	key_third_person = "bows"
	message = "hace una reverencia."
	message_param = "bows to %t."
	restraint_check = TRUE
	emote_type = EMOTE_VISIBLE
/mob/living/carbon/human/verb/emote_bow()
	set name = "Bow"
	set category = "Emotes.Actions"
	emote("bow", intentional = TRUE)

/datum/emote/living/burp
	key = "burp"
	key_third_person = "burps"
	message = "eructa."
	message_muffled = "hace un ruido ahogado."
	emote_type = EMOTE_AUDIBLE

/mob/living/carbon/human/verb/emote_burp()
	set name = "Burp"
	set category = "Emotes.Noises"
	emote("burp", intentional = TRUE)


// ............... C ..................
/datum/emote/living/chuckle
	key = "chuckle"
	key_third_person = "chuckles"
	message = "se ríe entre dientes."
	message_muffled = "hace un ruido ahogado."
	emote_type = EMOTE_AUDIBLE

/mob/living/carbon/human/verb/emote_chuckle()
	set name = "Chuckle"
	set category = "Emotes.Noises"
	emote("chuckle", intentional = TRUE)

/datum/emote/living/choke
	key = "choke"
	key_third_person = "chokes"
	message = "se atraganta!"
	emote_type = EMOTE_AUDIBLE
	ignore_silent = TRUE
/mob/living/carbon/human/verb/emote_choke()
	set name = "Choke"
	set category = "Emotes.Noises"
	emote("choke", intentional = TRUE)

/datum/emote/living/sniff
	key = "sniff"
	key_third_person = "sniffs"
	message = "olisquea el aire..."
	emote_type = EMOTE_AUDIBLE
	ignore_silent = TRUE

/mob/living/carbon/human/verb/emote_sniff()
	set name = "Sniff"
	set category = "Emotes.Noises"
	emote("sniff", intentional = TRUE)

/datum/emote/living/cross
	key = "crossarms"
	key_third_person = "crossesarms"
	message = "se cruza de brazos."
	restraint_check = TRUE
	emote_type = EMOTE_VISIBLE
/mob/living/carbon/human/verb/emote_crossarms()
	set name = "Crossarms"
	set category = "Emotes.Actions"
	emote("crossarms", intentional = TRUE)

/datum/emote/living/collapse
	key = "collapse"
	key_third_person = "collapses"
	message = "se desploma."
	emote_type = EMOTE_AUDIBLE

/datum/emote/living/collapse/run_emote(mob/user, params, type_override, intentional, targeted)
	. = ..()
	if(isliving(user))
		var/mob/living/L = user
		L.SetKnockdown(40)

/datum/emote/living/choke
	key = "choke"
	key_third_person = "chokes"
	message = "se atraganta!"
	emote_type = EMOTE_AUDIBLE

/datum/emote/living/cough
	key = "cough"
	key_third_person = "coughs"
	message = "tose."
	message_muffled = "hace un ruido sordo."
	emote_type = EMOTE_AUDIBLE

/mob/living/carbon/human/verb/emote_cough()
	set name = "Cough"
	set category = "Emotes.Noises"
	emote("cough", intentional = TRUE)

/datum/emote/living/sickcough
	key = "sickcough"
	key_third_person = "sickcoughs"
	message = "tose muy fuerte."
	message_muffled = "hace un ruido sordo muy fuerte."
	emote_type = EMOTE_AUDIBLE

/datum/emote/living/sickcough/run_emote(mob/user, params, type_override, intentional, targeted)
	. = ..()
	for(var/mob/living/carbon/human/witness in hearers(user)) // yes, you can proc your own cough!
		if(HAS_ANY_OF_TRAITS(witness, list(TRAIT_NOBREATH, TRAIT_NOMOOD, TRAIT_TOXIMMUNE, TRAIT_DISEASE_RESISTANCE)))
			continue
		var/cough_prob = 2
		if(witness.has_quirk(/datum/quirk/vice/paranoid))
			cough_prob += 2 // hypochondriac
		if(witness.has_quirk(/datum/quirk/vice/weak_heart))
			cough_prob += 2
		if(!prob(cough_prob))
			continue
		var/p_emote = prob(50) ? pick("yawn", "cough", "clearthroat") : "sickcough"
		addtimer(CALLBACK(witness, TYPE_PROC_REF(/mob, emote), p_emote), rand(12 SECONDS, 2 MINUTES), TIMER_UNIQUE|TIMER_DELETE_ME)

/datum/emote/living/clearthroat
	key = "clearthroat"
	key_third_person = "clearsthroat"
	message = "se aclara la garganta."
	message_muffled = "hace un ruido sordo."
	emote_type = EMOTE_AUDIBLE

/mob/living/carbon/human/verb/emote_clearthroat()
	set name = "Clearthroat"
	set category = "Emotes.Noises"
	emote("clearthroat", intentional = TRUE)

// ............... D ..................
/datum/emote/living/dance
	key = "dance"
	key_third_person = "dances"
	message = "baila."
	restraint_check = TRUE
	emote_type = EMOTE_VISIBLE
/mob/living/carbon/human/verb/emote_dance()
	set name = "Dance"
	set category = "Emotes.Actions"
	emote("dance", intentional = TRUE)

/datum/emote/living/death
	key = "death"
	emote_type = EMOTE_AUDIBLE
	nomsg = TRUE
	only_forced_audio = TRUE
	stat_allowed = UNCONSCIOUS
	mob_type_ignore_stat_typecache = list(/mob/living)

/datum/emote/living/deathgasp
	key = ""
	key_third_person = ""
	message = "exhala su último aliento.."
	message_monkey = "lets out a faint chimper as it collapses and stops moving..."
	message_simple =  "se desploma, perdiendo todas sus fuerzas."
	stat_allowed = HARD_CRIT
	cooldown = 15 SECONDS

/datum/emote/living/deathgasp/run_emote(mob/user, params, type_override, intentional, targeted)
	var/mob/living/simple_animal/S = user
	if(istype(S) && S.deathmessage)
		message_simple = S.deathmessage
	. = ..()
	message_simple = initial(message_simple)
	if(user.deathsound)
		if(isliving(user))
			var/mob/living/L = user
			if(!L.can_speak_vocal() || L.oxyloss >= 50)
				return //stop the sound if oxyloss too high/cant speak
		playsound(user, user.deathsound, 200, TRUE, TRUE)

/datum/emote/living/drool
	key = "drool"
	key_third_person = "drools"
	message = "babea."
	emote_type = EMOTE_VISIBLE
/mob/living/carbon/human/verb/emote_drool()
	set name = "Drool"
	set category = "Emotes.Actions"
	emote("drool", intentional = TRUE)

/datum/emote/living/drown
	key = "drown"
	emote_type = EMOTE_AUDIBLE
	nomsg = TRUE
	only_forced_audio = TRUE
	ignore_silent = TRUE

// ............... E ..................
/datum/emote/living/embed
	key = "embed"
	emote_type = EMOTE_AUDIBLE
	nomsg = TRUE
	only_forced_audio = TRUE

// ............... F ..................
/datum/emote/living/faint
	key = "faint"
	key_third_person = "faints"
	message = "se desmaya."
	emote_type = EMOTE_VISIBLE

/mob/living/carbon/human/verb/emote_faint()
	set name = "Faint"
	set category = "Emotes.Actions"
	emote("faint", intentional = TRUE)

/datum/emote/living/faint/run_emote(mob/user, params, type_override, intentional, targeted)
	. = ..()
	if(iscarbon(user))
		var/mob/living/carbon/L = user
		if(L.getShockStage() > (GET_MOB_ATTRIBUTE_VALUE(L, STAT_ENDURANCE) * 9))
			L.setDir(2)
			L.SetUnconscious(200)
		else
			L.Knockdown(10)

/datum/emote/living/fatigue
	key = "fatigue"
	emote_type = EMOTE_AUDIBLE
	nomsg = TRUE
	only_forced_audio = TRUE

/datum/emote/living/frown
	key = "frown"
	key_third_person = "frowns"
	message = "frunce el ceño."
	emote_type = EMOTE_VISIBLE

/mob/living/carbon/human/verb/emote_frown()
	set name = "Frown"
	set category = "Emotes.Actions"
	emote("frown", intentional = TRUE)

/datum/emote/living/scream/firescream
	key = "firescream"
	nomsg = TRUE
	emote_type = EMOTE_AUDIBLE
	only_forced_audio = TRUE

// ............... G ..................
/datum/emote/living/gag
	key = "gag"
	key_third_person = "gags"
	message = "hace una arcada."
	emote_type = EMOTE_AUDIBLE
	ignore_silent = TRUE
/mob/living/carbon/human/verb/emote_gag()
	set name = "Gag"
	set category = "Emotes.Noises"
	emote("gag", intentional = TRUE)

/datum/emote/living/gasp
	key = "gasp"
	key_third_person = "gasps"
	message = "hace un grito ahogado!"
	message_muffled = "hace un ruido ahogado."
	emote_type = EMOTE_AUDIBLE
	stat_allowed = HARD_CRIT

/mob/living/carbon/human/verb/emote_gasp()
	set name = "Gasp"
	set category = "Emotes.Noises"
	emote("gasp", intentional = TRUE)

/datum/emote/living/giggle
	key = "giggle"
	key_third_person = "giggles"
	message = "suelta una risita."
	message_mime = "suelta una risita silenciosa!"
	message_muffled = "suelta una risa ahogada."
	emote_type = EMOTE_AUDIBLE

/mob/living/carbon/human/verb/emote_giggle()
	set name = "Giggle"
	set category = "Emotes.Noises"
	emote("giggle", intentional = TRUE)

/datum/emote/living/glare
	key = "glare"
	key_third_person = "glares"
	message = "lanza una mirada fulminante."
	message_param = "lanza una mirada fulminante a %t."
	emote_type = EMOTE_VISIBLE
/mob/living/carbon/human/verb/emote_glare()
	set name = "Glare"
	set category = "Emotes.Actions"
	emote("glare", intentional = TRUE)

/datum/emote/living/grin
	key = "grin"
	key_third_person = "grins"
	message = "esboza una sonrisa."
	emote_type = EMOTE_VISIBLE

/mob/living/carbon/human/verb/emote_grin()
	set name = "Grin"
	set category = "Emotes.Actions"
	emote("grin", intentional = TRUE)

/datum/emote/living/groan
	key = "groan"
	key_third_person = "groans"
	message = "hace un quejido."
	message_muffled = "hace un quejido ahogado."
	emote_type = EMOTE_AUDIBLE

/datum/emote/living/attack
	key = "attack"
	key_third_person = "attacks"
	message = ""
	nomsg = TRUE
	message_muffled = "hace un gemido ahogado."
	emote_type = EMOTE_AUDIBLE
	show_runechat = FALSE

/mob/living/carbon/human/verb/emote_groan()
	set name = "Groan"
	set category = "Emotes.Noises"
	emote("groan", intentional = TRUE)

/datum/emote/living/grimace
	key = "grimace"
	key_third_person = "grimaces"
	message = "hace muecas."
	emote_type = EMOTE_VISIBLE
/mob/living/carbon/human/verb/emote_grimace()
	set name = "Grimace"
	set category = "Emotes.Actions"
	emote("grimace", intentional = TRUE)

/datum/emote/living/groin
	key = "groin"
	emote_type = EMOTE_AUDIBLE
	nomsg = TRUE
	only_forced_audio = TRUE

// ............... H ..................
/datum/emote/living/haltyell
	key = "haltyell"
	message = "grita que se detengan!"
	emote_type = EMOTE_AUDIBLE
	only_forced_audio = TRUE

/datum/emote/living/haltyellorphan

	key = "haltyellorphan"
	message = "intenta gritar con fuerza para que se detengan!"
	emote_type = EMOTE_AUDIBLE
	only_forced_audio = TRUE

/datum/emote/living/hmm
	key = "hmm"
	key_third_person = "hmms"
	message = "hmms."
	message_muffled = "hace un hmm ahogado."
	emote_type = EMOTE_AUDIBLE
/mob/living/carbon/human/verb/emote_hmm()
	set name = "Hmm"
	set category = "Emotes.Noises"
	emote("hmm", intentional = TRUE)

/datum/emote/living/hop
	key = "hop"
	key_third_person = "hops"
	message = "salta!"
	hands_use_check = TRUE
	emote_type = EMOTE_VISIBLE | EMOTE_AUDIBLE
/mob/living/carbon/human/verb/emote_hop()
	set name = "Hop"
	set category = "Emotes.Actions"
	emote("hop", intentional = TRUE)

/datum/emote/living/hop/run_emote(mob/living/user, params, type_override, intentional, targeted)
	. = ..()
	animate(user, pixel_y = user.pixel_y + 4, time = 0.1 SECONDS)
	animate(pixel_y = user.pixel_y - 4, time = 0.1 SECONDS)

/datum/emote/living/hop/get_sound(mob/living/user)
	return 'sound/items/weapons/thudswoosh.ogg'

/datum/emote/living/huh
	key = "huh"
	key_third_person = "huhs"
	message_muffled = "hace un ruido ahogado."
	emote_type = EMOTE_AUDIBLE
	nomsg = TRUE

/mob/living/carbon/human/verb/emote_huh()
	set name = "Huh"
	set category = "Emotes.Noises"
	emote("huh", intentional = TRUE)

/datum/emote/living/hum
	key = "hum"
	key_third_person = "hums"
	message = "hums."
	message_muffled = "hace un hum ahogado."
	emote_type = EMOTE_AUDIBLE

/mob/living/carbon/human/verb/emote_hum()
	set name = "Hum"
	set category = "Emotes.Noises"
	emote("hum", intentional = TRUE)

/datum/emote/living/hug
	key = "hug"
	key_third_person = "hugs"
	message = ""
	message_param = "abraza a %t."
	emote_type = EMOTE_VISIBLE
	restraint_check = TRUE

/mob/living/carbon/human/verb/emote_hug()
	set name = "Hug"
	set category = "Emotes.Actions"
	emote("hug", intentional = TRUE, targeted = TRUE)

/datum/emote/living/hug/can_run_emote(mob/living/user, status_check = TRUE , intentional)
	. = ..()
	if(HAS_TRAIT(user, TRAIT_EORA_CURSE))
		var/mob/living/carbon/human/H = user
		to_chat(H, "<span class='warning'>La idea me repugna!</span>")
		H.cursed_freak_out()
		return FALSE

/datum/emote/living/hug/adjacentaction(mob/user, mob/target)
	. = ..()
	if(!user || !target)
		return
	if(ishuman(target))
		var/mob/living/carbon/human/H = target
		// cursed is the one being hugged
		if(HAS_TRAIT(H, TRAIT_EORA_CURSE))
			to_chat(H, "<span class='warning'>Me siento inexplicablemente asqueado!</span>")
			H.cursed_freak_out()
			return

/datum/emote/living/hug/adjacentaction(mob/user, mob/target)
	. = ..()
	if(!user || !target)
		return
	if(ishuman(target))
		var/mob/living/carbon/H = target
		H.add_stress(/datum/stress_event/hug)
		playsound(target, pick('sound/vo/hug.ogg'), 100, FALSE, -1)

		if(user.mind)
			SEND_SIGNAL(user, COMSIG_MOB_HUGGED, H)
			record_round_statistic(STATS_HUGS_MADE)

/datum/emote/living/headpat
	key = "headpat"
	key_third_person = "pats"
	message = ""
	message_param = "le da una palmadita en la cabeza a %t."
	emote_type = EMOTE_VISIBLE
	restraint_check = TRUE

/mob/living/carbon/human/verb/emote_headpat()
	set name = "Headpat"
	set category = "Emotes.Actions"
	emote("headpat", intentional = TRUE, targeted = TRUE)

/datum/emote/living/headpat/adjacentaction(mob/user, mob/target)
	. = ..()
	if(!user || !target)
		return
	if(ishuman(target))
		var/mob/living/carbon/human/H = target
		playsound(target, pick('sound/vo/hug.ogg'), 100, FALSE, -1)
		if(israkshari(H))
			if(prob(10))
				H.emote("purr")


// ............... I ..................
/datum/emote/living/idle
	key = "idle"
	emote_type = EMOTE_AUDIBLE
	nomsg = TRUE
	only_forced_audio = TRUE

// ............... J ..................
/datum/emote/living/jump
	key = "jump"
	key_third_person = "jumps"
	message = "salta!"
	restraint_check = TRUE
	emote_type = EMOTE_AUDIBLE
	nomsg = TRUE
	only_forced_audio = TRUE

// ............... K ..................
/datum/emote/living/kiss
	key = "kiss"
	key_third_person = "kisses"
	message = "da un beso."
	message_param = "besa a %t."
	emote_type = EMOTE_VISIBLE


/datum/emote/living/kiss/can_run_emote(mob/living/user, status_check = TRUE , intentional)
	. = ..()
	if(HAS_TRAIT(user, TRAIT_EORA_CURSE))
		var/mob/living/carbon/human/H = user
		to_chat(H, "<span class='warning'>La idea me repugna!</span>")
		H.cursed_freak_out()
		return FALSE

/mob/living/carbon/human/verb/emote_kiss()
	set name = "Kiss"
	set category = "Emotes.Actions"
	emote("kiss", intentional = TRUE, targeted = TRUE)

/datum/emote/living/kiss/adjacentaction(mob/user, mob/target)
	. = ..()
	message_param = initial(message_param) // re
	if(!user || !target)
		return
	if(ishuman(user) && ishuman(target))
		var/mob/living/carbon/human/H = user
		var/mob/living/carbon/human/E = target

		// cursed is the one being kissed
		if(HAS_TRAIT(E, TRAIT_EORA_CURSE))
			to_chat(E, "<span class='warning'>Me siento inexplicablemente asqueado!</span>")
			E.cursed_freak_out()

		// anti pedophile logging
		var/log_msg
		if(E.age == AGE_CHILD)
			log_msg = "[key_name(H)][ADMIN_FLW(H)] kissed [key_name(E)] [ADMIN_FLW(E)], a CHILD!"
			if(H.age == AGE_CHILD)
				log_msg += " As a child."
			else
				log_msg += " As an adult."
			message_admins(log_msg)

		var/do_change
		if(target.loc == user.loc)
			do_change = TRUE
		if(!do_change)
			if(H.pulling == target)
				do_change = TRUE
		if(do_change)
			if(H.zone_selected == BODY_ZONE_PRECISE_MOUTH)
				message_param = "besa a %t apasionadamente."
			else if(H.zone_selected == BODY_ZONE_PRECISE_EARS)
				message_param = "besa a %t en la oreja."
				if(E.dna.species?.id == "elf")
					if(!E.cmode)
						to_chat(target, span_love("Da cosquillas..."))
			else if(H.zone_selected == BODY_ZONE_PRECISE_R_EYE || H.zone_selected == BODY_ZONE_PRECISE_L_EYE)
				message_param = "besa a %t en la ceja."
			else
				message_param = "besa a %t en \the [parse_zone(H.zone_selected)]."
	playsound(target, pick('sound/vo/kiss (1).ogg','sound/vo/kiss (2).ogg'), 100, FALSE, -1)
	if(user.mind)
		record_round_statistic(STATS_KISSES_MADE)

// ............... L ..................
/datum/emote/living/laugh
	key = "laugh"
	key_third_person = "laughs"
	message = "se ríe."
	message_mime = "se ríe en silencio!."
	message_muffled = "hace una risa ahogada."
	emote_type = EMOTE_AUDIBLE

/datum/emote/living/laugh/can_run_emote(mob/living/user, status_check = TRUE , intentional)
	return ..() && user.can_speak()

/datum/emote/living/laugh/run_emote(mob/user, params, type_override, intentional, targeted)
	. = ..()
	if(user.mind)
		record_featured_stat(FEATURED_STATS_JOKESTERS, user)
		record_round_statistic(STATS_LAUGHS_MADE)

/mob/living/carbon/human/verb/emote_laugh()
	set name = "Laugh"
	set category = "Emotes.Noises"
	emote("laugh", intentional = TRUE)

/datum/emote/living/leap
	key = "leap"
	key_third_person = "leaps"
	message = "da un gran salto!"
	restraint_check = TRUE
	only_forced_audio = TRUE

/datum/emote/living/look
	key = "look"
	key_third_person = "looks"
	message = "mira al vacío."
	message_param = "mira a %t."

/datum/emote/living/lower	// the emote that signals an animal is tamed. Previously smile was used. The chicken smiles. The pig smiles. Wut.
	key = "lower_head"
	key_third_person = "lowers_head"
	message = "baja la cabeza."
	message_param = "baja la cabeza."
	emote_type = EMOTE_VISIBLE


// ............... M ..................
/datum/emote/living/meditate
	key = "meditate"
	key_third_person = "meditate"
	message = "medita."
	restraint_check = FALSE
	emote_type = EMOTE_VISIBLE

/mob/living/carbon/human/verb/emote_meditate()
	set name = "Meditate"
	set hidden = 1

	emote("meditate", intentional = TRUE)

/datum/emote/living/meditate/run_emote(mob/user, params, type_override, intentional, targeted)
	if(isliving(user))
		if(!COOLDOWN_FINISHED(user, schizohelp_cooldown))
			to_chat(user, span_warning("Debo esperar antes de meditar de nuevo..."))
			return
		INVOKE_ASYNC(src, PROC_REF(async_meditate), user)

/datum/emote/living/meditate/proc/async_meditate(mob/user)
	var/msg = input("Di tu meditación:", "Voces en tu cabeza.") as text|null
	if(msg)
		user.schizohelp(msg)

// ............... N ..................
/datum/emote/living/nod
	key = "nod"
	key_third_person = "nods"
	message = "asiente."
	message_param = "asiente a %t."
	emote_type = EMOTE_VISIBLE
/mob/living/carbon/human/verb/emote_nod()
	set name = "Nod"
	set category = "Emotes.Actions"
	emote("nod", intentional = TRUE)

// ............... O ..................

// ............... P ..................
/datum/emote/living/pinch
	key = "pinch"
	key_third_person = "pinches"
	message = ""
	message_param = "pellizca a %t."
	emote_type = EMOTE_VISIBLE
	restraint_check = TRUE

/datum/emote/living/pinch/adjacentaction(mob/user, mob/target)
	. = ..()
	if(!user || !target)
		return
	if(ishuman(target))
		var/mob/living/carbon/human/H = target
		H.flash_fullscreen("redflash1")

/mob/living/carbon/human/verb/emote_pinch()
	set name = "Pinch"
	set category = "Emotes.Actions"
	emote("pinch", intentional = TRUE, targeted = TRUE)

/datum/emote/living/point
	key = "point"
	key_third_person = "points"
	message = "apunta."
	message_param = "apunta a %t."
	restraint_check = TRUE
	cooldown = 1 SECONDS

/datum/emote/living/point/run_emote(mob/user, params, type_override, intentional, targeted)
	message_param = initial(message_param) // reset
	if(ishuman(user))
		var/mob/living/carbon/human/H = user
		if(H.usable_hands == 0)
			if(H.usable_legs != 0)
				message_param = "intenta apuntar hacia %t con su pierna, <span class='danger'>desplomandose</span> en el proceso!"
				H.Paralyze(20)
			else
				message_param = "<span class='danger'>bumps [user.p_their()] head on the ground</span> trying to motion towards %t."
				H.adjustOrganLoss(ORGAN_SLOT_BRAIN, 5)
	. = ..()

/datum/emote/living/pout
	key = "pout"
	key_third_person = "pouts"
	message = "pone cara molesta."
	emote_type = EMOTE_AUDIBLE

/datum/emote/living/preen
	key = "preen"
	key_third_person = "preens"
	message = "se acicala las plumas."
	emote_type = EMOTE_AUDIBLE
	COOLDOWN_DECLARE(time_to_next_preen)


/mob/living/carbon/human/verb/emote_preen()
	set hidden = TRUE
	set name = "Preen"
	set category = "Emotes.Actions"
	emote("preen", intentional = TRUE)

/datum/emote/living/preen/can_run_emote(mob/living/user, status_check = TRUE , intentional)
	. = ..()
	if(!isharpy(user))
		return FALSE

/datum/emote/living/preen/run_emote(mob/user, params, type_override, intentional, targeted)
	. = ..()
	if(ishuman(user))
		var/mob/living/carbon/human/H = user
		if(!isharpy(H))
			return
		var/time_left = COOLDOWN_TIMELEFT(src, time_to_next_preen)
		if(time_left)
			to_chat(H, span_warning("Acicalé mis plumas hace poco! No tendrá efecto en mi higiene."))
		else
			COOLDOWN_START(src, time_to_next_preen, HARPY_PREENING_COOLDOWN)
			H.set_hygiene(HYGIENE_LEVEL_NORMAL)
			if(prob(50))
				var/preened_feather = /obj/item/natural/feather
				new preened_feather(user.loc)



/datum/emote/living/scream/painscream
	key = "painscream"
	message = "grita del dolor!"
	emote_type = EMOTE_AUDIBLE
	only_forced_audio = TRUE

/datum/emote/living/scream/agony
	key = "agony"
	message = "grita en agonía!"
	emote_type = EMOTE_AUDIBLE
	only_forced_audio = TRUE

/datum/emote/living/scream/firescream
	key = "firescream"
	nomsg = TRUE
	emote_type = EMOTE_AUDIBLE
	only_forced_audio = TRUE

/datum/emote/living/aggro
	key = "aggro"
	emote_type = EMOTE_AUDIBLE
	nomsg = TRUE
	only_forced_audio = TRUE

/datum/emote/living/death
	key = "death"
	emote_type = EMOTE_AUDIBLE
	nomsg = TRUE
	only_forced_audio = TRUE
	stat_allowed = UNCONSCIOUS
	mob_type_ignore_stat_typecache = list(/mob/living)

/datum/emote/living/pain
	key = "pain"
	emote_type = EMOTE_AUDIBLE
	nomsg = TRUE
	only_forced_audio = TRUE

/datum/emote/living/paincrit
	key = "paincrit"
	emote_type = EMOTE_AUDIBLE
	nomsg = TRUE
	only_forced_audio = TRUE

/datum/emote/living/painmoan
	key = "painmoan"
	emote_type = EMOTE_AUDIBLE
	nomsg = TRUE
	only_forced_audio = TRUE

// ............... Q ..................

// ............... R ..................
/datum/emote/living/rage
	key = "rage"
	message = "da un grito enfurecido!"
	emote_type = EMOTE_AUDIBLE

/datum/emote/living/rage/run_emote(mob/user, params, type_override, intentional, targeted)
	. = ..()
	if(user.mind)
		record_round_statistic(STATS_WARCRIES)

/mob/living/carbon/human/verb/emote_rage()
	set name = "Rage"
	set category = "Emotes.Noises"
	emote("rage", intentional = TRUE)

// ............... S ..................
/datum/emote/living/spit
	key = "spit"
	key_third_person = "spits"
	message = "escupe en el suelo."
	message_param = "escupe a %t."
	emote_type = EMOTE_VISIBLE

/mob/living/carbon/human/verb/emote_spit()
	set name = "Spit"
	set category = "Emotes.Actions"
	emote("spit", intentional = TRUE, targeted = TRUE)

/datum/emote/living/spit/run_emote(mob/user, params, type_override, intentional, targeted)
	message_param = initial(message_param) // reset
	var/mob/living/carbon/human/H = user
	if(ishuman(user))
		if(H.mouth)
			if(H.mouth.spitoutmouth)
				H.visible_message("<span class='warning'>[H] escupe [H.mouth].</span>")
				H.dropItemToGround(H.mouth, silent = FALSE)
			return
	. = ..()

/datum/emote/living/spit/adjacentaction(mob/user, mob/target)
	. = ..()
	if(!user || !target)
		return
	if(isliving(target))
		if(user.gender == MALE)
			playsound(target, pick('sound/vo/male/gen/spit.ogg','sound/vo/male/gen/spit_floor.ogg'), 100, FALSE, -1)
		else
			playsound(target, pick('sound/vo/female/gen/spit.ogg', 'sound/vo/female/gen/spit_floor.ogg'), 100, FALSE, -1)
		SEND_SIGNAL(user, COMSIG_SPAT_ON, target)

/datum/emote/living/slap
	key = "slap"
	key_third_person = "slaps"
	message = ""
	message_param = "le da una cachetada a %t."
	emote_type = EMOTE_VISIBLE
	restraint_check = TRUE
	cooldown = 3 SECONDS // to prevent endless table slamming

/datum/emote/living/slap/adjacentaction(mob/user, mob/target)
	. = ..()
	if(!user || !target)
		return
	if(ishuman(target) && ishuman(user))
		var/mob/living/carbon/human/H = user
		var/mob/living/carbon/human/E = target
		if(H.zone_selected == BODY_ZONE_PRECISE_GROIN)
		// anti pedophile logging
			var/log_msg
			if(E.age == AGE_CHILD)
				log_msg = "[key_name(H)][ADMIN_FLW(H)] slapped [key_name(E)][ADMIN_FLW(E)] on the ass, a CHILD!"
				if(H.age == AGE_CHILD)
					log_msg += " As a child."
				else
					log_msg += " As an adult."
				message_admins(log_msg)

/datum/emote/living/slap/run_emote(mob/user, params, type_override, intentional, targeted)
	message_param = initial(message_param) // reset
	if(ishuman(user))
		var/mob/living/carbon/human/H = user
		if(H.zone_selected == BODY_ZONE_PRECISE_GROIN)
			message_param = "le da una nalgada a %t!"

	. = ..()

/mob/living/carbon/human/verb/emote_slap()
	set name = "Slap"
	set category = "Emotes.Actions"
	emote("slap", intentional = TRUE, targeted = TRUE)

/datum/emote/living/slap/adjacentaction(mob/user, mob/target)
	. = ..()
	if(!user || !target)
		return
	if(ishuman(target))
		var/mob/living/carbon/human/H = target
		H.flash_fullscreen("redflash3")
		H.AdjustSleeping(-50)
		playsound(target, pick('sound/foley/slap (1).ogg','sound/foley/slap (2).ogg'), 50, FALSE, -1)

/datum/emote/living/scream
	key = "scream"
	key_third_person = "screams"
	message = "grita!"
	message_muffled = "hace un grito ahogado."
	message_mime = "actúa un grito!"
	emote_type = EMOTE_AUDIBLE

/mob/living/carbon/human/verb/emote_scream()
	set name = "Scream"
	set category = "Emotes.Noises"
	emote("scream", intentional = TRUE)

/datum/emote/living/scream/can_run_emote(mob/living/user, status_check = TRUE , intentional)
	. = ..()
	if(. && iscarbon(user))
		var/mob/living/carbon/C = user
		if(intentional)
			if(!C.adjust_stamina(3)) // I guess this is here to reduce spamming? Or some other concept? Reduced from 10
				to_chat(C, "<span class='warning'>Intento gritar, pero mi voz no da abasto.</span>")
				. = FALSE

/datum/emote/living/scream/run_emote(mob/user, params, type_override, intentional, targeted)
	. = ..()
	if(user.mind)
		record_featured_stat(FEATURED_STATS_SCREAMERS, user)

/datum/emote/living/strain
	key = "strain"
	message = "se esfuerza demasiado!"
	emote_type = EMOTE_AUDIBLE
	only_forced_audio = TRUE
	show_runechat = FALSE

/datum/emote/living/scowl
	key = "scowl"
	key_third_person = "scowls"
	message = "hace una mueca incómoda."
	emote_type = EMOTE_AUDIBLE

/datum/emote/living/shakehead
	key = "shakehead"
	key_third_person = "shakeshead"
	message = "sacude la cabeza."
	emote_type = EMOTE_VISIBLE

/mob/living/carbon/human/verb/emote_shakehead()
	set name = "Shakehead"
	set category = "Emotes.Actions"
	emote("shakehead", intentional = TRUE)

/datum/emote/living/shiver
	key = "shiver"
	key_third_person = "shiver"
	message = "tiembla."
	emote_type = EMOTE_VISIBLE
/mob/living/carbon/human/verb/emote_shiver()
	set name = "Shiver"
	set category = "Emotes.Actions"
	emote("shiver", intentional = TRUE)

#define SHIVER_LOOP_DURATION (1 SECONDS)
/datum/emote/living/shiver/run_emote(mob/living/user, params, type_override, intentional, targeted)
	. = ..()

	animate(user, pixel_w = 1, time = 0.1 SECONDS, flags = ANIMATION_RELATIVE|ANIMATION_PARALLEL)
	for(var/i in 1 to SHIVER_LOOP_DURATION / (0.2 SECONDS)) //desired total duration divided by the iteration duration to give the necessary iteration count
		animate(pixel_w = -2, time = 0.1 SECONDS, flags = ANIMATION_RELATIVE|ANIMATION_CONTINUE)
		animate(pixel_w = 2, time = 0.1 SECONDS, flags = ANIMATION_RELATIVE|ANIMATION_CONTINUE)
	animate(pixel_w = -1, time = 0.1 SECONDS, flags = ANIMATION_RELATIVE)
#undef SHIVER_LOOP_DURATION

/datum/emote/living/sigh
	key = "sigh"
	key_third_person = "sighs"
	message = "suspira."
	message_muffled = "hace un suspiro ahogado."
	emote_type = EMOTE_AUDIBLE

/mob/living/carbon/human/verb/emote_sigh()
	set name = "Sigh"
	set category = "Emotes.Noises"
	emote("sigh", intentional = TRUE)

/datum/emote/living/snore
	key = "snore"
	key_third_person = "snores"
	message = "ronca."
	message_mime = "pretende roncar en silencio."
	emote_type = EMOTE_AUDIBLE
	stat_allowed = UNCONSCIOUS
	snd_range = -4

/datum/emote/living/snap
	key = "snap"
	key_third_person = "snaps their fingers."
	message = "chasquea los dedos."
	message_muffled = "chasquea los dedos."
	restraint_check = TRUE
	emote_type = EMOTE_VISIBLE

/mob/living/carbon/human/verb/emote_snap()
	set name = "Snap"
	set category = "Emotes.Noises"
	emote("snap", intentional = TRUE)

/datum/emote/living/snaptwice
	key = "snaptwice"
	key_third_person = "snaps their fingers twice."
	message = "chasquea los dedos dos veces."
	message_muffled = "chasquea los dedos dos veces."
	restraint_check = TRUE
	emote_type = EMOTE_VISIBLE

/mob/living/carbon/human/verb/emote_snaptwice()
	set name = "Snaptwice"
	set category = "Emotes.Noises"
	emote("snaptwice", intentional = TRUE)

/datum/emote/living/snapthrice
	key = "snapthrice"
	key_third_person = "snaps their fingers thrice."
	message = "chasquea los dedos tres veces."
	message_muffled = "chasquea los dedos tres veces."
	restraint_check = TRUE
	emote_type = EMOTE_VISIBLE

/mob/living/carbon/human/verb/emote_snapthrice()
	set name = "Snapthrice"
	set category = "Emotes.Noises"
	emote("snapthrice", intentional = TRUE)

/datum/emote/living/stare
	key = "stare"
	key_third_person = "stares"
	message = "se queda mirando fijamente a la nada."
	message_param = "mira fijamente a %t."

/datum/emote/living/strech
	key = "stretch"
	key_third_person = "stretches"
	message = "estira sus brazos."

/datum/emote/living/sulk
	key = "sulk"
	key_third_person = "sulks"
	message = "agacha la cabeza tristemente.."

/datum/emote/living/sway
	key = "sway"
	key_third_person = "sways"
	message = "se balancea de lado a lado."

/datum/emote/living/shh
	key = "shh"
	key_third_person = "shhs"
	message = "manda a callar."
	message_muffled = "hace un shh ahogado."
	emote_type = EMOTE_AUDIBLE

/mob/living/carbon/human/verb/emote_shh()
	set name = "Shh"
	set category = "Emotes.Noises"
	emote("shh", intentional = TRUE)

/datum/emote/living/smug
	key = "smug"
	key_third_person = "smugs"
	message = "sonríe pícaramente."

/datum/emote/living/sniff
	key = "sniff"
	key_third_person = "sniffs"
	message = "olisquea el aire."
	emote_type = EMOTE_AUDIBLE

/datum/emote/living/smile
	key = "smile"
	key_third_person = "smiles"
	message = "sonríe."
	emote_type = EMOTE_VISIBLE
/mob/living/carbon/human/verb/emote_smile()
	set name = "Smile"
	set category = "Emotes.Actions"
	emote("smile", intentional = TRUE)

/datum/emote/living/sneeze
	key = "sneeze"
	key_third_person = "sneezes"
	message = "estornuda."
	message_muffled = "hace un estornudo ahogado."
	emote_type = EMOTE_AUDIBLE

// ............... T ..................
/datum/emote/living/tremble
	key = "tremble"
	key_third_person = "trembles"
	message = "tiembla del miedo!"

/datum/emote/living/twitch
	key = "twitch"
	key_third_person = "twitches"
	message = "se sacude violentamente."

/datum/emote/living/twitch_s
	key = "twitch_s"
	message = "twitches."
	stat_allowed = UNCONSCIOUS
	mob_type_ignore_stat_typecache = list(/mob/living/carbon/human)

// ............... U ..................



// ............... W ..................
/datum/emote/living/wave
	key = "wave"
	key_third_person = "waves"
	message = "saluda con la mano."

/datum/emote/living/whisper
	key = "whisper"
	key_third_person = "whispers"
	message = "susurra."
	message_mime = "parece susurrar."
	emote_type = EMOTE_AUDIBLE

/datum/emote/living/whimper
	key = "whimper"
	key_third_person = "whimpers"
	message = "solloza."
	message_muffled = "hace un sollozo ahogado."
	message_mime = "parece adolorido."

/mob/living/carbon/human/verb/emote_whimper()
	set name = "Whimper"
	set category = "Emotes.Noises"
	emote("whimper", intentional = TRUE)

/datum/emote/living/whistle
	key = "whistle"
	key_third_person = "whistles"
	message = "silba."
	message_muffled = "hace un ruido ahogado."
	emote_type = EMOTE_AUDIBLE

/mob/living/carbon/human/verb/emote_whistle()
	set name = "Whistle"
	set category = "Emotes.Noises"
	emote("whistle", intentional = TRUE)

/datum/emote/living/wsmile
	key = "wsmile"
	key_third_person = "wsmiles"
	message = "sonríe débilmente."

// ............... Z ..................
/datum/emote/living/zombiemoan
	key = "zmoan"
	key_third_person = "moans"
	message = "gime."
	emote_type = EMOTE_AUDIBLE
	snd_vol = 80

/// The base chance for your yawn to propagate to someone else if they're on the same tile as you
#define YAWN_PROPAGATE_CHANCE_BASE 20
/// The amount the base chance to propagate yawns falls for each tile of distance
#define YAWN_PROPAGATE_CHANCE_DECAY 4

// ............... Y ..................
/datum/emote/living/yawn
	key = "yawn"
	key_third_person = "yawns"
	message = "bosteza."
	message_muffled = "hace un bostezo ahogado."
	emote_type = EMOTE_VISIBLE | EMOTE_AUDIBLE
	cooldown = 5 SECONDS

/datum/emote/living/yawn/run_emote(mob/user, params, type_override, intentional, targeted)
	. = ..()
	if(!iscarbon(user))
		return

	if(TIMER_COOLDOWN_FINISHED(user, COOLDOWN_YAWN_PROPAGATION))
		TIMER_COOLDOWN_START(user, COOLDOWN_YAWN_PROPAGATION, cooldown * 3)

	var/mob/living/carbon/carbon_user = user
	if(carbon_user.check_obscured_slots() & HIDEFACE)
		return // if your face is obscured, skip propagation

	var/propagation_distance = user.client ? 5 : 2 // mindless mobs are less able to spread yawns

	for(var/mob/living/iter_living in view(user, propagation_distance))
		if(IS_DEAD_OR_INCAP(iter_living) || TIMER_COOLDOWN_RUNNING(iter_living, COOLDOWN_YAWN_PROPAGATION))
			continue

		var/dist_between = get_dist(user, iter_living)
		var/recently_examined = FALSE // if you yawn just after someone looks at you, it forces them to yawn as well. Tradecraft!

		if(iter_living.client)
			var/examine_time = LAZYACCESS(iter_living.client?.recent_examines, user)
			if(examine_time && (world.time - examine_time < YAWN_PROPAGATION_EXAMINE_WINDOW))
				recently_examined = TRUE

		if(!recently_examined && !prob(YAWN_PROPAGATE_CHANCE_BASE - (YAWN_PROPAGATE_CHANCE_DECAY * dist_between)))
			continue

		var/yawn_delay = rand(0.2 SECONDS, 0.7 SECONDS) * dist_between
		addtimer(CALLBACK(src, PROC_REF(propagate_yawn), iter_living), yawn_delay)

/// This yawn has been triggered by someone else yawning specifically, likely after a delay. Check again if they don't have the yawned recently trait
/datum/emote/living/yawn/proc/propagate_yawn(mob/user)
	if(!istype(user) || TIMER_COOLDOWN_RUNNING(user, COOLDOWN_YAWN_PROPAGATION))
		return
	user.emote("yawn")

#undef YAWN_PROPAGATE_CHANCE_BASE
#undef YAWN_PROPAGATE_CHANCE_DECAY

/mob/living/carbon/human/verb/emote_yawn()
	set name = "Yawn"
	set category = "Emotes.Noises"
	emote("yawn", intentional = TRUE)
