#!/usr/bin/env python3
"""pathref.py: an independent reader of SVG path data, and the writer of
tests/pathdata_tests.nv from it.

The reader follows SVG 1.1 section 8.3 and its grammar in section 8.3.9:
a number ends at the first byte that cannot continue it, an arc flag is
one byte, a command letter repeats for further arguments, and a move's
extra arguments are lines.  It normalises the way svg-nv's reader does:
every command absolute, H and V as lines, S and T with their reflected
control point, and an arc's rotation in radians.  The expected text is
that path written by svg-nv's `svgpath.to_string` at six decimals.

A case that is not a path answers the byte offset of the fault.

Run from the package root:  python3 tools/pathref.py > tests/pathdata_tests.nv
"""
import math
import re

CASES = [
    # The two spellings of a separator, and none at all.
    "M 10 10 L 20 20",
    "M10,10L20,20",
    "M10 10,20 20",
    # Relative commands and the close.
    "m 10 10 l 5 0 l 0 5 z",
    "M 0 0 H 10 V 10 h -5 v -5 Z",
    # A number ends where the next one begins.
    "M1.5.5",
    "M-1-2L3-4",
    "M0 0L.5-.5",
    "M 0 0 L 1e1 2E-1",
    "M0,0 L+5,+5",
    "M 0 0 L 5. 5.",
    # A command letter repeats, and a move's extra pairs are lines.
    "M 0 0 1 1 2 2",
    "m 1 1 2 2 3 3",
    "M 10 10 h 5 5",
    "M0 0v1 1",
    # The smooth curves reflect the previous control point, or use the pen.
    "M0 0C0 1 1 1 1 0S2 -1 2 0",
    "M 0 0 c 1 1 2 2 3 3 s 1 1 2 2",
    "M 0 0 S 1 1 2 0",
    "M0 0Q1 1 2 0T4 0t2 0",
    "M 0 0 T 2 0",
    "M 0 0 Q 1 1 2 0 L 3 0 T 5 0",
    "M 0 0 C 1 1 2 1 3 0 Q 4 1 5 0 S 7 1 8 0",
    # Arcs, their flags with and without separators, and degrees.
    "M0 0A5 5 0 0 1 10 0",
    "M0 0a5 5 30 1 0 10 0",
    "M0 0A10 10 0 1110 10",
    "M0 0a1 1 0 00 1 1",
    "M 0 0 A -5 -5 45 1 1 10 0",
    # After a close the pen is back at the subpath's start.
    "M 1 1 L 2 2 z m 1 1",
    "M 1 1 L 5 1 Z l 0 5",
    "M0 0L1 1M5 5L6 6",
    "M 0 0 z z",
    # Nothing at all.
    "",
    "   \t\n",
    # Faults.
    "L 0 0",
    "M 0",
    "M 0 0 X 5",
    "M 0 0 Z 5",
    "M 0 0 A 5 5 0 2 0 1 1",
    "M 0 0 L 5 ,",
    "5 5",
    "M 0 0 L 1 1 L",
    "M 0 0 C 1 1 2 2",
    "M e5 0",
]

NUMBER = re.compile(r'[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?')


class Fault(Exception):
    def __init__(self, at):
        self.at = at


def skip(d, i):
    while i < len(d) and d[i] in ' \t\n\r,':
        i += 1
    return i


def number(d, i):
    i = skip(d, i)
    m = NUMBER.match(d, i)
    if not m:
        raise Fault(i)
    return float(m.group(0)), m.end()


def flag(d, i):
    i = skip(d, i)
    if i >= len(d) or d[i] not in '01':
        raise Fault(i)
    return d[i] == '1', i + 1


ARITY = {'M': 2, 'L': 2, 'H': 1, 'V': 1, 'C': 6, 'S': 4, 'Q': 4, 'T': 2, 'A': 7, 'Z': 0}


