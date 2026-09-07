/datum/slapcraft_recipe/masonry/structure/carving_block
	name = "carving block"
	steps = list(
		/datum/slapcraft_step/item/stoneblock,
		/datum/slapcraft_step/item/stoneblock/second,
		/datum/slapcraft_step/item/stoneblock/third,
		/datum/slapcraft_step/use_item/masonry/hammer,
		)
	result_type = /obj/structure/fluff/carving_block
	craftdiff = 3
	category = "Statues"

/* tallstructure.dmi */

/datum/slapcraft_recipe/masonry/structure/statue
	abstract_type = /datum/slapcraft_recipe/masonry/structure/statue
	can_disassemble = FALSE
	step_order = SLAP_ORDER_FIRST_AND_LAST
	dense_assembly = TRUE
	repeat_perform_time = 2 SECONDS
	category = "Statues"

/datum/slapcraft_recipe/masonry/structure/statue/gargoyle
	name = "gargoyle"
	steps = list(
		/datum/slapcraft_step/structure/carving_block,
		/datum/slapcraft_step/use_item/masonry/chisel,
		/datum/slapcraft_step/use_item/masonry/hammer,
		/datum/slapcraft_step/use_item/masonry/hammer/second,
		/datum/slapcraft_step/use_item/masonry/chisel/second,
		)
	result_type = /obj/structure/fluff/statue/gargoyle
	craftdiff = 3

/datum/slapcraft_recipe/masonry/structure/statue/gargoyle_candles
	name = "gargoyle (candles)"
	steps = list(
		/datum/slapcraft_step/structure/carving_block,
		/datum/slapcraft_step/use_item/masonry/chisel,
		/datum/slapcraft_step/use_item/masonry/hammer,
		/datum/slapcraft_step/use_item/masonry/hammer/second,
		/datum/slapcraft_step/use_item/masonry/chisel/second,
		/datum/slapcraft_step/item/candles,
		)
	result_type = /obj/structure/fluff/statue/gargoyle/candles
	craftdiff = 3

/datum/slapcraft_recipe/masonry/structure/statue/mgargoyle
	name = "mossy gargoyle"
	steps = list(
		/datum/slapcraft_step/structure/carving_block,
		/datum/slapcraft_step/use_item/masonry/chisel,
		/datum/slapcraft_step/use_item/masonry/hammer,
		/datum/slapcraft_step/use_item/masonry/hammer/second,
		/datum/slapcraft_step/use_item/masonry/chisel/second,
		)
	result_type = /obj/structure/fluff/statue/gargoyle/moss
	craftdiff = 3

/datum/slapcraft_recipe/masonry/structure/statue/mgargoyle_candles
	name = "mossy gargoyle (candles)"
	steps = list(
		/datum/slapcraft_step/structure/carving_block,
		/datum/slapcraft_step/use_item/masonry/chisel,
		/datum/slapcraft_step/use_item/masonry/hammer,
		/datum/slapcraft_step/use_item/masonry/chisel/second,
		/datum/slapcraft_step/use_item/masonry/hammer/second,
		/datum/slapcraft_step/item/candles,
		)
	result_type = /obj/structure/fluff/statue/gargoyle/moss/candles
	craftdiff = 3

/datum/slapcraft_recipe/masonry/structure/statue/bstatue
	name = "necra statue"
	steps = list(
		/datum/slapcraft_step/structure/carving_block,
		/datum/slapcraft_step/use_item/masonry/chisel,
		/datum/slapcraft_step/use_item/masonry/hammer,
		/datum/slapcraft_step/use_item/masonry/hammer/second,
		/datum/slapcraft_step/use_item/masonry/chisel/second,
		)
	result_type = /obj/structure/fluff/statue/necra
	craftdiff = 3

/datum/slapcraft_recipe/masonry/structure/statue/small
	name = "elf statue"
	steps = list(
		/datum/slapcraft_step/structure/carving_block,
		/datum/slapcraft_step/use_item/masonry/chisel,
		/datum/slapcraft_step/use_item/masonry/hammer,
		/datum/slapcraft_step/use_item/masonry/hammer/second,
		/datum/slapcraft_step/use_item/masonry/chisel/second,
		)
	result_type = /obj/structure/fluff/statue/small
	craftdiff = 3

