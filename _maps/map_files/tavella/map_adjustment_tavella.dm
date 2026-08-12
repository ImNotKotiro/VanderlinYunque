/*
			< ATTENTION >
	If you need to add more map_adjustment, check 'map_adjustment_include.dm'
	These 'map_adjustment.dm' files shouldn't be included in 'dme'
*/

/datum/map_adjustment/tavella
	map_file_name = "tavella.dmm"
	blacklist = list(
	)
	// Limited positions to ensure core roles are filled.
	slot_adjust = list(
		/datum/job/lord = 1,
		/datum/job/consort = 1,
		/datum/job/hand = 1,
		/datum/job/prince = 2,
		/datum/job/captain = 1,
		/datum/job/steward: = 1,
		/datum/job/magician = 1,
		/datum/job/archivist = 1,
		/datum/job/courtphys = 1,
		/datum/job/minor_noble = 1,
		/datum/job/sunlord = 0,
		/datum/job/adventurer/courtagent = 1,
		/datum/job/royalknight = 1,
		/datum/job/guardsman = 5,
		/datum/job/lieutenant = 1,
		/datum/job/men_at_arms = 5,
		/datum/job/gatemaster = 1,
		/datum/job/dungeoneer = 1,
		/datum/job/town_elder = 0,
		/datum/job/forestwarden = 1,
		/datum/job/forestguard = 1,
		/datum/job/persistence/caravanguard = 0,
		/datum/job/priest = 1,
		/datum/job/gmtemplar = 1,
		/datum/job/monk = 3,
		/datum/job/undertaker = 2,
		/datum/job/templar = 3,
		/datum/job/inquisitor = 1,
		/datum/job/orthodoxist = 1,
		/datum/job/absolver = 1,
		/datum/job/adept = 1,
		/datum/job/innkeep = 1,
		/datum/job/blacksmith = 1,
		/datum/job/tailor = 1,
		/datum/job/alchemist = 1,
		/datum/job/artificer = 1,
		/datum/job/matron = 1,
		/datum/job/feldsher = 1,
		/datum/job/apothecary = 1,
		/datum/job/tomb_warden = 1,
		/datum/job/butler = 1,
		/datum/job/farmer = 1,
		/datum/job/miner = 1,
		/datum/job/butcher = 1,
		/datum/job/cook = 1,
		/datum/job/carpenter = 1,
		/datum/job/mason = 1,
		/datum/job/jester = 1,
		/datum/job/hunter = 1,
		/datum/job/fisher = 1,
		/datum/job/bard = 2,
		/datum/job/prisoner = 1,
		/datum/job/vagrant = 1,
		/datum/job/squire = 1,
		/datum/job/bapprentice = 1,
		/datum/job/mageapprentice = 1,
		/datum/job/servant = 1,
		/datum/job/tapster = 1,
		/datum/job/clinicapprentice = 2,
		/datum/job/innkeep_son = 1,
		/datum/job/orphan = 3,
		/datum/job/churchling = 2,
		/datum/job/soilchild = 1,
		/datum/job/merchant = 1,
		/datum/job/shophand = 1,
		/datum/job/grabber = 1,
		/datum/job/bogwitch = 1,
		/datum/job/bog_apprentice = 1,
		/datum/job/pilgrim = 3,
		/datum/job/adventurer = 3,
		/datum/job/mercenary = 2,
	)

	ages_adjust = list(
		/datum/job/forestguard = list(AGE_ADULT, AGE_MIDDLEAGED, AGE_OLD, AGE_IMMORTAL)
		/datum/job/tomb_warden = list(AGE_MIDDLEAGED, AGE_OLD, AGE_IMMORTAL)
	)