def read(d):
    out = []
    i = skip(d, 0)
    letter = None
    cx = cy = sx = sy = qx = qy = 0.0
    kind = 0
    while i < len(d):
        ch = d[i]
        if ch.upper() in ARITY and ch.isalpha():
            if letter is None and ch not in 'Mm':
                raise Fault(i)
            letter = ch
            i += 1
        elif letter is None or letter in 'Zz' or not NUMBER.match(d, i):
            raise Fault(i)
        up = letter.upper()
        rel = letter.islower()
        ox, oy = (cx, cy) if rel else (0.0, 0.0)
        args = []
        for k in range(ARITY[up]):
            if up == 'A' and k in (3, 4):
                v, i = flag(d, i)
            else:
                v, i = number(d, i)
            args.append(v)
        if up == 'M':
            x, y = ox + args[0], oy + args[1]
            out.append(('M', x, y))
            cx, cy, sx, sy, kind = x, y, x, y, 0
            letter = 'l' if rel else 'L'
        elif up == 'L':
            x, y = ox + args[0], oy + args[1]
            out.append(('L', x, y))
            cx, cy, kind = x, y, 0
        elif up == 'H':
            x = ox + args[0]
            out.append(('L', x, cy))
            cx, kind = x, 0
        elif up == 'V':
            y = oy + args[0]
            out.append(('L', cx, y))
            cy, kind = y, 0
        elif up in 'CS':
            if up == 'C':
                x1, y1 = ox + args[0], oy + args[1]
                rest = args[2:]
            else:
                x1, y1 = (2 * cx - qx, 2 * cy - qy) if kind == 1 else (cx, cy)
                rest = args
            x2, y2 = ox + rest[0], oy + rest[1]
            x, y = ox + rest[2], oy + rest[3]
            out.append(('C', x1, y1, x2, y2, x, y))
            cx, cy, qx, qy, kind = x, y, x2, y2, 1
        elif up in 'QT':
            if up == 'Q':
                x1, y1 = ox + args[0], oy + args[1]
                rest = args[2:]
            else:
                x1, y1 = (2 * cx - qx, 2 * cy - qy) if kind == 2 else (cx, cy)
                rest = args
            x, y = ox + rest[0], oy + rest[1]
            out.append(('Q', x1, y1, x, y))
            cx, cy, qx, qy, kind = x, y, x1, y1, 2
        elif up == 'A':
            rx, ry, rot, large, sweep = abs(args[0]), abs(args[1]), args[2], args[3], args[4]
            x, y = ox + args[5], oy + args[6]
            # svg-nv keeps radians and writes degrees back, so the text
            # carries the degrees through the same two conversions.
            rad = rot * math.pi / 180.0
            out.append(('A', rx, ry, rad * 180.0 / math.pi, 1.0 if large else 0.0,
                        1.0 if sweep else 0.0, x, y))
            cx, cy, kind = x, y, 0
        else:
            out.append(('Z',))
            cx, cy, kind = sx, sy, 0
        i = skip(d, i)
    return out


def fmt(v, decimals=6):
    """svg-nv's number spelling: rounded half away from zero, trailing
    zeroes dropped, no exponent, no sign on zero."""
    if math.isnan(v):
        return 'NaN'
    scale = 10.0 ** decimals
    x = abs(v)
    whole = math.floor(x)
    units = math.floor((x - whole) * scale + 0.5)
    if units >= scale:
        units -= scale
        whole += 1.0
    frac = ('%0*d' % (decimals, int(units))).rstrip('0') if units >= 0.5 else ''
    body = str(int(whole)) + ('.' + frac if frac else '')
    if body == '0' or v > 0:
        return body
    return '-' + body


def spelled(cmds):
    return ''.join(c[0] + ' '.join(fmt(v) for v in c[1:]) for c in cmds)


def novo_string(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('\t', '\\t') \
        .replace('\n', '\\n') + '"'


def main():
    print('// pathdata_tests.nv — SVG path data read by svgread.parse_path and')
    print('// checked against tools/pathref.py, an independent reader in Python.')
    print('//')
    print('// Written by tools/pathref.py; edit the cases there and run it again.')
    print('// Each case is a `d` attribute and either the path it normalises to,')
    print('// written by `svgpath.to_string` at six decimals, or the byte offset')
    print('// of the fault it is refused with.')
    print('')
    print('use std.test')
    print('use svgpath')
    print('use svgread')
    print('use svgfault')
    print('')
    print('fn reads_as(d: Str, expected: Str) -> Bool')
    print('    match svgread.parse_path(d)')
    print('        Ok(p)  => svgpath.to_string(p, 6) == expected')
    print('        Err(_) => false')
    print('')
    print('fn refused_at(d: Str, offset: Int) -> Bool')
    print('    match svgread.parse_path(d)')
    print('        Ok(_)  => false')
    print('        Err(f) => svgfault.offset_of(f) == offset')
    print('')
    print('@test')
    print('fn test_path_data_agrees_with_the_python_reader() [io]')
    for d in CASES:
        try:
            expected = spelled(read(d))
            print('    test.case(%s)' % novo_string('reads ' + repr(d)))
            print('    test.assert(reads_as(%s, %s))' % (novo_string(d), novo_string(expected)))
        except Fault as f:
            print('    test.case(%s)' % novo_string('refuses %r at byte %d' % (d, f.at)))
            print('    test.assert(refused_at(%s, %d))' % (novo_string(d), f.at))


main()