/datum/slapcraft_recipe/masonry/structure/statue/pillar
	name = "pillar"
	steps = list(
		/datum/slapcraft_step/structure/carving_block,
		/datum/slapcraft_step/use_item/masonry/chisel,
		/datum/slapcraft_step/use_item/masonry/hammer,
		/datum/slapcraft_step/use_item/masonry/hammer/second,
		/datum/slapcraft_step/use_item/masonry/chisel/second,
		)
	result_type = /obj/structure/fluff/statue/pillar
	craftdiff = 3

/datum/slapcraft_recipe/masonry/structure/statue/myth
	name = "myth statue"
	steps = list(
		/datum/slapcraft_step/structure/carving_block,
		/datum/slapcraft_step/use_item/masonry/chisel,
		/datum/slapcraft_step/use_item/masonry/hammer,
		/datum/slapcraft_step/use_item/masonry/chisel/second,
		/datum/slapcraft_step/use_item/masonry/hammer/second,
		/datum/slapcraft_step/use_item/masonry/chisel/third,
		)
	result_type = /obj/structure/fluff/statue/myth
	craftdiff = 4

/datum/slapcraft_recipe/masonry/structure/statue/interior_knight
	name = "interior knight statue"
	steps = list(
		/datum/slapcraft_step/structure/carving_block,
		/datum/slapcraft_step/use_item/masonry/chisel,
		/datum/slapcraft_step/item/stoneblock,
		/datum/slapcraft_step/use_item/masonry/hammer,
		/datum/slapcraft_step/use_item/masonry/chisel/second,
		/datum/slapcraft_step/use_item/masonry/hammer/second,
		/datum/slapcraft_step/use_item/masonry/chisel/third,
		)
	result_type = /obj/structure/fluff/statue/knight/interior/gen
	craftdiff = 4

/datum/slapcraft_recipe/masonry/structure/statue/knightalt
	name = "knight statue (alt)"
	steps = list(
		/datum/slapcraft_step/structure/carving_block,
		/datum/slapcraft_step/use_item/masonry/chisel,
		/datum/slapcraft_step/item/stoneblock,
		/datum/slapcraft_step/use_item/masonry/hammer,
		/datum/slapcraft_step/use_item/masonry/chisel/second,
		/datum/slapcraft_step/use_item/masonry/hammer/second,
		/datum/slapcraft_step/use_item/masonry/chisel/third,
		)
	result_type = /obj/structure/fluff/statue/knightalt/gen
	craftdiff = 4

/* tallandwide.dmi */

/datum/slapcraft_recipe/masonry/structure/statue/astrata
	name = "astrata statue"
	steps = list(
		/datum/slapcraft_step/structure/carving_block,
		/datum/slapcraft_step/use_item/masonry/chisel,
		/datum/slapcraft_step/item/stoneblock,
		/datum/slapcraft_step/item/stoneblock/second,
		/datum/slapcraft_step/item/gold,
		/datum/slapcraft_step/item/cloth,
		/datum/slapcraft_step/use_item/masonry/hammer,
		/datum/slapcraft_step/use_item/masonry/chisel/second,
		/datum/slapcraft_step/use_item/masonry/hammer/second,
		/datum/slapcraft_step/use_item/masonry/chisel/third,
		)
	result_type = /obj/structure/fluff/statue/astrata
	craftdiff = 5

/datum/slapcraft_recipe/masonry/structure/statue/astratabling
	name = "astrata statue (bling)"
	steps = list(
		/datum/slapcraft_step/structure/carving_block,
		/datum/slapcraft_step/use_item/masonry/chisel,
		/datum/slapcraft_step/item/stoneblock,
		/datum/slapcraft_step/item/stoneblock/second,
		/datum/slapcraft_step/item/gold,
		/datum/slapcraft_step/item/gold/second,
		/datum/slapcraft_step/item/cloth,
		/datum/slapcraft_step/use_item/masonry/hammer,
		/datum/slapcraft_step/use_item/masonry/chisel/second,
		/datum/slapcraft_step/use_item/masonry/hammer/second,
		/datum/slapcraft_step/use_item/masonry/chisel/third,
		)
	result_type = /obj/structure/fluff/statue/astrata/bling
	craftdiff = 5

