import altair as alt
from altair import vegalite

import pandas as pd

from . import staidreamh
from .díolaim import Díolaim, CorrectionDict
from .parsáil import Lexicon

def counts_to_vegalite(title: str, counts: dict, indent: int = 20) -> dict:
    """
    Produce a VegaLite dictionary for these counts.

    Note that this currently assumes one top-level rule, with
    a single level of exceptions below.
    """

    total_exceptions = counts['count']['repeated']['only']['fail'] + counts['count']['repeated']['only']['excepted']
    exceptions = pd.DataFrame([
            dict(
                {k: ex['count']['repeated']['only'][k] for k in ('pass', 'tick', 'excepted', 'fail')},
                name=ex_na,
                samples=ex['samples']['tick'],
                samples_fail=ex['samples']['fail'],
            )
            for ex, ex_na in zip(counts['exceptions'], counts['exception_names'])
    ])
    exceptions['total'] = total_exceptions
    exceptions['offset'] = exceptions['tick'].cumsum() - exceptions['tick']

    exceptions_by_level = pd.concat({
        0: pd.DataFrame([{
            'pass': counts['count']['repeated']['only']['pass'],
            'tick': counts['count']['repeated']['only']['tick'],
            'fail': counts['count']['repeated']['only']['fail'],
            'samples': counts['samples']['tick'],
            'samples_fail': counts['samples']['fail'],
            'offset': 0,
            'excepted': counts['count']['repeated']['only']['excepted'],
            'name': title,
            'total': counts['count']['repeated']['only']['pass'] + counts['count']['repeated']['only']['fail']
        }]),
        1: exceptions
    })

    exceptions_by_level["final"] = False
    for n, rows in exceptions_by_level.groupby(level=0):
        m = rows.index.get_level_values(level=1)[-1]
        exceptions_by_level.loc[(n, m), "final"] = True
    exceptions_by_level = exceptions_by_level.reset_index()

    split = ('offset', 'pass', 'fail')

    color_map_all = {
        'offset': '#EEEEEE',
        'pass': '#888888',
        'tick': '#888888',
        'fail': '#AAAAAA'
    }
    color_map_one = {
        'pass': '#27a827',
        'tick': '#27a827',
        'excepted': '#008080',
        'fail': '#008080'
    }

    text = alt.Chart().mark_text(
        xOffset=alt.ExprRef(f'datum.level_0 * {indent}'),
        align='left',
        dx=-200,
        fontSize=alt.ExprRef('(1 - 0.2 * datum.level_0) * 20'),
        yOffset=-20
    ).encode(
        text='name'
    )
    split = ['offset', 'tick', 'excepted', 'fail']
    all_split = alt.Chart().transform_fold(
        split
    ).transform_calculate(
        split=f'indexof({split}, datum.key)',
        color_key=f'datum.final && datum.key == "fail" ? "fail_all" : datum.key'
    ).mark_bar(
        xOffset=alt.ExprRef(f'datum.level_0 * {indent}'),
        yOffset=-10,
        height=6
    ).encode(
        x=alt.X('value:Q', stack="normalize", axis=alt.Axis(labels=False, title=None)),
        y=alt.Y('variable:N', sort=split, axis=alt.Axis(labels=False, title=None)),
        color=alt.Color('color_key:N', legend=None),
        order=alt.Order('split:Q'),
    )

    layers = [
        text,
        all_split,
        alt.Chart().mark_rect(
            x=0,
            x2=alt.ExprRef(f'datum.level_0 * {indent} * 0.9'),
            yOffset=20,
            height=60,
            color="#f8f8f8"
        ),
        alt.Chart().mark_rect(
            x=0,
            x2=alt.ExprRef(f'datum.level_0 * {indent} * 0.1'),
            yOffset=20,
            height=60,
            color="#008080"
        )
    ]

    selection = alt.selection_single(empty='none')
    selection2 = alt.selection_single(empty='none')
    rect_layers = None
    for l in ('tick', 'excepted', 'fail'):
        layer = alt.Chart().mark_rect(
            xOffset=alt.ExprRef(f'datum.level_0 * {indent}'),
            x2Offset=alt.ExprRef(f'datum.level_0 * {indent}'),
            yOffset=20,
            height=30,
            cornerRadius=10,
            cursor='pointer' if l == 'tick' else 'auto'
        )
        if l == 'fail':
            layer = layer.transform_filter(
                ~alt.datum.final
            )
        layer = layer.encode(
            x=alt.X(f'{l}_norm:Q', axis=alt.Axis(labels=False)), # apparently for either l
            color=alt.condition(
                selection,
                alt.value('#eeeeee'),
                alt.value(color_map_one[l]) # , legend=None, scale=None)
            ),
            #order=alt.Order('split'),
        )
        if not rect_layers:
            rect_layers = layer
        else:
            rect_layers = rect_layers + layer

    fail_layer = alt.Chart().mark_rect(
        xOffset=alt.ExprRef(f'datum.level_0 * {indent}'),
        x2Offset=alt.ExprRef(f'datum.level_0 * {indent}'),
        yOffset=20,
        height=30,
        cornerRadius=10,
        cursor='pointer'
    ).transform_filter(
        alt.datum.final
    ).encode(
        x=alt.X(f'fail_norm:Q', axis=alt.Axis(labels=False)), # apparently for either l
        color=alt.condition(
            selection2,
            alt.value('#eeeeee'),
            alt.value('#dd0000') # , legend=None, scale=None)
        ),
    ).add_selection(selection2)
    rect_layers = rect_layers + fail_layer

    text_layer = alt.Chart().mark_text(
        xOffset=alt.ExprRef(f'datum.level_0 * {indent} + 5'),
        align='left',
        dx=-200,
        fontSize=alt.ExprRef('(1 - 0.2 * datum.level_0) * 20'),
        yOffset=10,
    ).transform_calculate(
        joined_samples='join(datum.samples, ", ")'
    ).encode(
        text="joined_samples:N",
        opacity=alt.condition(selection, alt.value(0.9), alt.value(0.05))
    )
    stat_layer = alt.Chart().mark_text(
        xOffset=alt.ExprRef(f'datum.level_0 * {indent} + 5'),
        align='left',
        dx=-200,
        fontSize=alt.ExprRef('(1 - 0.2 * datum.level_0) * 20'),
        yOffset=10,
        color='white',
        text=alt.ExprRef('round(datum.tick * 100 / datum.total) + "% (" + datum.tick + ")"'),
    ).encode(
        opacity=alt.condition(selection, alt.value(0), alt.value(1))
    )

    fail_text_layer = alt.Chart().mark_text(
        xOffset=alt.ExprRef(f'datum.level_0 * {indent} + 20'),
        align='left',
        dx=-200,
        fontSize=15,
        yOffset=30,
        color='red',
        fontWeight='bold'
    ).transform_filter(
        alt.datum.final
    ).transform_calculate(
        joined_samples='"..." + join(datum.samples_fail, ", ")'
    ).encode(
        text="joined_samples:N",
        opacity=alt.condition(selection, alt.value(0.9), alt.value(0.0))
    )
    exc_stat_layer = alt.Chart().mark_text(
        xOffset=alt.ExprRef(f'datum.level_0 * {indent} + 380'),
        align='right',
        dx=-200,
        fontSize=alt.ExprRef('(1 - 0.2 * datum.level_0) * 13'),
        yOffset=3,
        color='white',
        fontWeight='bold',
        text=alt.ExprRef(
            '"Exc: " + round(datum.excepted * 100 / datum.total) + "% (" + datum.excepted + ")"'
        ),
    ).transform_filter(
        alt.datum.final
    ).encode(
        opacity=alt.condition(selection, alt.value(0), alt.value(1))
    )
    fail_stat_layer = alt.Chart().mark_text(
        xOffset=alt.ExprRef(f'datum.level_0 * {indent} + 380'),
        align='right',
        dx=-200,
        fontSize=alt.ExprRef('(1 - 0.2 * datum.level_0) * 13'),
        yOffset=18,
        color='white',
        fontWeight='bold',
        text=alt.ExprRef(
            '"F: " + round(datum.fail * 100 / datum.total) + "% (" + datum.fail + ")"'
        ),
    ).transform_filter(
        alt.datum.final
    ).encode(
        opacity=alt.condition(selection, alt.value(0), alt.value(1))
    )
    layers.append(
        (rect_layers + text_layer + stat_layer + fail_text_layer + exc_stat_layer + fail_stat_layer).add_selection(selection)
    )

    a = alt.layer(
        *layers,
        data=exceptions_by_level
    ).transform_calculate(
        used="datum.pass + datum.fail"
    ).transform_calculate(
        excepted_norm="datum.excepted / datum.used",
        pass_norm="datum.pass / datum.used",
        tick_norm="datum.tick / datum.used",
        fail_norm="datum.fail / datum.used"
    ).facet(
        row=alt.Row('name', sort=alt.EncodingSortField('ix'), title=None, header=alt.Header(labels=False)),
        padding=0,
        spacing=0
    ).configure(
        font='League Spartan',
    ).configure_range(
        category=[
            "#008080", # excepted
            "#aaaaaa", # fail
            '#dd0000', # offset
            "#eeeeee", # pass
            "#444444"  # tick
        ],
    ).configure_view(strokeOpacity=0)

    ad = a.to_dict()

    layer = ad['spec']['layer'][-1]['layer']
    layer[0]['encoding']['x2'] = {'field': 'tick_norm', 'type': 'quantitative'}
    layer[0]['encoding']['x'] = {'datum': 0}
    layer[1]['encoding']['x2'] = {'field': 'tick_norm', 'type': 'quantitative'}
    layer[1]['encoding']['x'] = {'field': 'pass_norm', 'type': 'quantitative'}
    layer[2]['encoding']['x'] = {'field': 'pass_norm', 'type': 'quantitative'}
    layer[2]['encoding']['x2'] = {'datum': 1}
    layer[3]['encoding']['x'] = {'field': 'pass_norm', 'type': 'quantitative'}
    layer[3]['encoding']['x2'] = {'datum': 1}

    return ad
