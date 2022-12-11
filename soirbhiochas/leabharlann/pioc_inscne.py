import re

from gramadan.v2.features import Gender
from gramadan.v2.opers import Opers

from ..rialacha import Riail
from ..parsáil import FocalGinearalta

from ._utils import is_a_language, is_a_country, deireadh_caol

class GlacFirinscneach(Riail):
    gairid = "Glac firinscneach"
    prefix = "gf"
    fada = "Glac leis go bhfuil gach focal firinscneach"
    béarla = "Assume every word is masculine"
    míniú = "Tá formhór na bhfocal firinscneach, mar sin glac leis go bhfuil siad uile"
    soláithraíonn = ()

    def tástáladh(self, focal: FocalGinearalta) -> bool:
        return (focal.focal is not None) and focal.focal.gender == Gender.Masc


KNOWN_FEMININE_ENDINGS = [
    "eog",
    "óg",
    "lann"
]
re_fe = re.compile(f"({'|'.join(KNOWN_FEMININE_ENDINGS)})$")
def has_a_known_feminine_ending(focal: FocalGinearalta) -> bool:
    return (re_fe.search(focal.lemma) is not None)

def is_a_multisyllable_word_ending_in_acht_or_íocht(focal: FocalGinearalta) -> bool:
    return (
        (re.search("(acht|íocht)$", focal.lemma) is not None) and
        Opers.PolysyllabicV2(focal.lemma)
    )

relevant_fourth_declension_feminine_words = set()
def is_fourth_declension_feminine(focal: FocalGinearalta) -> bool:
    if focal.lemma[-1] not in Opers.VowelsSlender or focal < "PROPN" or not focal.focal:
        return False

    # We record this simply so you can see what they are later
    if focal.focal.gender == Gender.Fem:
        relevant_fourth_declension_feminine_words.add(focal.focal.getLemma())

    return focal.focal.declension == 4

PIOC_INSCNE = (GlacFirinscneach()
    .eisceacht_a_dhéanamh(
        is_a_language,
        "...or if it is a feminine language"
    )
    .eisceacht_a_dhéanamh(
        is_a_country,
        "...or if it is a feminine country"
    )
    .eisceacht_a_dhéanamh(
        is_fourth_declension_feminine,
        "...or it is (roughly) a feminine abstract noun ending in e/i"
    )
    .eisceacht_a_dhéanamh(
        is_a_multisyllable_word_ending_in_acht_or_íocht,
        "...or if it is a feminine multisyllable word with known ending"
    )
    .eisceacht_a_dhéanamh(
        has_a_known_feminine_ending,
        "...or if it is a feminine word with another standard feminine ending"
    )
    .eisceacht_a_dhéanamh(
        deireadh_caol,
        "...or if it is feminine with a slender ending"
    )
)