/* ay.dmi */

/datum/slapcraft_recipe/masonry/structure/statue/fstatue
	name = "female statue (LEGENDARY)"
	steps = list(
		/datum/slapcraft_step/structure/carving_block,
		/datum/slapcraft_step/use_item/masonry/chisel,
		/datum/slapcraft_step/item/stoneblock,
		/datum/slapcraft_step/item/stoneblock/second,
		/datum/slapcraft_step/item/stoneblock/third,
		/datum/slapcraft_step/use_item/masonry/hammer,
		/datum/slapcraft_step/use_item/masonry/chisel/second,
		/datum/slapcraft_step/use_item/masonry/hammer/second,
		/datum/slapcraft_step/use_item/masonry/hammer/third,
		/datum/slapcraft_step/use_item/masonry/chisel/third,
		)
	result_type = /obj/structure/fluff/statue/femalestatue
	craftdiff = 6

/datum/slapcraft_recipe/masonry/structure/statue/fstatue/clean
	name = "female statue (clean) (LEGENDARY)"
	result_type = /obj/structure/fluff/statue/femalestatue/clean

/datum/slapcraft_recipe/masonry/structure/statue/fstatue/alt
	name = "female statue (alt) (LEGENDARY)"
	result_type = /obj/structure/fluff/statue/femalestatue/alt

/datum/slapcraft_recipe/masonry/structure/statue/fstatue/dancer
	name = "female statue (dancer) (LEGENDARY)"
	result_type = /obj/structure/fluff/statue/femalestatue/dancer

/datum/slapcraft_recipe/masonry/structure/statue/fstatue/lying
	name = "female statue (lying) (LEGENDARY)"
	result_type = /obj/structure/fluff/statue/femalestatue/lying

/datum/slapcraft_recipe/masonry/structure/statue/fstatue/cleanlying
	name = "female statue (clean lying) (LEGENDARY)"
	result_type = /obj/structure/fluff/statue/femalestatue/cleanlying

/datum/slapcraft_recipe/masonry/structure/statue/fstatue/cleanlying
	name = "female statue (clean lying) (LEGENDARY)"
	result_type = /obj/structure/fluff/statue/femalestatue/cleanlying

/datum/slapcraft_recipe/masonry/structure/statue/fstatue/cleanlying
	name = "female statue (clean lying) (LEGENDARY)"
	result_type = /obj/structure/fluff/statue/femalestatue/cleanlying

/datum/slapcraft_recipe/masonry/structure/statue/fstatue/cleanlying
	name = "female statue (clean lying) (LEGENDARY)"
	result_type = /obj/structure/fluff/statue/femalestatue/cleanlying

/datum/slapcraft_recipe/masonry/structure/statue/fstatue/cleanlying
	name = "female statue (clean lying) (LEGENDARY)"
	result_type = /obj/structure/fluff/statue/femalestatue/cleanlying

/datum/slapcraft_recipe/masonry/structure/statue/fstatue/cleanlying
	name = "female statue (clean lying) (LEGENDARY)"
	result_type = /obj/structure/fluff/statue/femalestatue/cleanlying

/datum/slapcraft_recipe/masonry/structure/statue/fstatue/cleanlying
	name = "female statue (clean lying) (LEGENDARY)"
	result_type = /obj/structure/fluff/statue/femalestatue/cleanlying	

/datum/slapcraft_recipe/masonry/structure/statue/copper
	name = "musician statue (LEGENDARY)"
	steps = list(
		/datum/slapcraft_step/structure/carving_block,
		/datum/slapcraft_step/use_item/masonry/chisel,
		/datum/slapcraft_step/item/stoneblock,
		/datum/slapcraft_step/item/stoneblock/second,
		/datum/slapcraft_step/item/stoneblock/third,
		/datum/slapcraft_step/item/copper,
		/datum/slapcraft_step/use_item/masonry/hammer,
		/datum/slapcraft_step/use_item/masonry/chisel/second,
		/datum/slapcraft_step/use_item/masonry/hammer/second,
		/datum/slapcraft_step/use_item/masonry/hammer/third,
		/datum/slapcraft_step/use_item/masonry/chisel/third,
		)
	result_type = /obj/structure/fluff/statue/musician
	craftdiff = 6

