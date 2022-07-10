from typing import Optional, Iterable, Any, Callable
import pyconll # type: ignore
from gramadan.v2.noun import Noun
from gramadan.v2 import database as gramadán_db

from . import parsáil

CorrectionDict = dict[tuple[str, str], tuple[str, str]]

class FocailTrasnaitheoir:
    def __init__(self, sonraí, go_focal: Callable):
        self.sonraí = sonraí
        self.go_focal = go_focal

    def __iter__(self):
        success, failure, unknown = 0, 0, 0
        if self.sonraí is None:
            raise RuntimeError("Lód sonraí ar dtús")

        banc_focal_ainmfhocal: dict[str, list[Noun]] = {}
        for abairt in self.sonraí:
            for comhartha in abairt:
                try:
                    focal = self.go_focal(comhartha)
                except KeyError:
                    failure += 1
                    yield parsáil.FocalGinearalta(comhartha, None)
                else:
                    if comhartha.upos in ('PROPN', 'SYM', 'X'):
                        unknown += 1
                    else:
                        success += 1
                    yield focal

        return success, failure, unknown

    def __len__(self):
        return sum(len(abairt) for abairt in self.sonraí)

class Díolaim:
    def __init__(self, comhartha_go_focal: Callable):
        self.sonraí: Optional[Iterable] = None
        self.banc_focal: Optional[Iterable] = None
        self.comhartha_go_focal: Callable = comhartha_go_focal
        self.cache: dict[tuple[str, str], gramadán_db.EntityType] = {
        }

    @classmethod
    def cruthaíodh_as_comhad(cls, comhadainm: str, comhartha_go_focal: Callable, corrections: CorrectionDict):
        díolaim = cls(comhartha_go_focal)
        díolaim.lódáladh(comhadainm, corrections=corrections)
        return díolaim

    def de_réir_focal(self):
        return FocailTrasnaitheoir(self.sonraí, self.go_focal)

    def lódáladh(self, comhadainm: str, corrections: CorrectionDict) -> None:
        self.sonraí = pyconll.load_from_file(comhadainm) or []

        for from_pair, to_pair in corrections.items():
            for abairt in self.sonraí:
                for comhartha in abairt:
                    if comhartha.upos == from_pair[0] and comhartha.form == from_pair[1]:
                        comhartha._upos = to_pair[0]
                        comhartha._form = to_pair[1]

    def go_focal(self, comhartha, use_cache=True):
        result = None

        if hasattr(comhartha, 'upos') and comhartha.upos in gramadán_db.UPOS_TYPE_MAP:
            gineadh = self.comhartha_go_focal
        else:
            gineadh = lambda comhartha: parsáil.FocalGinearalta(comhartha, None)

        if use_cache and (comhartha.upos, comhartha.form.lower()) in self.cache:
            return self.cache[(comhartha.upos, comhartha.form.lower())]

        result = gineadh(comhartha)

        if comhartha.form and use_cache:
            self.cache[(comhartha.upos, comhartha.form.lower())] = result

        return result
