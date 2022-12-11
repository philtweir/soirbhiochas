from ..rialacha import Riail, RiailIs

from ._utils import (
    get_consonant_blocks,
    IsContraction,
    is_foreign,
    expanded_form_passes,
    GUTAÍ,
    GUTAÍ_CAOL,
    GUTAÍ_LEATHAN
)

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

def a_is_ae(clc_pointí_teipe, focal):
    return all([
        s > 1 and f'{focal[s - 2]}{focal[s - 1]}' == 'ae'
        for s, _ in clc_pointí_teipe
    ])

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
        # This is a loanword
        is_foreign,
        "...agus focail iasachta"
    )
    .eisceacht_a_dhéanamh(
        # There are enough examples to suggest this is the one
        # true exception - féadfaidh exists, but so does féadfidh
        # in a range of sources
        RiailIs("féadfidh"),
        "...agus 'féadfidh'"
    )
)


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
        print(focal, CAOL_LE_CAOL.rith(focal, passed_already=False))
