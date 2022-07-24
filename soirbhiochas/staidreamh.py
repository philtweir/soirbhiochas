import sys
import json
import os
from pathlib import Path

from gramadan import v2
from gramadan.features import Form
from gramadan.v2.opers import Opers
from tqdm import tqdm

from .rialacha import RiailCumaisc
from .leabharlann import rith, CAOL_LE_CAOL, PIOC_INSCNE 
from .loadable import add_loadable
from collections import Counter

def count_rule_by_word(riail, corpas_iter, filt=None):
    rialacha = Counter()
    statistics = {}
    def _capture_stats(it):
        statistics['focail'] = yield from it

    for focal in tqdm(_capture_stats(corpas_iter), total=len(corpas_iter)):
        if not filt(focal):
            # We assume proper nouns are irrelevant as exceptions
            continue

        caol_le_caol = rith(riail, focal)
        if not caol_le_caol:
            rialacha[str(focal)] += 1

    return rialacha, statistics

def print_count(count, indent):
    total = count["count"]["repeated"]["only"] # Look at the interesting ones
    total_bl = count["count"]["by_lemma"]["only"] # Look at the interesting ones
    total_bd = count["count"]["by_demut"]["only"] # Look at the interesting ones
    total_bf = count["count"]["by_form"]["only"] # Look at the interesting ones
    print(
        " " * indent + f"{count['self'].gairid}"
        + f" | With rep: P {total['pass']} F {total['fail']}"
        + (f" T {total['tick']} E {total['excepted']}" if count["exceptions"] else "")
        + f" | By lemma: P {total_bl['pass']} F {total_bl['fail']}"
        + (f" T {total_bl['tick']} E {total_bl['excepted']}" if count["exceptions"] else "")
        + f" | By demut: P {total_bd['pass']} F {total_bd['fail']}"
        + (f" T {total_bd['tick']} E {total_bd['excepted']}" if count["exceptions"] else "")
        + f" | By form: P {total_bf['pass']} F {total_bf['fail']}"
        + (f" T {total_bf['tick']} E {total_bf['excepted']}" if count["exceptions"] else "")
    )

    if count['exceptions']:
        print(" " * indent + "EISCEACHTAÍ")
    for exception in count['exceptions']:
        print(" " * indent + "\\")
        print_count(exception, indent + 2)

    if isinstance(count['self'], RiailCumaisc):
        print(" " * indent + "(")
        print_count(count['clé'], indent + 2)
        print(" " * indent + " +")
        print_count(count['deis'], indent + 2)
        print(" " * indent + ")")


def rith_caol_le_caol():
    def filt(focal):
        return (focal.upos not in ('PROPN', 'SYM', 'X'))

    return rith_riail("caol_le_caol", CAOL_LE_CAOL, filt)

def rith_pioc_inscne():
    SEEMINGLY_BROKEN = ("ann", "doh", "té", "sul", "(e)amar", "uile")
    # I could be wrong, but the above appear as normal (not e.g. substantive or loaned) nouns
    # at least once in corpus with insufficient information to use them, so we skip.

    def only_nouns_with_known_gender(focal):
        return (focal < "NOUN" or focal < "PROPN") and \
            focal.focal and focal.focal.gender and \
            focal.focal.getLemma() and \
            focal.token.form not in SEEMINGLY_BROKEN

    return rith_riail("pioc_inscne", PIOC_INSCNE, only_nouns_with_known_gender)

def rith_riail(ainm, riail, filt):
    from .díolaim import Díolaim, CorrectionDict
    from .parsáil import Lexicon
    from .visualization import counts_to_vegalite

    corrections: CorrectionDict = {}
    vegalite_file = f"{ainm}.json"
    if len(sys.argv) > 3:
        with open(sys.argv[3], 'r') as f:
            correction_lines = f.readlines()
        for line in correction_lines:
            from_form, from_upos, to_form, to_upos = line.strip().split(',')
            corrections[(from_upos, from_form)] = (to_upos, to_form)
        if len(sys.argv) > 4:
            vegalite_file = sys.argv[4]

    wikt_dir = Path(os.getenv("WIKT_IRISH_PREFIXES_DIR", "wikt-irish-prefixes"))
    add_loadable("prefixes", wikt_dir / "wikt-irish-prefixes.txt")
    add_loadable("countries", wikt_dir / "countries-ga.txt")
    add_loadable("languages", wikt_dir / "wikt-languages.txt")

    lexicon = Lexicon()
    lexicon.load()
    add_loadable("lexicon", lexicon)

    corpas = Díolaim.cruthaíodh_as_comhad(sys.argv[2], lexicon.find_by_token, corrections=corrections)
    riail.set_sample_size(5)
    counter, statistics = count_rule_by_word(riail, corpas.de_réir_focal(), filt)

    print(f"Found {len(counter)} exceptions")
    most_common = counter.most_common(150)
    for row in zip(*[most_common[i::3] for i in range(3)]):
        row = [r[0] if r[1] == 1 else f"{r[0]} {r[1]}" for r in row]
        print(f"{row[0]: >20} {row[1]: >20} {row[2]: >20}")

    counts = riail.get_counts()

    print_count(counts, 0)

    print(
        f"Checked {sum(statistics['focail'])} words (inc rep), of which {statistics['focail'][1]} were missing, "
        + f"and {statistics['focail'][2]} were ignored (tagged symbols, proper nouns, etc.)"
    )

    vegalite = counts_to_vegalite(f"{riail.fada} ...", counts)
    with open(vegalite_file, "w") as f:
        json.dump(vegalite, f, indent=2)

    print(f"Wrote vegalite to {vegalite_file}")

if __name__ == "__main__":
    ainm = sys.argv[1]
    if ainm == "caol_le_caol":
        rith_caol_le_caol()
    elif ainm == "pioc_inscne":
        rith_pioc_inscne()
