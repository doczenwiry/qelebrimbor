from vedo import get_color

COLOR_NAMES = {
    'highlighted' : 'k7',
    'U' : 'k5',
    'O' : 'k2',
    'X' : 'r5',
    'Y' : 'g5',
    'Z' : 'b5'
}

COLOR_RGBS = {
    k: [ 255 * c for c in get_color(rgb = v) ] for k, v in COLOR_NAMES.items()
}