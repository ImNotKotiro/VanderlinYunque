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
		/datum/job/hand = POINTY_EARS,
	)


	blacklist = list(
		/datum/job/adept,
	)
	// Limited positions to ensure core roles are filled.
	slot_adjust = list(
		/datum/job/absolver = 1,
		/datum/job/adept = 1,
		/datum/job/adventurer = 3,
		/datum/job/alchemist = 1,
		/datum/job/apothecary = 1,
		/datum/job/archivist = 1,
		/datum/job/artificer = 1,
		/datum/job/bard = 2,
		/datum/job/butcher = 1,
		/datum/job/blacksmith = 1,
		/datum/job/bogwitch = 1,
		/datum/job/bog_apprentice = 2,
		/datum/job/butler = 1,
		/datum/job/captain = 1,
		/datum/job/carpenter = 1,
		/datum/job/cheesemaker = 1,
		/datum/job/churchling = 1,
		/datum/job/clinicapprentice = 1,
		/datum/job/consort = 1,
		/datum/job/cook = 1,
		/datum/job/courtagent = 1,
		/datum/job/courtphys = 1,
		/datum/job/dungeoneer = 1,
		/datum/job/farmer = 1,
		/datum/job/feldsher = 1,
		/datum/job/fisher = 1,
		/datum/job/forestenforcer = 1,
		/datum/job/forestguard = 2,
		/datum/job/forestpreacher = 1,
		/datum/job/forestsupport = 2,
		/datum/job/forestwarden = 1,
		/datum/job/gatemaster = 1,
		/datum/job/gmtemplar = 1,
		/datum/job/grabber = 1,
		/datum/job/undertaker = 1,
		/datum/job/guardsman = 3,
		/datum/job/hand = 1,
		/datum/job/hunter = 1,
		/datum/job/innkeep = 1,
		/datum/job/innkeep_son = 1,
		/datum/job/jester = 1,
		/datum/job/lieutenant = 1,
		/datum/job/lord = 1,
		/datum/job/persistence/woodsman = 1,
		/datum/job/magician = 1,
		/datum/job/royalknight = 1,
		/datum/job/matron = 1,
		/datum/job/mercenary = 3,
		/datum/job/merchant = 1,
		/datum/job/miner = 1,
		/datum/job/minor_noble = 2,
		/datum/job/monk = 3,
		/datum/job/orphan = 3,
		/datum/job/orthodoxist = 2,
		/datum/job/priest = 1,
		/datum/job/prince = 2,
		/datum/job/prisoner = 1,
		/datum/job/inquisitor = 1,
		/datum/job/bapprentice = 1,
		/datum/job/servant = 2,
		/datum/job/shophand = 1,
		/datum/job/squire = 1,
		/datum/job/steward = 1,
		/datum/job/sweeper = 1,
		/datum/job/tailor = 1,
		/datum/job/tapster = 1,
		/datum/job/templar = 3,
		/datum/job/tomb_warden = 1,
		/datum/job/vagrant = 3,
		/datum/job/villager = 2,
		/datum/job/mageapprentice = 2,
		/datum/job/men_at_arms = 3,
		/datum/job/town_elder = 1,
	)

	ages_adjust = list(
		/datum/job/bogwitch = list(AGE_ADULT, AGE_MIDDLEAGED, AGE_OLD, AGE_IMMORTAL),
		/datum/job/forestguard = list(AGE_ADULT, AGE_MIDDLEAGED, AGE_OLD, AGE_IMMORTAL),
		/datum/job/forestsupport = list(AGE_CHILD, AGE_ADULT, AGE_MIDDLEAGED, AGE_OLD, AGE_IMMORTAL),
		/datum/job/forestenforcer = list(AGE_ADULT, AGE_MIDDLEAGED, AGE_OLD, AGE_IMMORTAL),
		/datum/job/forestpreacher = list(AGE_ADULT, AGE_MIDDLEAGED, AGE_OLD, AGE_IMMORTAL),
		/datum/job/forestwarden = list(AGE_ADULT, AGE_MIDDLEAGED, AGE_OLD, AGE_IMMORTAL),
		/datum/job/tomb_warden = list(AGE_ADULT, AGE_MIDDLEAGED, AGE_OLD, AGE_IMMORTAL),
	)
	migrant_blacklist = list(
		/datum/migrant_wave/grenzelhoft_visit,
	)

#undef POINTY_EARS
