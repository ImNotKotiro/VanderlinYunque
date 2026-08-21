/datum/round_event_control/antagonist/solo/lich
	name = ROLE_LICH
	tags = list(
		TAG_ZIZO,
		TAG_COMBAT,
		TAG_HAUNTED,
		TAG_VILLAIN,
	)
	roundstart = TRUE
	antag_flag = ROLE_LICH
	shared_occurence_type = SHARED_HIGH_THREAT

	base_antags = 1
	maximum_antags = 2
	min_players = 15
	denominator = 20

	earliest_start = 0 SECONDS
	weight = 12

	typepath = /datum/round_event/antagonist/solo/lich
	antag_datum = /datum/antagonist/lich

	restricted_roles = list(
		/datum/job/lord,
		/datum/job/consort,
		/datum/job/priest,
		/datum/job/hand,
		/datum/job/captain,
		/datum/job/prince,
		/datum/job/inquisitor,
		/datum/job/absolver,
		/datum/job/orthodoxist,
		/datum/job/adept,
		/datum/job/royalknight,
		/datum/job/templar,
		/datum/job/gmtemplar,
		/datum/job/advclass/combat/assassin,
		/datum/job/tomb_warden,
		/datum/job/forestwarden,
		/datum/job/forestenforcer,
		/datum/job/forestpreacher,
		/datum/job/bogwitch,
		/datum/job/bog_apprentice,
		/datum/job/admin,
	)


/datum/round_event_control/antagonist/solo/lich/valid_for_map()
	if(SSmapping.config.map_name != "Voyage")
		return TRUE
	return FALSE

/datum/round_event/antagonist/solo/lich
