/**
 * A chalk-scribable circle that renders gemstones down into innate magic points.
 *
 * Gems carrying an elemental attunement deepen the matching form, while unaligned
 * stones pay into the generic technique pool. Insight banks up between invocations
 * and only converts into a point once it crosses a threshold that climbs with every
 * point already drawn, so gems stay a sink rather than a faucet.
 */
/obj/effect/decal/cleanable/ritual_rune/arcyne/attunement
	name = "arcyne attunement circle"
	desc = "A ring of sigils drawn around empty sockets, meant to coax the elements sleeping inside gemstones out into the open."
	icon = 'icons/effects/96x96.dmi'
	icon_state = "empowerment"
	tier = 2
	runesize = 1
	SET_BASE_PIXEL(-32, -32)
	pixel_z = 0
	color = "#2FBEA8"
	invocation = "Ael'vorun geth'sarai en'myr!"
	invoker_name = "attunement circle"
	invoker_desc = "a circle that renders gemstones down into innate arcyne insight."
	can_be_scribed = TRUE
	scribe_damage = 8

	/// Gems currently resting on the circle, in placement order.
	var/list/obj/item/gem/staged_gems = list()
	/// TRUE while the ritual resolves. Blocks all interaction.
	var/animating = FALSE

/obj/effect/decal/cleanable/ritual_rune/arcyne/attunement/Destroy()
	release_gems()
	return ..()

/obj/effect/decal/cleanable/ritual_rune/arcyne/attunement/examine(mob/user)
	. = ..()
	if(!isliving(user) || GET_MOB_SKILL_VALUE(user, magictype) <= SKILL_LEVEL_NONE)
		return

	. += span_info("It cradles up to [ATTUNEMENT_CIRCLE_MAX_GEMS] gemstones. Elemental gems deepen the form they match, unaligned ones widen my techniques.")
	if(length(staged_gems))
		. += span_info("[length(staged_gems)] of the sockets are filled. An empty hand invokes the circle, a grab clears it.")

	var/datum/spell_mastery/mastery = user.mana_pool?.mastery
	if(!mastery)
		return
	if(mastery.attunement_points_drawn >= ATTUNEMENT_CIRCLE_MAX_POINTS)
		. += span_warning("I have already drawn every scrap of insight these circles will ever give me.")
		return

	. += span_notice("My next insight would take [mastery.get_attunement_threshold()] resonance.")
	for(var/key in mastery.attunement_insight)
		var/banked = mastery.get_banked_insight(key)
		if(banked <= 0)
			continue
		. += span_notice("Gathered [get_insight_label(key)] resonance: [banked].")

/obj/effect/decal/cleanable/ritual_rune/arcyne/attunement/attack_hand(mob/living/user)
	if(animating)
		to_chat(user, span_notice("The circle is already working..."))
		return
	if(user.get_active_held_item())
		return ..()
	if(!length(staged_gems))
		to_chat(user, span_hierophant_warning("The sockets are bare."))
		return
	try_invoke(user)

/obj/effect/decal/cleanable/ritual_rune/arcyne/attunement/attack_hand_secondary(mob/living/user, list/modifiers)
	if(animating)
		to_chat(user, span_notice("The circle is already working..."))
		return
	if(!length(staged_gems))
		return ..()
	release_gems()
	to_chat(user, span_cultsmall("The gemstones clatter free of the sigils."))
	playsound(src, 'sound/magic/glass.ogg', 40, TRUE)

/obj/effect/decal/cleanable/ritual_rune/arcyne/attunement/item_interaction(mob/living/user, obj/item/tool, list/modifiers)
	if(user.cmode)
		return NONE
	if(!istype(tool, /obj/item/gem))
		return NONE
	if(animating)
		to_chat(user, span_notice("The circle is already working..."))
		return ITEM_INTERACT_BLOCKING

	try_place_gem(user, tool)
	return ITEM_INTERACT_SUCCESS

