
# +
# leaf key(s)
# -
leaf_keys = ['baseshape', 'margin', 'shape', 'tipshape', 'type', 'venation']

leaf_keys_proper_names = [
    # use alphabetical order for human readability
    'Leaf Base Shape',
    'Leaf Margin',
    'Leaf Shape',
    'Leaf Tip Shape',
    'Leaf Type',
    'Leaf Venation'
]

# +
# leaf target(s)
# -
leaf_targets = {
    # use alphabetical order for human readability (with 'none' to denote last entry in list)
    'Leaf baseshape': [
        'AEQUILATERAL',
        'ATTENUATE',
        'AURICULATE',
        'CORDATE',
        'CUNEATE',
        'HASTATE',
        'OBLIQUE',
        'ROUNDED',
        'SAGITTATE',
        'TRUNCATE',
        'NONE'
    ],
    # use alphabetical order for human readability (with 'none' to denote last entry in list)
    'Leaf margin': [
        'BIDENTATE',
        'BIFID',
        'BIPINNATIFID',
        'BISERRATE',
        'CLEFT',
        'CRENATE',
        'CRENULATE',
        'CRISPED',
        'DENTATE',
        'DENTICULATE',
        'DIGITATE',
        'DISSECTED',
        'DIVIDED',
        'ENTIRE',
        'EROSE',
        'INCISED',
        'INVOLUTE',
        'LACERATE',
        'LACINIATE',
        'LOBED',
        'LOBULATE',
        'PALMATIFID',
        'PALMATISECT',
        'PARTED',
        'PEDATE',
        'PINNATIFID',
        'PINNATILOBATE',
        'PINNATISECT',
        'REPAND',
        'REVOLUTE',
        'RUNCINATE',
        'SERRATE',
        'SERRULATE',
        'SINUATE',
        'TRIDENTATE',
        'TRIFID',
        'TRIPARTITE',
        'TRIPINNATIFID',
        'NONE'
    ],
    # use alphabetical order for human readability (with 'none' to denote last entry in list)
    'Leaf shape': [
        'ACEROSE',
        'AWL-SHAPED',
        'CORDATE',
        'DELTOID',
        'ELLIPTIC',
        'ENSIFORM',
        'FALCATE',
        'FLABELLATE',
        'GLADIATE',
        'HASTATE',
        'LANCEOLATE',
        'LINEAR',
        'LYRATE',
        'OBCORDATE',
        'OBDELTOID',
        'OBELLIPTIC',
        'OBLANCEOLATE',
        'OBLONG',
        'OBOVATE',
        'ORBICULAR',
        'OVAL',
        'OVATE',
        'PANDURATE',
        'PELTATE',
        'PERFOLIATE',
        'QUADRATE',
        'RENIFORM',
        'RHOMBIC',
        'ROTUND',
        'SAGITTATE',
        'SPATULATE',
        'SUBULATE',
        'NONE'
    ],
    # use alphabetical order for human readability (with 'none' to denote last entry in list)
    'Leaf tipshape': [
        'ACUMINATE',
        'ACUTE',
        'APICULATE',
        'ARISTATE',
        'ARISTULATE',
        'CAUDATE',
        'CIRROSE',
        'CUSPIDATE',
        'EMARGINATE',
        'MUCRONATE',
        'MUCRONULATE',
        'MUTICOUS',
        'OBCORDATE',
        'OBTUSE',
        'RETUSE',
        'ROUNDED',
        'SUBACUTE',
        'TRUNCATE',
        'NONE'
    ],
    # use alphabetical order for human readability (with 'none' to denote last entry in list)
    'Leaf type': [
        'COMPOUND',
        'SIMPLE',
        'NONE'
    ],
    # use alphabetical order for human readability (with 'none' to denote last entry in list)
    'Leaf venation': [
        'PARALLEL',
        'RETICULATE',
        'NONE'
    ]
}

# +
# leaf targets link(s) etc
# -
leaf_targets_links = {_k: ['undefined'] * len(leaf_targets[_k]) for _k in leaf_targets}
leaf_keys_nospaces = [_k.replace(' ', '').lower() for _k in leaf_targets]
leaf_keys_spaces = [_k for _k in leaf_targets]
