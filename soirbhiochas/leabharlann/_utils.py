from typing import Optional
import re
from gramadan.v2.opers import Opers
from ..rialacha import Riail, RiailIs
from ..collections import PREPOSITIONS, PREFIXES
from ..parsáil import FocalGinearalta


def begins_with_a(clc_pointí_teipe, focal, passed_already):
    demut = Opers.Demutate(str(focal))
    return len(clc_pointí_teipe) == 1 and demut.startswith('a') \
        and focal.find('a') in [s - 1 for s, _ in clc_pointí_teipe]

def deireadh_caol(focal: FocalGinearalta) -> bool:
    return Opers.IsSlenderEnding(focal.lemma)

from soirbhiochas.collections import COUNTRIES, LANGUAGES

def is_a_country(focal: FocalGinearalta):
    return focal < "PROPN" and focal in COUNTRIES

def is_a_language(focal: FocalGinearalta):
    return focal < "PROPN" and focal in LANGUAGES

TEMP_CONTRACTIONS = {
    'anseo': 'an seo',
    'ansin': 'an sin',
}

MUST = False
CAN = True

GUTAÍ_CAOL = ('e', 'i', 'é', 'í')
GUTAÍ_LEATHAN = ('a', 'o', 'u', 'á', 'ó', 'ú')
GUTAÍ = tuple(list(GUTAÍ_CAOL) + list(GUTAÍ_LEATHAN))
CONSAIN = (
    'b', 'c', 'd', 'f', 'g', 'l', 'm',
    'n', 'p', 'r', 's', 't', 'v'
)

def get_consonant_blocks(focal: str) -> list[tuple[int, int]]:
    consain_blocks = []
    in_block: Optional[int] = 0 if focal[0] not in GUTAÍ else None
    for i, (p, c) in enumerate(zip(focal, focal[1:])):
        if in_block is not None and c in GUTAÍ:
            consain_blocks.append((in_block, i))
            in_block = None
        elif in_block is None and c not in GUTAÍ:
            in_block = i + 1

    return consain_blocks

class FocailChumaisc(Riail):
    gairid = "Más focal chumaisc é"
    prefix = "fc"
    fada = "Tá feidhm aige seo nuair a bheith an focal cumasc"
    béarla = "This applies when the word is (may be) compound"
    míniú = "Roinnt iompraíochtaí atá ann a bheith faoi leith do fhocail chumaisc"
    soláithraíonn = ("prefixes", "pointí_briste",)

    def tástáladh(self, focal, aschuir: dict) -> bool:
        prefixes = PREFIXES & focal
        aschuir["prefixes"] = prefixes

        if prefixes:
            aschuir["pointí_briste"] = [len(p) for p in prefixes]
            return True
        else:
            aschuir["pointí_briste"] = []
            return False

class IsContraction(Riail):
    prefix = "con"
    gairid = "Contraction?"
    soláithraíonn = ("expansion",)

    def tástáladh(self, focal, aschuir: dict) -> bool:
        focal = focal.lower()
        if focal in TEMP_CONTRACTIONS:
            aschuir["expansion"] = TEMP_CONTRACTIONS[focal]
            return True
        else:
            aschuir["expansion"] = ""
            return False

def is_breakpoint_in_failure_area(focal, clc_pointí_teipe, fc_pointí_briste):
    matches = any(
        s <= pb and pb - 1 <= f
        for pb in
        fc_pointí_briste
        for s, f in
        clc_pointí_teipe
    )

    return matches

def is_foreign(focal: FocalGinearalta) -> bool:
    # This is _not_ thorough, but by the point we apply it we should have caught most other scenarios
    return focal.foreign

def expanded_form_passes(back_to_top, con_expansion, focal):
    focal_exp = focal.new_for_form(con_expansion)
    return True # back_to_top.rith(focal_exp, passed_already=True) RMV

def is_a_preposition(focal):
    return focal.lower() in PREPOSITIONS