/// Moves a held gem out of the user's hands and onto the next free socket.
/obj/effect/decal/cleanable/ritual_rune/arcyne/attunement/proc/try_place_gem(mob/living/user, obj/item/gem/gem)
	if((gem.item_flags & ABSTRACT) || HAS_TRAIT(gem, TRAIT_NODROP))
		return
	if(gem in staged_gems)
		to_chat(user, span_notice("That one is already on the circle."))
		return
	if(length(staged_gems) >= ATTUNEMENT_CIRCLE_MAX_GEMS)
		to_chat(user, span_hierophant_warning("Every socket is filled."))
		return
	if(!user.temporarilyRemoveItemFromInventory(gem))
		return

	gem.forceMove(get_turf(src))
	gem.anchored = TRUE
	staged_gems += gem
	RegisterSignal(gem, COMSIG_QDELETING, PROC_REF(on_gem_deleted))
	relayout_gems()
	playsound(src, 'sound/magic/glass.ogg', 60, TRUE)

	if(!get_gem_insight(gem))
		to_chat(user, span_warning("[gem] settles into a socket, but nothing inside it stirs."))
		return
	to_chat(user, span_cultsmall("[gem] settles into a socket and begins to hum."))

/obj/effect/decal/cleanable/ritual_rune/arcyne/attunement/proc/on_gem_deleted(obj/item/gem/source)
	SIGNAL_HANDLER
	staged_gems -= source

/// Spaces the staged gems evenly around the circle. A lone gem sits in the middle.
/obj/effect/decal/cleanable/ritual_rune/arcyne/attunement/proc/relayout_gems()
	var/count = length(staged_gems)
	for(var/i in 1 to count)
		var/obj/item/gem/gem = staged_gems[i]
		if(QDELETED(gem))
			continue
		var/target_x = 0
		var/target_y = 0
		if(count > 1)
			var/angle = ((360 / count) * (i - 1)) - 90
			target_x = round(26 * cos(angle))
			target_y = round(26 * sin(angle))
		animate(gem, pixel_x = target_x, pixel_y = target_y, time = 0.5 SECONDS, flags = ANIMATION_END_NOW)

/// Unanchors every staged gem and drops it back onto the turf.
/obj/effect/decal/cleanable/ritual_rune/arcyne/attunement/proc/release_gems()
	for(var/obj/item/gem/gem as anything in staged_gems)
		if(QDELETED(gem))
			continue
		UnregisterSignal(gem, COMSIG_QDELETING)
		gem.anchored = FALSE
		animate(gem, pixel_x = 0, pixel_y = 0, time = 0.5 SECONDS, flags = ANIMATION_END_NOW)
	staged_gems.Cut()

/// Raw insight a gem is worth, before the invoker's skill is applied.
/obj/effect/decal/cleanable/ritual_rune/arcyne/attunement/proc/get_gem_insight(obj/item/gem/gem)
	if(QDELETED(gem) || !gem.attunement_insight)
		return 0

	var/quality_multiplier
	switch(gem.quality)
		if(GEM_CHIPPED)
			quality_multiplier = 0.6
		if(GEM_FLAWED)
			quality_multiplier = 0.8
		if(GEM_FLAWLESS)
			quality_multiplier = 1.4
		if(GEM_PERFECT)
			quality_multiplier = 2
		else
			quality_multiplier = 1

	if(gem.is_cut)
		quality_multiplier *= 1.25

	return round(gem.attunement_insight * quality_multiplier)

/// Which bucket a gem's insight pays into - a form, or the formless technique pool.
/obj/effect/decal/cleanable/ritual_rune/arcyne/attunement/proc/get_gem_insight_key(obj/item/gem/gem)
	if(!gem.attuned)
		return ATTUNEMENT_INSIGHT_TECHNIQUE
	return GLOB.attunement_to_form[gem.attuned] || ATTUNEMENT_INSIGHT_TECHNIQUE

/obj/effect/decal/cleanable/ritual_rune/arcyne/attunement/proc/get_insight_label(key)
	return (key == ATTUNEMENT_INSIGHT_TECHNIQUE) ? "formless" : LOWER_TEXT(key)

