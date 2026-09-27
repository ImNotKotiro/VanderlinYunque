/mob/living/simple_animal/hostile/gnome_homunculus
	name = "gnome homunculus"
	desc = "A small, industrious magical construct that resembles a tiny gnome. Its eyes glow with alchemical energy, and it seems eager to help with menial tasks."
	icon = 'icons/mob/gnome2.dmi' // You'll need appropriate sprites
	icon_state = "gnome"
	icon_living = "gnome"
	icon_dead = "gnome_dead"

	pass_flags = PASSMOB

	animal_type = /datum/blood_type/putrid

	maxHealth = 50
	health = 50
	harm_intent_damage = 8
	obj_damage = 10
	melee_damage_lower = 5
	melee_damage_upper = 8
	attack_verb_continuous = "punches"
	attack_verb_simple = "punch"
	density = FALSE

	response_help_continuous = "pets"
	response_help_simple = "pet"
	response_disarm_continuous = "gently pushes aside"
	response_disarm_simple = "gently push aside"
	response_harm_continuous = "kicks"
	response_harm_simple = "kick"

	speed = 1
	move_to_delay = 3

	faction = list(FACTION_NEUTRAL)

	gold_core_spawnable = FRIENDLY_SPAWN

	ai_controller = /datum/ai_controller/basic_controller/gnome_homunculus

	var/list/waypoints = list()
	var/max_carry_size = WEIGHT_CLASS_NORMAL
	var/list/item_filters = list()

	var/hat_state

	var/static/list/pet_commands = list(
		/datum/pet_command/follow/gnome,
		/datum/pet_command/idle/gnome,
		/datum/pet_command/fetch/gnome,
		/datum/pet_command/free/gnome,
	)

	var/list/gnome_friendship_levels = list(
		"enemy" = -50,
		"dislike" = -10,
		"neutral" = 0,
		"like" = 25,
		"friend" = 50,
		"best_friend" = 100
	)

	// Learned words from friends (stored as word = times_heard)
	var/list/learned_words = list()

	// Pending death messages to deliver (dying_gnome_name = list("message" = text, "friends" = list))
	var/list/pending_death_messages = list()

	// Track delivered death messages to avoid repeats (message_key = list(delivered_to))
	var/list/delivered_death_messages = list()


/mob/living/simple_animal/hostile/gnome_homunculus/Initialize()
	AddComponent(/datum/component/obeys_commands, pet_commands) // here due to signal overridings from pet commands
	AddComponent(/datum/component/emotion_buffer)
	AddComponent(/datum/component/friendship_container, gnome_friendship_levels, "friend", FALSE)
	AddComponent(/datum/component/scared_of_item, 5)
	AddComponent(/datum/component/hovering_information, /datum/hover_data/gnome_status)
	. = ..()

	setup_emotional_responses()

/mob/living/simple_animal/hostile/gnome_homunculus/update_overlays()
	. = ..()
	if(hat_state)
		. += mutable_appearance(icon, hat_state)

/mob/living/simple_animal/hostile/gnome_homunculus/proc/item_matches_filter(obj/item/target_item)
	if(!length(item_filters))
		return TRUE
	return (is_type_in_list(target_item, item_filters))


/mob/living/simple_animal/hostile/gnome_homunculus/proc/setup_emotional_responses()
	RegisterSignal(src, COMSIG_LIVING_BEFRIENDED, PROC_REF(on_befriended))
	RegisterSignal(src, COMSIG_LIVING_UNFRIENDED, PROC_REF(on_unfriended))
	RegisterSignal(src, COMSIG_ATOM_ATTACKBY, PROC_REF(on_attacked))
	RegisterSignal(src, COMSIG_LIVING_DEATH, PROC_REF(on_death))


/mob/living/simple_animal/hostile/gnome_homunculus/proc/on_befriended(datum/source, mob/living/new_friend)
	SEND_SIGNAL(src, COMSIG_EMOTION_STORE, new_friend, EMOTION_HAPPY, "es nuevo amigo!", 5)
	// Gnomes get excited when they make friends
	say(pick("*tararea feliz", "*hace un pequeño baile", "Amigo! Amigo!"))

/mob/living/simple_animal/hostile/gnome_homunculus/proc/on_unfriended(datum/source, mob/living/former_friend)
	SEND_SIGNAL(src, COMSIG_EMOTION_STORE, former_friend, EMOTION_SAD, "ya no amigo...", -5)
	say(pick("*solloza tristemente", "*se ve deprimido", "¿Porqué amigo irse?"))

