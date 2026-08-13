/*
			< ATTENTION >
	If you need to add more map_adjustment, check 'map_adjustment_include.dm'
	These 'map_adjustment.dm' files shouldn't be included in 'dme'
*/

#define POINTY_EARS list(\
	SPEC_ID_ELF,\
	SPEC_ID_HALF_ELF\
)

/datum/map_adjustment/blueveil
	map_file_name = "blueveil.dmm"
	species_adjust = list(
		/datum/job/lord = POINTY_EARS,
		/datum/job/consort = POINTY_EARS,
		/datum/job/prince = POINTY_EARS,
		/datum/job/hand = POINTY_EARS,
	)


	blacklist = list(
	)
	// Limited positions to ensure core roles are filled.
	slot_adjust = list(
		/datum/job/prince = 1,
		/datum/job/captain = 1,
		/datum/job/steward = 1,
		/datum/job/magician = 1,
		/datum/job/archivist = 1,
		/datum/job/courtphys = 1,
		/datum/job/minor_noble = 1,
		/datum/job/royalknight = 2,
		/datum/job/guardsman = 8,
		/datum/job/men_at_arms = 8,
		/datum/job/town_elder = 1,
		/datum/job/tomb_warden = 1,
		/datum/job/priest = 1,
		/datum/job/gmtemplar = 1,
		/datum/job/monk = 3,
		/datum/job/undertaker = 1,
		/datum/job/templar = 3,
		/datum/job/orthodoxist = 1,
		/datum/job/innkeep = 1,
		/datum/job/blacksmith = 1,
		/datum/job/tailor = 1,
		/datum/job/alchemist = 1,
		/datum/job/artificer = 1,
		/datum/job/butler = 1,
		/datum/job/farmer = 2,
		/datum/job/miner = -2,
		/datum/job/cook = 1,
		/datum/job/carpenter = 1,
		/datum/job/mason = 1,
		/datum/job/jester = 1,
		/datum/job/hunter = 2,
		/datum/job/fisher = 2,
		/datum/job/bard = 2,
		/datum/job/bapprentice = 1,
		/datum/job/servant = 2,
		/datum/job/clinicapprentice = 2,
		/datum/job/innkeep_son = 1,
		/datum/job/orphan = 3,
		/datum/job/merchant = 1,
		/datum/job/shophand = 1,
		/datum/job/grabber = 1,
		/datum/job/adventurer = 1,
		/datum/job/bogwitch = 1,
		/datum/job/bog_apprentice = 1,
		/datum/job/adept = 1,
	)

	ages_adjust = list(
		/datum/job/bogwitch = list(AGE_ADULT, AGE_MIDDLEAGED, AGE_OLD, AGE_IMMORTAL),
		/datum/job/forestguard = list(AGE_ADULT, AGE_MIDDLEAGED, AGE_OLD, AGE_IMMORTAL),
		/datum/job/forestsupport = list(AGE_ADULT, AGE_MIDDLEAGED, AGE_OLD, AGE_IMMORTAL),
		/datum/job/forestenforcer = list(AGE_ADULT, AGE_MIDDLEAGED, AGE_OLD, AGE_IMMORTAL),
		/datum/job/forestpreacher = list(AGE_ADULT, AGE_MIDDLEAGED, AGE_OLD, AGE_IMMORTAL),
		/datum/job/forestwarden = list(AGE_ADULT, AGE_MIDDLEAGED, AGE_OLD, AGE_IMMORTAL),
		/datum/job/tomb_warden = list(AGE_ADULT, AGE_MIDDLEAGED, AGE_OLD, AGE_IMMORTAL),
	)
	migrant_blacklist = list(
		/datum/migrant_wave/grenzelhoft_visit,
	)

#undef POINTY_EARS