// Estatuas yunque

/datum/slapcraft_recipe/masonry/structure/statue/godnew/stone
	name = "Ten"
	steps = list(
		/datum/slapcraft_step/structure/carving_block,
		/datum/slapcraft_step/use_item/masonry/chisel,
		/datum/slapcraft_step/item/stoneblock,
		/datum/slapcraft_step/item/stoneblock/second,
		/datum/slapcraft_step/item/stoneblock/third,
		/datum/slapcraft_step/use_item/masonry/hammer,
		/datum/slapcraft_step/use_item/masonry/chisel/second,
		/datum/slapcraft_step/use_item/masonry/hammer/second,
		/datum/slapcraft_step/use_item/masonry/hammer/third,
		/datum/slapcraft_step/use_item/masonry/chisel/third,
		)
	result_type = /obj/structure/fluff/statue/godsnew/stone
	craftdiff = 4

/datum/slapcraft_recipe/masonry/structure/statue/godnew/stone/astrata
	name = "Astrata Statue"
	result_type = /obj/structure/fluff/statue/godsnew/astrata/stone

/datum/slapcraft_recipe/masonry/structure/statue/godnew/stone/noc
	name = "Noc Statue"
	result_type = /obj/structure/fluff/statue/godsnew/noc/stone

/datum/slapcraft_recipe/masonry/structure/statue/godnew/stone/necra
	name = "Necra Statue"
	result_type = /obj/structure/fluff/statue/godsnew/necra/stone

/datum/slapcraft_recipe/masonry/structure/statue/godnew/stone/pestra
	name = "Pestra Statue"
	result_type = /obj/structure/fluff/statue/godsnew/pestra/stone

/datum/slapcraft_recipe/masonry/structure/statue/godnew/stone/ravox
	name = "Ravox Statue"
	result_type = /obj/structure/fluff/statue/godsnew/ravox/stone

/datum/slapcraft_recipe/masonry/structure/statue/godnew/stone/malum
	name = "Malum Statue"
	result_type = /obj/structure/fluff/statue/godsnew/malum/stone

/datum/slapcraft_recipe/masonry/structure/statue/godnew/stone/dendor
	name = "Dendor Statue"
	result_type = /obj/structure/fluff/statue/godsnew/dendor/stone

/datum/slapcraft_recipe/masonry/structure/statue/godnew/stone/abyssor
	name = "Abyssor Statue"
	result_type = /obj/structure/fluff/statue/godsnew/abyssor/stone

/datum/slapcraft_recipe/masonry/structure/statue/godnew/stone/xylix
	name = "Xylix Statue"
	result_type = /obj/structure/fluff/statue/godsnew/xylix/stone

/datum/slapcraft_recipe/masonry/structure/statue/godnew/stone/eora
	name = "Eora Statue"
	result_type = /obj/structure/fluff/statue/godsnew/eora/stone

/datum/slapcraft_recipe/masonry/structure/statue/godnew/stone/zizo
	name = "Zizo Statue"
	result_type = /obj/structure/fluff/statue/godsnew/zizo/stone

/datum/slapcraft_recipe/masonry/structure/statue/godnew/stone/graggar
	name = "Graggar Statue"
	result_type = /obj/structure/fluff/statue/godsnew/graggar/stone

/datum/slapcraft_recipe/masonry/structure/statue/godnew/stone/matthios
	name = "Matthios Statue"
	result_type = /obj/structure/fluff/statue/godsnew/matthios/stone

/datum/slapcraft_recipe/masonry/structure/statue/godnew/stone/baotha
	name = "Baotha Statue"
	result_type = /obj/structure/fluff/statue/godsnew/baotha/stone