/obj/effect/decal/cleanable/ritual_rune/arcyne/attunement/proc/try_invoke(mob/living/user)
	if(rune_in_use)
		to_chat(user, span_notice("The circle is already active."))
		return

	var/skill_level = GET_MOB_SKILL_VALUE(user, magictype)
	if(skill_level < SKILL_LEVEL_APPRENTICE)
		to_chat(user, span_warning("These sigils ask for a steadier grasp of the arcyne than I have."))
		return
	if(!user.mana_pool)
		to_chat(user, span_warning("Nothing within me answers the circle."))
		return

	var/datum/spell_mastery/mastery = user.mana_pool.get_mastery()
	if(mastery.attunement_points_drawn >= ATTUNEMENT_CIRCLE_MAX_POINTS)
		to_chat(user, span_hierophant_warning("My mind is already as wide as these circles can pry it."))
		return

	// A finer grasp of the arcyne coaxes more out of the same stones.
	var/skill_multiplier = 1 + (skill_level / 100)
	var/list/insight_by_key = list()
	var/total_insight = 0
	for(var/obj/item/gem/gem as anything in staged_gems)
		var/value = round(get_gem_insight(gem) * skill_multiplier)
		if(value <= 0)
			continue
		var/key = get_gem_insight_key(gem)
		insight_by_key[key] = nulltozero(insight_by_key[key]) + value
		total_insight += value

	if(!total_insight)
		to_chat(user, span_hierophant_warning("Nothing on the sigils holds any true resonance."))
		return

	var/mana_cost = total_insight * ATTUNEMENT_CIRCLE_MANA_PER_INSIGHT
	if(user.mana_pool.amount < mana_cost)
		to_chat(user, span_hierophant_warning("Prying this much loose would take [mana_cost] mana, and I do not hold it."))
		return

	rune_in_use = TRUE
	animating = TRUE
	user.mana_pool.adjust_mana(-mana_cost)

	user.say(invocation, language = /datum/language/common, ignore_spam = TRUE, forced = "cult invocation")
	playsound(src, 'sound/magic/cosmic_expansion.ogg', 60, TRUE)
	SpinAnimation(speed = 1.5 SECONDS, loops = 1, clockwise = TRUE, segments = 6, parallel = TRUE)

	INVOKE_ASYNC(src, PROC_REF(run_attunement_animation), user, insight_by_key)

/obj/effect/decal/cleanable/ritual_rune/arcyne/attunement/proc/run_attunement_animation(mob/living/user, list/insight_by_key)
	var/list/consumed = staged_gems.Copy()
	staged_gems.Cut()

	for(var/obj/item/gem/gem as anything in consumed)
		if(QDELETED(gem))
			continue
		UnregisterSignal(gem, COMSIG_QDELETING)
		animate(gem,
			pixel_x = 0, pixel_y = 0,
			alpha = 0,
			transform = matrix() * 0.2,
			time = 1.5 SECONDS,
			flags = ANIMATION_END_NOW
		)
	sleep(1.5 SECONDS)

	for(var/obj/item/gem/gem as anything in consumed)
		if(!QDELETED(gem))
			qdel(gem)

	// The circle can be scrubbed away mid-ritual, but the mana was already spent.
	if(!QDELETED(src))
		playsound(src, 'sound/magic/blink.ogg', 80, TRUE)
		animating = FALSE
		rune_in_use = FALSE
		do_invoke_glow()

	award_insight(user, insight_by_key)

/obj/effect/decal/cleanable/ritual_rune/arcyne/attunement/proc/award_insight(mob/living/user, list/insight_by_key)
	if(QDELETED(user) || !user.mana_pool)
		return
	var/datum/spell_mastery/mastery = user.mana_pool.get_mastery()
	if(!mastery)
		return

	var/points_gained = 0
	var/total_insight = 0
	for(var/key in insight_by_key)
		var/amount = insight_by_key[key]
		total_insight += amount
		var/gained = mastery.absorb_attunement_insight(user, key, amount)
		points_gained += gained

		if(!gained)
			to_chat(user, span_notice("[amount] points of [get_insight_label(key)] resonance settle into me - [mastery.get_banked_insight(key)] of [mastery.get_attunement_threshold()] gathered."))
			continue
		if(key == ATTUNEMENT_INSIGHT_TECHNIQUE)
			to_chat(user, span_nicegreen("The formless resonance burns itself into me. I can feel [gained] new technique\s waiting to be shaped."))
		else
			to_chat(user, span_nicegreen("The resonance burns itself into me. My innate command of [key] deepens."))

	if(points_gained)
		playsound(user, 'sound/magic/charged.ogg', 70, TRUE)
		if(mastery.attunement_points_drawn >= ATTUNEMENT_CIRCLE_MAX_POINTS)
			to_chat(user, span_boldwarning("Something in me closes over. No circle will pry my mind wider than this."))

	user.add_sleep_experience(magictype, round(total_insight / 2), FALSE)
