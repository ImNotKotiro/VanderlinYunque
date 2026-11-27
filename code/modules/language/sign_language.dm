/datum/language/sign_language
    name = "Psydonian Sign Language"
    desc = "A visual language communicated through hand gestures, developed by the dwarf federation to communicate with blacksmiths who had gone deaf after years of listening to the loud smacking of anvils."
    icon_state = "sign"
    speech_verb = "signs"
    ask_verb = "signs"
    exclaim_verb = "signs"
    key = "x"
    flags = SIGNLANG | LANGUAGE_HIDE_ICON_IF_NOT_UNDERSTOOD
    space_chance = 80
    sentence_chance = 5
    between_word_sentence_chance = 0
    between_word_space_chance = 100
    additional_syllable_low = -2
    additional_syllable_high = -1
    default_priority = 80
    signlang_verb = list(
    "mueve las manos expresivamente",
    "abre y cierra las manos",
    "mueve los dedos con rapidez",
    "señala con el índice",
    "señala hacia sí mismo",
    "hace un gesto de caminar con dos dedos de la mano",
    "señala hacia un lado",
    "señala hacia arriba",
    "señala hacia abajo",
    "levanta ambas manos",
    "baja lentamente las manos",
    "gira las palmas hacia arriba",
    "gira las palmas hacia abajo",
    "muestra las palmas de las manos",
    "cierra las manos en puños",
    "abre los puños lentamente",
    "junta las manos",
    "separa las manos",
    "entrelaza los dedos",
    "cruza los dedos",
    "mueve una mano de un lado a otro",
    "mueve ambas manos de un lado a otro",
    "hace un gesto afirmativo con la cabeza",
    "niega con la cabeza",
    "inclina la cabeza hacia un lado",
    "inclina la cabeza hacia el otro lado",
    "cruza los brazos",
    "levanta las cejas apuntando a su nariz",
    "arquea una ceja mientras coloca una mano en su mejilla",
    "mira fijamente con una mano levantada",
    "mira hacia un lado bajando una mano",
    "mira hacia el otro lado mientras mueve una de sus manos de un lado a otro",
    "señala sus ojos con ambas manos",
    "señala su boca con ambas manos",
    "señala sus oídos con ambas manos",
    "señala su cabeza con ambas manos",
    "se toca el pecho con una mano",
    "se lleva una mano al corazón",
    "se lleva un dedo a los labios, luego junta ambas manos",
    "hace un gesto de negación con la mano",
    "hace un gesto de aprobación con la mano",
    "agita una mano para llamar la atención.",
    "hace un pequeño movimiento circular con la mano",
    "traza una forma en el aire con un dedo",
    "traza un movimiento con ambas manos",
    "mueve las manos rápidamente",
    "mueve las manos lentamente",
    "hace una pausa con las manos alzadas",
    "gira sus manos en pequeños circulos lentamente",
    "hace un gesto con un movimiento firme"
)