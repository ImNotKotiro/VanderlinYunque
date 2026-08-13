/*
			< ATTENTION >
	If you need to add more map_adjustment, check 'map_adjustment_include.dm'
	These 'map_adjustment.dm' files shouldn't be included in 'dme'
*/

/datum/map_adjustment/tavella
	map_file_name = "tavella.dmm"
	blacklist = list(
		/datum/job/archivist,
		/datum/job/courtphys,
		/datum/job/minor_noble,
		/datum/job/sunlord,
		/datum/job/men_at_arms,
		/datum/job/dungeoneer,
		/datum/job/town_elder,
		/datum/job/tomb_warden,
		/datum/job/butler,
		/datum/job/servant,
		/datum/job/advclass/combat/swordmaster,
		/datum/job/advclass/mercenary/grenzelhoftzwei,
		/datum/job/advclass/mercenary/grenzelhofthalb,
		/datum/job/advclass/mercenary/grenzelhoftgun,
		/datum/job/advclass/pilgrim/rare/grenzelhoft,
		/datum/job/advclass/pilgrim/rare/preacher,
	)
	// Limited positions to ensure core roles are filled.
	slot_adjust = list(
		// Existing Tavella limits.
		/datum/job/prince = 1,
		/datum/job/royalknight = 1,
		/datum/job/monk = 3,
		/datum/job/undertaker = 1,
		/datum/job/templar = 3,
		/datum/job/orthodoxist = 1,
		/datum/job/blacksmith = 1,
		/datum/job/artificer = 1,
		/datum/job/farmer = 2,
		/datum/job/miner = 2,
		/datum/job/cook = 1,
		/datum/job/carpenter = 1,
		/datum/job/mason = 1,
		/datum/job/hunter = 1,
		/datum/job/fisher = 1,
		/datum/job/bard = 1,
		/datum/job/bandit = 2,
		/datum/job/courtagent = 1,
		/datum/job/guardsman = 5,
		/datum/job/vagrant = 5,
		/datum/job/bogwitch = 1,
		/datum/job/bog_apprentice = 1,
		/datum/job/tapster = 1,
		/datum/job/clinicapprentice = 1,
		/datum/job/squire = 1,
		/datum/job/bapprentice = 1,
		/datum/job/mageapprentice = 1,
		/datum/job/shophand = 1,
		/datum/job/grabber = 1,
		/datum/job/orphan = 3,
		/datum/job/churchling = 1,
		/datum/job/soilchild = 1,
		/datum/job/mercenary = 3,
		/datum/job/pilgrim = 10,
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
