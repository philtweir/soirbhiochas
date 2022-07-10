import sys

from gramadan import v2
from gramadan.features import Form
from gramadan.v2.opers import Opers
from tqdm import tqdm

from .rialacha import RiailCumaisc
from .leabharlann import rith, CAOL_LE_CAOL
from .loadable import add_loadable
from collections import Counter

def count_rule_by_word(riail, corpas_iter):
    rialacha = Counter()
    statistics = {}
    def _capture_stats(it):
        statistics['focail'] = yield from it

    for focal in tqdm(_capture_stats(corpas_iter), total=len(corpas_iter)):
        if focal.upos in ('PROPN', 'SYM', 'X'):
            # We assume proper nouns are irrelevant as exceptions
            continue

        caol_le_caol = rith(riail, focal)
        if not caol_le_caol:
            rialacha[str(focal)] += 1

    return rialacha, statistics


if __name__ == "__main__":
    from .díolaim import Díolaim, CorrectionDict
    from .parsáil import Lexicon

    corrections: CorrectionDict = {}
    if len(sys.argv) > 2:
        with open(sys.argv[2], 'r') as f:
            correction_lines = f.readlines()
        for line in correction_lines:
            from_form, from_upos, to_form, to_upos = line.split(',')
            corrections[(from_upos, from_form)] = (to_upos, to_form)

    add_loadable("prefixes", "../wiktionary/wikt-irish-prefixes.txt")

    lexicon = Lexicon()
    lexicon.load()
    add_loadable("lexicon", lexicon)

    corpas = Díolaim.cruthaíodh_as_comhad(sys.argv[1], lexicon.find_by_token, corrections=corrections)
    counter, statistics = count_rule_by_word(CAOL_LE_CAOL, corpas.de_réir_focal())
    print(f"Found {len(counter)} exceptions")
    most_common = counter.most_common(150)
    for row in zip(*[most_common[i::3] for i in range(3)]):
        row = [r[0] if r[1] == 1 else f"{r[0]} {r[1]}" for r in row]
        print(f"{row[0]: >20} {row[1]: >20} {row[2]: >20}")

    counts = CAOL_LE_CAOL.get_counts()
    def _print_count(count, indent):
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
            _print_count(exception, indent + 2)

        if isinstance(count['self'], RiailCumaisc):
            print(" " * indent + "(")
            _print_count(count['clé'], indent + 2)
            print(" " * indent + " +")
            _print_count(count['deis'], indent + 2)
            print(" " * indent + ")")
    _print_count(counts, 0)

    print(
        f"Checked {sum(statistics['focail'])} words (inc rep), of which {statistics['focail'][1]} were missing, "
        + f"and {statistics['focail'][2]} were ignored (tagged symbols, proper nouns, etc.)"
    )
