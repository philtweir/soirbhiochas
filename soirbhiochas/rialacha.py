# https://toingaeilge.com/post/190215418983/caol-le-leathan-mar-focal-leat

from abc import abstractproperty, abstractmethod
from typing import Callable
from inspect import signature, isfunction, Signature, ismethod
from collections import OrderedDict

def tástáil_a_rith(tástáil, things_we_know, soláithraíonn=None, prefix=None, passed_already=False):
    if isfunction(tástáil) or ismethod(tástáil):
        res = tástáil_a_rith_real(tástáil, things_we_know, soláithraíonn=soláithraíonn, prefix=prefix, passed_already=passed_already)
        return res
    else:
        res = tástáil.rith_real(things_we_know, passed_already)
        return res, things_we_know

def tástáil_a_rith_real(tástáil, things_we_know, soláithraíonn=None, prefix=None, passed_already=False):
    parameters = set(signature(tástáil).parameters.keys())

    kwargs = {
        k: v
        for k, v in
        things_we_know.items()
        if k in parameters
    }

    aschuir = {}

    if 'aschuir' in parameters:
        kwargs['aschuir'] = aschuir

    if 'passed_already' in parameters:
        kwargs['passed_already'] = passed_already

    result = tástáil(**kwargs)

    if soláithraíonn:
        if set(soláithraíonn) - set(aschuir.keys()):
            raise RuntimeError(f"Keys missing {set(soláithraíonn)} {set(aschuir.keys())}")

        if prefix:
            prefix += '_'
        else:
            prefix = ''
        things_we_know = {
            f'{prefix}{key}': value
            for key, value in
            aschuir.items()
        }
    else:
        things_we_know = {}

    return result, things_we_know

class Riail:
    prefix = ''
    soláithraíonn: tuple = ()
    tástáladh: Callable[..., bool]

    def __init__(self):
        self.eisceachtaí = []
        self.eisceachtaí_names = []
        self.sample = {
            "tick": {},
            "excepted": {},
            "fail": {}
        }
        self.sample_size = 0
        self.count_per_lemma_log = {}
        self.count_per_form_log = {}
        self.count_per_demut_log = {}
        self.count = {
            c: {
                "all": {
                    "pass": 0,
                    "fail": 0,
                    "tick": 0, # passed without using an exception
                    "excepted": 0 # passed using an exception
                },
                "only": {
                    "pass": 0,
                    "fail": 0,
                    "tick": 0, # passed without using an exception
                    "excepted": 0 # passed using an exception
                }
            } for c in ("repeated", "by_lemma", "by_form", "by_demut")
        }


    def set_sample_size(self, size, cascade=True):
        self.sample_size = size
        if cascade:
            for e in self.eisceachtaí:
                e.set_sample_size(size, cascade=True)

    def get_counts(self):
        struct = {
            "self": self,
            "count": self.count,
            "exceptions": [
                e.get_counts()
                for e in self.eisceachtaí
            ],
            "exception_names": self.eisceachtaí_names
        }
        if sum(map(len, self.sample.values())):
            struct["samples"] = {
                measure: [str(f) for f in samples]
                for measure, samples in self.sample.items()
            }
        return struct

    def tástáil_a_rith(self, things_we_know, passed_already):
        return tástáil_a_rith(
            self.tástáladh,
            things_we_know,
            soláithraíonn=self.soláithraíonn,
            prefix=self.prefix,
            passed_already=passed_already
        )

    def rith(self, focal, passed_already):
        return self.rith_real({
            'focal': focal,
            'back_to_top': self
        }, passed_already)

    def set_counts(self, measure, passed_already, first_time_by_lemma, first_time_by_form, first_time_by_demut):
        counts = ["repeated"]
        if first_time_by_lemma:
            counts.append("by_lemma")
        if first_time_by_form:
            counts.append("by_form")
        if first_time_by_demut:
            counts.append("by_demut")
        for count in counts:
            self.count[count]["all"][measure] += 1
            if not passed_already:
                self.count[count]["only"][measure] += 1

    def _add_sample(self, measure, focal):
        if len(self.sample[measure]) < self.sample_size:
            self.sample[measure][str(focal)] = focal

    def rith_real(self, things_we_know, passed_already):
        global CONT
        # first time or failed last time
        first_time_by_lemma = not self.count_per_lemma_log.get(things_we_know["focal"].lemma, False)
        first_time_by_demut = not self.count_per_demut_log.get(things_we_know["focal"].demut, False)
        first_time_by_form = not self.count_per_form_log.get(str(things_we_know["focal"]), False)

        result, aschuir = self.tástáil_a_rith(
            things_we_know, passed_already
        )
        things_we_know.update(aschuir)

        passed_without_exception = result
        if result:
            self.set_counts("tick", passed_already, first_time_by_lemma, first_time_by_form, first_time_by_demut)
            if not passed_already:
                self._add_sample("tick", things_we_know["focal"])

        # IIRC, we run this even if result is already
        # true to ensure we fill things_we_know
        for eisceacht in self.eisceachtaí:
            result = result | eisceacht.rith_real(things_we_know, passed_already=result)

        if result:
            if not passed_without_exception:
                self.set_counts("excepted", passed_already, first_time_by_lemma, first_time_by_form, first_time_by_demut)
                if not passed_already:
                    self._add_sample("excepted", things_we_know["focal"])
            self.set_counts("pass", passed_already, first_time_by_lemma, first_time_by_form, first_time_by_demut)
        else:
            first_time_by_lemma = things_we_know["focal"].lemma not in self.count_per_lemma_log
            first_time_by_demut = things_we_know["focal"].demut not in self.count_per_demut_log
            first_time_by_form = str(things_we_know["focal"]) not in self.count_per_form_log
            self.set_counts("fail", passed_already, first_time_by_lemma, first_time_by_form, first_time_by_demut)
            if not passed_already:
                self._add_sample("fail", things_we_know["focal"])

        # We want to count any successful forms of a lemma
        self.count_per_lemma_log[things_we_know["focal"].lemma] = result or self.count_per_lemma_log.get(things_we_know["focal"].lemma, False)
        self.count_per_demut_log[things_we_know["focal"].demut] = result or self.count_per_demut_log.get(things_we_know["focal"].demut, False)
        self.count_per_form_log[str(things_we_know["focal"])] = result or self.count_per_form_log.get(str(things_we_know["focal"]), False)

        return result

    def eisceacht_a_dhéanamh(self, riail, name=None):
        if isfunction(riail):
            riail = RiailFunction(riail)
        self.eisceachtaí.append(riail)
        self.eisceachtaí_names.append(name)
        return self

    def __and__(self, other):
        return RiailCumaisc(self, other)

