from typing import Optional
from gramadan.v2.opers import Opers
from .rialacha import Riail, RiailIs
from .collections import PREPOSITIONS, PREFIXES
from .parsáil import FocalGinearalta

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

class CaolLeCaol(Riail):
    gairid = "Caol le caol"
    prefix = "clc"
    fada = "Caol le caol, leathan le leathan"
    béarla = "Slender with slender, broad with broad"
    míniú = "Caithfidh go haontaíonn na gutaí ar dhá thaobh consain"
    soláithraíonn = ("pointí_teipe",)

    def tástáladh(self, focal: str, aschuir: dict) -> bool:
        aschuir["pointí_teipe"] = []
        focal = focal.lower()
        consain_blocks = get_consonant_blocks(focal)
        for s, f in consain_blocks:
            if s > 0 and f < len(focal) - 1:
                g1 = focal[s - 1]
                g2 = focal[f + 1]
                assert g1 in GUTAÍ
                assert g2 in GUTAÍ

                if g1 in GUTAÍ_CAOL and g2 in GUTAÍ_LEATHAN \
                        or g1 in GUTAÍ_LEATHAN and g2 in GUTAÍ_CAOL:
                    aschuir["pointí_teipe"].append((s, f))

        return not bool(aschuir["pointí_teipe"])

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

def expanded_form_passes(back_to_top, con_expansion, focal):
    focal_exp = focal.new_for_form(con_expansion)
    return True # back_to_top.rith(focal_exp, passed_already=True) RMV

def is_a_preposition(focal):
    return focal.lower() in PREPOSITIONS

def a_is_ae(clc_pointí_teipe, focal):
    return all([
        s > 1 and f'{focal[s - 2]}{focal[s - 1]}' == 'ae'
        for s, _ in clc_pointí_teipe
    ])

def begins_with_a(clc_pointí_teipe, focal, passed_already):
    demut = Opers.Demutate(str(focal))
    return len(clc_pointí_teipe) == 1 and demut.startswith('a') \
        and focal.find('a') in [s - 1 for s, _ in clc_pointí_teipe]

# Caol le caol, leathan le leathan
CAOL_LE_CAOL = (CaolLeCaol()
    # Exceptions
    .eisceacht_a_dhéanamh(
        # Contractions, if the expanded form passes (we put this here to ensure
        # they are not labelled as compound words, e.g. anseo vs anbhás)
        IsContraction() & expanded_form_passes,
        "...ach amháin 'ansin' agus 'anseo'"
    )
    .eisceacht_a_dhéanamh(
        # Compound words, if the breakpoints are where CLC fails
        FocailChumaisc() & is_breakpoint_in_failure_area,
        "...agus roinnt focail chumaisc"
    )
    .eisceacht_a_dhéanamh(
        # Is a preposition
        is_a_preposition,
        "...agus roinnt reamhfhocail"
    )
    .eisceacht_a_dhéanamh(
        # Where a slender e is really a broad ae
        a_is_ae,
        "...agus nuair a bhíonn 'ae' leathan i ndáirire"
    )
    .eisceacht_a_dhéanamh(
        # Just one of those words that just begins with an A
        # Mainly: arís, areir, aniar, adeir, ...
        begins_with_a,
        "...agus roinnt dobhríathair a thosaíonn le 'a'"
    )
    .eisceacht_a_dhéanamh(
        # There are enough examples to suggest this is the one
        # true exception - féadfaidh exists, but so does féadfidh
        # in a range of sources
        RiailIs("féadfidh"),
        "...agus 'féadfidh'"
    )
)



def rith(riail, focal):
    return riail.rith(focal, False)

if __name__ == "__main__":
    focail = [
        'neamhbheo',
        'lena',
        'rith',
        'smaoineamh',
        'laethanta',
        'traenalaí',
        'ospideal'
    ]

    for focal in focail:
        print(focal, rith(CAOL_LE_CAOL, focal))
