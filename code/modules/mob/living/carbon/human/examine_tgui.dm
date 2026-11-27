/datum/examine_panel
	/// Human being examined.
	var/mob/living/carbon/human/holder
	/// Mob viewing the examine panel.
	var/mob/viewing
	/// Preferences being previewed from the character creation screen.
	var/datum/preferences/pref

/datum/examine_panel/New(mob/living/carbon/human/holder_mob)
	if(holder_mob)
		holder = holder_mob

/datum/examine_panel/Destroy(force)
	holder = null
	pref = null
	viewing = null
	return ..()

/datum/examine_panel/ui_state(mob/user)
	return GLOB.always_state

/datum/examine_panel/ui_interact(mob/user, datum/tgui/ui)
	ui = SStgui.try_update_ui(user, src, ui)
	if(!ui)
		ui = new(user, src, "ExaminePanel")
		ui.open()

/datum/examine_panel/ui_static_data(mob/user)
	var/character_name = "Unknown"
	var/headshot = ""
	var/flavor_text = ""
	var/ooc_notes = ""
	var/ooc_extra_link = ""
	var/descriptor_text = ""

	if(holder)
		character_name = holder.real_name || holder.name
		headshot = holder.headshot_link || ""
		flavor_text = holder.flavortext_display || ""
		ooc_notes = holder.ooc_notes_display || ""
		ooc_extra_link = holder.ooc_extra_link || ""
		var/list/holder_descriptors = holder.get_mob_descriptors(FALSE, viewing)
		if(length(holder_descriptors))
			descriptor_text = build_cool_description(holder_descriptors, holder).Join("<br>")
	else if(pref)
		character_name = pref.read_preference(/datum/preference/text/real_name) || "Unknown"
		headshot = pref.read_preference(/datum/preference/text/headshot_link) || ""
		flavor_text = pref.read_preference(/datum/preference/text/flavortext_display) || ""
		ooc_notes = pref.read_preference(/datum/preference/text/ooc_notes_display) || ""
		ooc_extra_link = pref.read_preference(/datum/preference/text/ooc_extra_link) || ""
		descriptor_text = pref.get_examine_descriptor_text()

	return list(
		"character_name" = character_name,
		"headshot" = headshot,
		"flavor_text" = flavor_text,
		"ooc_notes" = ooc_notes,
		"ooc_extra_link" = ooc_extra_link,
		"descriptor_text" = descriptor_text,
	)


/datum/preferences/proc/get_examine_descriptor_text()
	var/height_text
	var/body_text
	var/age_text
	var/gender_text
	var/stature_text
	var/face_text
	var/expression_text
	var/skin_text
	var/voice_text
	var/list/prominent_text = list()

	var/gender = read_preference(/datum/preference/choiced/gender)
	switch(gender)
		if(MALE)
			gender_text = "man"
		if(FEMALE)
			gender_text = "woman"
		else
			gender_text = "person"

	var/age = read_preference(/datum/preference/choiced/age)
	switch(age)
		if(AGE_OLD)
			age_text = "old"
		if(AGE_MIDDLEAGED)
			age_text = "middle-aged"
		if(AGE_CHILD)
			age_text = "young"
		else
			age_text = "adult"

	for(var/datum/descriptor_entry/entry as anything in descriptor_entries)
		var/datum/mob_descriptor/descriptor = MOB_DESCRIPTOR(entry.descriptor_type)
		if(!descriptor)
			continue

		switch(entry.descriptor_choice_type)
			if(/datum/descriptor_choice/height)
				height_text = descriptor.describe
			if(/datum/descriptor_choice/body)
				body_text = descriptor.describe
			if(/datum/descriptor_choice/stature)
				stature_text = descriptor.describe
				if(entry.descriptor_type == /datum/mob_descriptor/stature/man || entry.descriptor_type == /datum/mob_descriptor/stature/gentleman)
					stature_text = (gender == MALE) ? (entry.descriptor_type == /datum/mob_descriptor/stature/man ? "man" : "gentleman") : (entry.descriptor_type == /datum/mob_descriptor/stature/man ? "woman" : "gentlewoman")
				else if(entry.descriptor_type == /datum/mob_descriptor/stature/scoundrel)
					stature_text = (gender == MALE) ? "scoundrel" : "wench"
			if(/datum/descriptor_choice/face)
				face_text = descriptor.describe
			if(/datum/descriptor_choice/face_exp)
				expression_text = descriptor.describe
			if(/datum/descriptor_choice/skin)
				skin_text = descriptor.describe
			if(/datum/descriptor_choice/voice)
				voice_text = descriptor.describe
			if(/datum/descriptor_choice/prominent_one, /datum/descriptor_choice/prominent_two, /datum/descriptor_choice/prominent_three, /datum/descriptor_choice/prominent_four, /datum/descriptor_choice/prominent_one_wild, /datum/descriptor_choice/prominent_two_wild, /datum/descriptor_choice/prominent_three_wild, /datum/descriptor_choice/prominent_four_wild)
				if(entry.descriptor_type == /datum/mob_descriptor/prominent/none)
					continue
				if(entry.descriptor_type == /datum/mob_descriptor/prominent/custom/one || entry.descriptor_type == /datum/mob_descriptor/prominent/custom/two)
					var/custom_index = entry.descriptor_type == /datum/mob_descriptor/prominent/custom/one ? 1 : 2
					if(length(custom_descriptors) >= custom_index)
						var/datum/custom_descriptor_entry/custom_entry = custom_descriptors[custom_index]
						if(length(custom_entry.content_text))
							prominent_text += custom_entry.content_text
				else
					prominent_text += descriptor.describe

	if(!height_text)
		height_text = "moderate"
	if(!body_text)
		body_text = "average"
	if(!age_text)
		age_text = "adult"
	if(!gender_text)
		gender_text = "person"

	var/text = "You see [descriptor_article(height_text)] [height_text], [body_text] [age_text] [gender_text]."
	if(face_text)
		text += " Their face is [face_text]"
	if(expression_text)
		text += ", with a [expression_text] resting expression"
	if(face_text || expression_text)
		text += "."
	if(skin_text)
		text += " They have [skin_text]"
	if(voice_text)
		text += " and speak with [descriptor_article(voice_text)] [voice_text] voice"
	if(skin_text || voice_text)
		text += "."
	if(stature_text)
		text += " They carry themselves as a [stature_text]."
	if(length(prominent_text))
		var/prominent_string = ""
		for(var/i in 1 to length(prominent_text))
			if(i > 1)
				prominent_string += (i == length(prominent_text) ? " and " : ", ")
			prominent_string += prominent_text[i]
		text += " Notable features include [prominent_string]."
	return capitalize(text)

/datum/preferences/proc/descriptor_article(text)
	if(!length(text))
		return "a"
	var/first = lowertext(copytext(text, 1, 2))
	if(first in list("a", "e", "i", "o", "u"))
		return "an"
	return "a"


/datum/examine_panel/ui_data(mob/user)
	return list()

/datum/examine_panel/ui_close()
	QDEL_NULL(src)