class RiailFocail(Riail):
    def rith(self, abairt, passed_already):
        return all(Riail.rith(self, f, passed_already) for f in str(abairt).split(' '))

class RiailIs(Riail):
    def __init__(self, focal):
        super().__init__()

        self.focal = focal
        self.gairid = f"Is {focal}"

    def tástáladh(self, focal) -> bool:
        return str(focal) == self.focal

class RiailFunction(Riail):
    prefix = ''
    soláithraíonn = ()

    def __init__(self, fn):
        super().__init__()

        def tástáladh(**kwargs):
            result, things_we_know = tástáil_a_rith(fn, kwargs)
            kwargs.update(things_we_know)
            return result
        self.tástáladh = tástáladh
        self.tástáladh.__signature__ = signature(fn)
        self.gairid = fn.__name__

class RiailCumaisc(Riail):
    prefix = ''
    gairid = 'IDIR'

    def __init__(self, riail_clé, riail_deis):
        super().__init__()

        if isfunction(riail_clé):
            riail_clé = RiailFunction(riail_clé)
        if isfunction(riail_deis):
            riail_deis = RiailFunction(riail_deis)

        def tástáladh(aschuir, passed_already, **kwargs):
            result_clé, things_we_know_clé = tástáil_a_rith(riail_clé, kwargs, passed_already=passed_already)
            kwargs.update(things_we_know_clé)
            aschuir.update(things_we_know_clé)
            if result_clé:
                result_deis, things_we_know_deis = tástáil_a_rith(riail_deis, kwargs, passed_already=passed_already)
                aschuir.update(things_we_know_deis)
                return result_deis
            else:
                kwargs.update({
                    f'{riail_deis.prefix}_{s}': None
                    for s in riail_clé.soláithraíonn
                })
            return False

        tástáladh_clé = riail_clé.tástáladh
        tástáladh_deis = riail_deis.tástáladh
        signature_self = signature(tástáladh)
        signature_clé = signature(tástáladh_clé)
        signature_deis = signature(tástáladh_deis)
        parameters = OrderedDict(signature_clé.parameters)
        for signature_set in (signature_deis, signature_self):
            for param, value in signature_set.parameters.items():
                if param not in parameters:
                    parameters[param] = value
        self.tástáladh = tástáladh
        self.tástáladh.__signature__ = Signature(list(parameters.values()))

        soláithraíonn_clé = (f'{riail_clé.prefix}_{s}' for s in riail_clé.soláithraíonn)
        soláithraíonn_deis = (f'{riail_deis.prefix}_{s}' for s in riail_deis.soláithraíonn)
        self.soláithraíonn = tuple(list(soláithraíonn_clé) + list(soláithraíonn_deis))
        self.riail_clé = riail_clé
        self.riail_deis = riail_deis

    def get_counts(self):
        counts = super().get_counts()
        counts.update({
            "clé": self.riail_clé.get_counts(),
            "deis": self.riail_deis.get_counts(),
        })
        return counts

    def set_sample_size(self, size, cascade=True):
        super().set_sample_size(size, cascade=cascade)
        if cascade:
            self.riail_clé.set_sample_size(size, cascade=True)
            self.riail_deis.set_sample_size(size, cascade=True)