/mob/living/simple_animal/hostile/gnome_homunculus/proc/on_attacked(datum/source, obj/item/weapon, mob/living/attacker)
	if(!attacker)
		return

	// Check if this is a friend attacking us - extra sad!
	var/friendship_check = SEND_SIGNAL(src, COMSIG_FRIENDSHIP_CHECK_LEVEL, attacker, "friend")
	if(friendship_check)
		SEND_SIGNAL(src, COMSIG_EMOTION_STORE, attacker, EMOTION_SAD, "hacer daño!", -10)
		say(pick("Porque golpear amigo?!", "*llora", "Amigo... Porque?!"))
	else
		SEND_SIGNAL(src, COMSIG_EMOTION_STORE, attacker, EMOTION_ANGER, "ataco con [weapon]!", -3)
		say(pick("*gruñe enojado", "Auch! Malo!", "*hace un bufido"))

/mob/living/simple_animal/hostile/gnome_homunculus/proc/on_death(datum/source)
	SEND_SIGNAL(src, COMSIG_EMOTION_STORE, null, EMOTION_SCARED, "muere!", 0)

	// Collect friends before dying - PROPERLY using befriended_refs
	var/list/my_friends = list()

	for(var/datum/friend as anything in ai_controller?.blackboard?[BB_FRIENDS_LIST])
		if(QDELETED(friend))
			continue
		my_friends |= friend

	// Create death message for nearby gnomes to remember
	var/death_message = pick(
		"amo a sus amigos muchísimo",\
		"dijo que sus amigos eran lo mejor",\
		"fue feliz junto a sus amigos",\
		"extrañara a sus amigos",\
		"queria que sus amigos fueran felices",\
	)

	// Tell nearby gnomes about our death message
	for(var/mob/living/simple_animal/hostile/gnome_homunculus/nearby_gnome in range(10, src))
		if(nearby_gnome == src || nearby_gnome.stat != CONSCIOUS)
			continue

		// Store this death message for later delivery
		nearby_gnome.pending_death_messages[name] = list(
			"message" = death_message,
			"friends" = my_friends.Copy()
		)

		// The witnessing gnome becomes sad
		SEND_SIGNAL(nearby_gnome, COMSIG_EMOTION_STORE, src, EMOTION_SAD, "ver amigo [name] morir...", -3)
		nearby_gnome.say(pick("*cries for [name]*", "[name] no!", "*whimpers sadly*"))

	say(pick("*canta una canción de luto", "Decir amigos... Querer gnomo...", "*solloza", "Amigos... Recordar gnomo..."))

/mob/living/simple_animal/hostile/gnome_homunculus/proc/hat()
	hat_state = pick("spike_helm", "fungi_helm", "fungi_helm_bog", "gnome_helm", null)
	update_appearance(UPDATE_OVERLAYS)

/mob/living/simple_animal/hostile/gnome_homunculus/hitby(atom/movable/AM, skipcatch, hitpush, blocked, datum/thrownthing/throwingdatum, damage_type)
	. = ..()
	SEND_SIGNAL(src, COMSIG_EMOTION_STORE, throwingdatum?.thrower, EMOTION_SCARED, "[throwingdatum.thrower] lanzarme cosa!", 0)

/mob/living/simple_animal/hostile/gnome_homunculus/attackby(obj/item/item, mob/living/user, list/modifiers)
	// Check what kind of item interaction this is
	if(istype(item, /obj/item/reagent_containers/food))
		handle_food_gift(item, user)
		return
	if(istype(item, /obj/item/grown/log)) //idk man we don't got toys
		handle_toy_interaction(item, user)
		return

	return ..()

/mob/living/simple_animal/hostile/gnome_homunculus/proc/handle_food_gift(obj/item/reagent_containers/food/food_item, mob/living/giver)
	SEND_SIGNAL(src, COMSIG_FRIENDSHIP_CHANGE, giver, 5)
	SEND_SIGNAL(src, COMSIG_EMOTION_STORE, giver, EMOTION_HAPPY, "darme delicioso [food_item]!", 3)

	say(pick("Comida!", "Yum!", "Rico!", "*silbido alegre"))

	qdel(food_item)
	adjustBruteLoss(-5)

/mob/living/simple_animal/hostile/gnome_homunculus/proc/handle_toy_interaction(obj/item/toy/toy_item, mob/living/player)
	SEND_SIGNAL(src, COMSIG_FRIENDSHIP_CHANGE, player, 2)
	SEND_SIGNAL(src, COMSIG_EMOTION_STORE, player, EMOTION_FUNNY, "jugar conmigo con [toy_item]!", 2)

	say(pick("*se rie", "Gustar!", "*salta", "Jugar!"))

