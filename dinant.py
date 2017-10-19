#! /usr/bin/env python3

import re
import sys
import copy
from functools import partial

class Dinant:
    # TODO: *others, should help fixing either()
    def __init__(self, other, escape=True, capture=False, name=None, times=None,
                 greedy=True):

        if times is not None:
            fail = False

            if isinstance(times, _int):
                other = exactly(times, other)
            elif isinstance(times, list):
                if len(times) == 1:
                    # times is the lower bound
                    if times[0] == 0:
                        other = zero_or_more(other, greedy)
                    elif times[0] == 1:
                        other = one_or_more(other, greedy)
                    else:
                        fail = True

                elif len(times) == 2:
                    if times[1] == 1 and (times[0] is None or times[0] is Ellipsis):
                        other = maybe(other, greedy)
                    else:
                        other = between(*times, other, greedy)
                else:
                    fail = True

            if fail:
                raise ValueError('times must be either an integer, [0, ], [1, ] or [m, n], where m or n could be ... ')

        if isinstance(other, str):
            if escape:
                self.strings = [ re.escape(other) ]
            else:
                self.strings = [ other ]
        else:
            # Dinant(Dinant('a')) == Dinant('a') but
            # id(Dinant('a')) != id(Dinant('a'))
            # the leftmost protion accumulates all the other ones in its .string attr
            # so we copy so we can reuse portions at will
            # see __add__()
            self.strings = copy.copy(other.strings)

        if capture is False:
            pass
        elif capture is True:
            # fastest way as per timeit, py3.5
            l = [ '(' ]
            l.extend(self.strings)
            l.append(')')
            self.strings = l
        elif isinstance(capture, str) or name is not None:
            name = name if name is not None else capture

            # capture holds the name to use
            l = [ '(?P<', name, '>' ]
            l.extend(self.strings)
            l.append(')')
            self.strings = l

        # caches
        self.expression = None
        self.compiled = None


    def __add__(self, other):
        result = Dinant(self)

        if isinstance(other, str):
            result.strings.append(re.escape(other))
        else:
            result.strings.extend(other.strings)

        return result


    def __radd__(self, other):
        result = Dinant(self)

        if isinstance(other, str):
            # faster than result.strings.insert(0, re.escape(other))
            # and [ re.escape(other) ]+self.strings creates another list besides [ re.escape(other) ]
            result.strings = [ re.escape(other) ]
            result.strings.extend(self.strings)
        else:
            raise ValueError('str expected, got %r')

        return result


    def __str__(self):
        if self.expression is None:
            # compact
            self.expression = ''.join(self.strings)

        return self.expression


    def __repr__(self):
        return 'Dinant%r' % self.strings


    def matches(self, s):
        if self.compiled is None:
            self.compiled = re.compile(str(self))

        self.g = self.compiled.match(s)

        return self.g is not None


    def __getitem__(self, index):
        if self.expression is None:
            self.expression = ''.join(self.strings)

        return self.expression[index]


    def match(self, s):
        """For compatibility with the `re` module."""
        if self.compiled is None:
            self.compiled = re.compile(str(self))

        return self.compiled.match(s)


    def debug(self, s):
        """Match incrementally until one of the subexpression fails matching. Returns the non-matching expression,
        True if it matches, or raise teh point where there is a syntax error."""
        so_far = ''
        syntax_error = None

        for string in self.strings:
            so_far += string
            try:
                compiled = re.compile(so_far)
            except re.error as e:
                syntax_error = e
            else:
                syntax_error = None
                if not compiled.match(s):
                    return so_far

        if syntax_error is not None:
            raise syntax_error
        else:
            # it matched
            return True


    def __eq__(self, other):
        return self.strings == other.strings


    def search(self, s):
        if self.compiled is None:
            self.compiled = re.compile(str(self))

        return self.compiled.search(s)


    def groups(self):
        if not hasattr(self, 'g'):
            raise ValueError('''This regular expression hasn't matched anything yet.''')

        return self.g.groups()


    def group(self, *args):
        if not hasattr(self, 'g'):
            raise ValueError('''This regular expression hasn't matched anything yet.''')

        return self.g.group(*args)


    def __call__(self, *args, **kwargs):
        # for supporting d.integer and d.integer(capture='foo')
        return Dinant(self, *args, **kwargs)


anything = Dinant('.', escape=False)


# this is a common structure used below
def wrap(left, middle, right):
    return Dinant(left, escape=False) + middle + Dinant(right, escape=False)


def any_of(s):
    """s must be in the right format.
    See https://docs.python.org/3/library/re.html#regular-expression-syntax ."""
    return wrap('[', Dinant(s, escape=False), ']')

# another helper function
def captures(kwargs):
    return ('capture' in kwargs and kwargs['capture']) or 'name' in kwargs

def either(*args, **kwargs):
    # TODO: this is the only point where we pre compact
    inner = Dinant('|'.join([ str(Dinant(s) if isinstance(s, str) else s) for s in args ]), escape=False)
    # optimization: check if capturing
    if captures(kwargs):
        return capture(inner, **kwargs)
    else:
        return wrap('(?:', inner, ')')


def capture(s, capture=True, name=None):
    # ugh
    name = name if name is not None else (capture if isinstance(capture, str) else None)

    if name is None:
        return wrap('(', Dinant(s), ')')
    else:
        return wrap('(?P', wrap('<', name, '>',) + Dinant(s), ')')


def backref(name):
    return wrap('(?P=', Dinant(name), ')')

def comment(text):
    return wrap('(?# ', Dinant(text), ' )')

def lookahead(s):
    return wrap('(?=', Dinant(s), ')')

def neg_lookahead(s):
    return wrap('(?!', Dinant(s), ')')

def lookbehind(s):
    return wrap('(?<=', Dinant(s), ')')

def neg_lookbehind(s):
    return wrap('(?<!', Dinant(s), ')')

# TODO: make these check lengths and use (?:...) only if > 1
def one_or_more(s, greedy=True):
    result = wrap('(?:', Dinant(s), ')+')
    if not greedy:
        result += Dinant('?', escape=False)

    return result

def zero_or_more(s, greedy=True):
    result = wrap('(?:', Dinant(s), ')*')
    if not greedy:
        result += Dinant('?', escape=False)

    return result

def maybe(s, greedy=True):
    result = wrap('(?:', Dinant(s), ')?')
    if not greedy:
        result += Dinant('?', escape=False)

    return result

then = Dinant
text = Dinant

bol = Dinant('^', escape=False)
eol = Dinant('$', escape=False)

def none_of(s):
    return wrap('[^', Dinant(s), ']')

def exactly(n, s):
    return s + wrap('{', str(n), '}')

def between(m, n, s, greedy=True):
    if m is None or m is Ellipsis:
        m = ''
    if n is None or n is Ellipsis:
        n = ''

    result =  s + wrap('{', Dinant("%s,%s" % (m, n), escape=False), '}')
    if not greedy:
        result += '?'

    return result

def at_most(n, s, greedy=True):
    return between(None, n, s, greedy)

def at_least(n, s, greedy=True):
    return between(n, None, s, greedy)


# useful shit
digit = Dinant('\d', escape=False)
digits = digit
uint = one_or_more(digits)
_int = int
int = maybe(any_of('+-')) + uint
integer = int
# NOTE: the order is important or the regexp stops at the first match
float = ( either(maybe(any_of('+-')) + maybe(one_or_more(digits)) + then('.') + one_or_more(digits),
                 integer + then('.'),
                 integer) +
          maybe(any_of('Ee') + maybe(any_of('+-')) + one_or_more(digits)) )
hex = one_or_more(any_of('0-9A-Fa-f'))
hexa = hex
# TODO: octal

# fallback
regexp = partial(Dinant, escape=False)

# NOTE: none of these regexps do any value checking (%H between 00-23, etc)
__dt_format_to_re = {
    '%a': one_or_more(anything, greedy=False),  # TODO: this is not really specific
    '%A': one_or_more(anything, greedy=False),  # TODO: this is not really specific
    '%b': one_or_more(anything, greedy=False),  # TODO: this is not really specific
    '%B': one_or_more(anything, greedy=False),  # TODO: this is not really specific
    '%d': exactly(2, digits),
    '%H': exactly(2, digits),
    '%I': exactly(2, digits),
    '%j': exactly(3, digits),
    '%m': exactly(2, digits),
    '%M': exactly(2, digits),
    '%p': one_or_more(anything, greedy=False),  # TODO: this is not really specific
    '%S': exactly(2, digits),
    '%U': exactly(2, digits),
    '%w': digit,
    '%W': exactly(2, digits),
    '%y': exactly(2, digits),
    '%Y': exactly(4, digits),
    '%z': either('+', '-') + exactly(4, digits),
    '%%': '%',
    }

# date/time
# NOTE: this must be kept in sync with
# https://docs.python.org/3/library/time.html#time.strptime
def datetime(s="%a %b %d %H:%M:%S %Y", buggy_day=False):
    for fmt in ('%c', '%x', '%X'):
        if fmt in s:
            raise ValueError('%r not supported.' % fmt)

    if buggy_day and '%d' in s:
        # Apr  7 07:46:44
        #     ^^
        s = s.replace('%d', str(either(' '+digit, exactly(2, digits))))

    # TODO: support escaped %%a
    for fmt, regexp in __dt_format_to_re.items():
        # another instance of pre compacting
        s = s.replace(fmt, str(regexp))

    return Dinant(s, escape=False)

# TODO: support the real vales
IPv4 = ( between(1, 3, digits) + '.' +
         between(1, 3, digits) + '.' +
         between(1, 3, digits) + '.' +
         between(1, 3, digits) )

IP_number = either(IPv4)  # TODO IPv6

IP_port = IP_number + ':' + integer


def run_tests():
    def ass(x, y=True):
        try:
            assert x == y
        except AssertionError:
            print("%r != %r" % (x, y))
            raise

    def test(regexp, src, dst=None, capt=True):
        try:
            if (regexp[0] != '(' or regexp[:3] == '(?:') and capt:
                regexp = capture(regexp)

            if dst is not None:
                ass(regexp.matches(src))
                ass(regexp.groups(), dst)
            else:
                assert not regexp.matches(src)
        except:
            print(regexp)
            print(src)
            raise

    ass(str(Dinant('a')), 'a')

    ass(str(then('a')), 'a')
    ass(str(then('[]')), '\[\]')

    test(any_of('a-z'), 'abc', ('a', ))
    test(any_of('+-'), '+', ('+', ))
    test(any_of('-+'), '+', ('+', ))
    test(zero_or_more(any_of('a-z')), 'abc', ('abc', ))
    test(zero_or_more(any_of('a-z')), '', ('', ))
    test(one_or_more(any_of('a-z')), '', None)
    test(one_or_more(any_of('a-z')), 'a', ('a', ))

    test(either('abc', 'def'), 'abc', ('abc', ))
    test(either('abc', 'def'), 'def', ('def', ))
    test(either('abc', 'def', capture=True), 'abc', ('abc', ))
    test(either('abc', 'def', capture='foo'), 'abc', ('abc', ))
    test(either('abc', 'def', name='foo'), 'abc', ('abc', ))

    test(anything, 'def', ('d', ))

    test(bol+capture(anything)+eol, 'def', None, False)
    test(bol+capture(either('abc', 'def'))+eol, 'def', ('def', ), False)

    test(bol+capture(maybe('foo')+either('bar', 'baz'))+eol, 'bar', ('bar', ), False)
    test(bol+capture(maybe('foo')+either('bar', 'baz'))+eol, 'foobaz', ('foobaz', ), False)

    # ass(capture(one_or_more(any_of('a-z')))+zero_or_more(then('[')+capture(one_or_more(any_of('a-z')))+then(']')), '')
    # '((?:[a-z])+)(?:[((?:[a-z])+)])*'
    #  ((?:[a-z])+)(?:[((?:[a-z])+)])*
    #  ([a-z]+)(?:[([a-z]+)])*

    name = one_or_more(any_of('a-z'))
    key = zero_or_more(any_of('a-z'))
    subexp = capture(name) + zero_or_more(then('[') + capture( key ) + then(']'))

    # some of these fail because of this:
    # https://stackoverflow.com/questions/9764930/capturing-repeating-subpatterns-in-python-regex/9765390#9765390
    test(subexp, 'foo', ('foo', None))
    test(subexp, 'foo[]', ('foo', ''))
    test(subexp, 'foo[bar]', ('foo', 'bar'))
    # test(subexp, 'foo[bar][]', ('foo', 'bar'))
    # test(subexp, 'foo[bar][baz]', ('foo', 'bar', 'baz'))
    # ass(subexp.match('foo[bar][baz][quux]').groups(),
    #     ('foo', 'bar', 'baz', 'quux'))

    test(anything, 'a', ('a', ))

    test(capture(capture(anything, name='foo') + backref('foo')), 'aa', ('aa', 'a'))

    test(anything + comment('foo'), 'a', ('a', ))

    test(capture('foo') + lookahead('bar'), 'foobar', ('foo', ))

    test(capture('foo') + neg_lookahead('bar'), 'foobaz', ('foo', ))

    # I don't understand this. it works, but don't know why
    ass((lookbehind('foo') + capture('bar')).search('foobar').groups(), ('bar', ))

    test(integer, '1942', ('1942', ))
    test(integer, '+1942', ('+1942', ))
    test(integer, '-1942', ('-1942', ))

    test(float, '1942', ('1942', ))
    test(float, '-1942', ('-1942', ))
    # -?\d+ | -?\d+\. | (?:-)?(?:(?:\d)+)?\.(?:\d)+
    test(float, '+1942.', ('+1942.', ))
    test(float, '-1942.', ('-1942.', ))
    test(float, '-1942.736', ('-1942.736', ))
    test(float, '-.736', ('-.736', ))
    test(float, '.736', ('.736', ))

    # exponential
    test(float, '1942E1', ('1942E1', ))
    test(float, '1942E+1', ('1942E+1', ))
    test(float, '1942E-1', ('1942E-1', ))
    test(float, '1942e1', ('1942e1', ))
    test(float, '1942e+1', ('1942e+1', ))
    test(float, '1942e-1', ('1942e-1', ))


    # TODO
    # test(hex, '0005da36'

    test(datetime(), 'Fri Apr 28 13:34:19 2017', ('Fri Apr 28 13:34:19 2017', ))
    test(datetime('%b %d %H:%M:%S'), 'Apr 28 13:34:19', ('Apr 28 13:34:19', ))
    test(datetime('%b %d %H:%M:%S', buggy_day=True), 'Apr  8 13:34:19', ('Apr  8 13:34:19', ))

    test(IP_number, '10.33.1.53', ('10.33.1.53', ))
    test(IP_port, '10.33.1.53:60928', ('10.33.1.53:60928', ))


    # real life examples
    def timestamp_re(capt=True):
        if capt:
            regexp = then('[') + capture(datetime("%b %d %H:%M:%S"), name='timestamp') + then(']')
        else:
            regexp = then('[') + datetime("%b %d %H:%M:%S") + then(']')

        return regexp

    line_re = bol + timestamp_re() + then(' ')

    begin_SIP_message_re = ( line_re + then('<--- ') + either('SIP read from UDP:', 'Transmitting (no NAT) to ') +
                             capture(IP_port, name='client') + then(' --->') )

    line = '[Apr 27 06:25:21] <--- Transmitting (no NAT) to 85.31.193.210:5060 --->'
    test(begin_SIP_message_re, line, ('[Apr 27 06:25:21] <--- Transmitting (no NAT) to 85.31.193.210:5060 --->',
                                      'Apr 27 06:25:21', '85.31.193.210:5060'))

    # another
    pid_re =  then('[') + integer + then(']')

    def call_id_re(capt=True, name=None):
        if capt:
            result = '[C-' + one_or_more(any_of('0-9a-f')) + ']'
        else:
            assert name is not None
            result = '[C-' + capture(one_or_more(any_of('0-9a-f')), name=name) + ']'

        return result

    call_re = ( line_re + either('VERBOSE') + pid_re + call_id_re(capt=True, name='call_id') + ' ' +
                one_or_more(any_of('a-z_\.')) + ': ' + timestamp_re(capt=False) + ' ' )

    line = '[Apr 27 07:01:27] VERBOSE[4023][C-0005da36] chan_sip.c: [Apr 27 07:01:27] Sending to 85.31.193.194:5060 (no NAT)'
    test(call_re, line, ('[Apr 27 07:01:27] VERBOSE[4023][C-0005da36] chan_sip.c: [Apr 27 07:01:27] ', 'Apr 27 07:01:27'))

    # another, smaller
    test(one_or_more(any_of('a-z0-9_.')), 'netsock2.c', ('netsock2.c', ))

    # strptime() assumes year=1900 if not parsable from the string
    # hadn't figure out how to make it return objects
    # test(datetime("%b %d %H:%M:%S"), 'Jul 26 07:33:37', (dt.datetime(1900, 6, 26, 7, 33, 37), ))

    identifier_re = one_or_more(any_of('A-Za-z0-9-'))
    line = """36569.12ms (cpu 35251.71ms) | rendering style for layer: 'terrain-small' and style 'terrain-small'"""
    render_time_re = ( bol + capture(float, name='wall_time') + 'ms ' +
                       #    v-- here's the bug, needs a space
                       '(cpu' + capture(float, name='cpu_time') + 'ms)' + one_or_more(' ') + '| ' +
                       "rendering style for layer: '" + capture(identifier_re, name='layer') + "' " +
                       "and style '" + capture(identifier_re, name='style') + "'" + eol )
    render_time_partial_match_re = ( bol + capture(float, name='wall_time') + 'ms ' +
                                     '(cpu' + capture(float, name='cpu_time') )
    ass(render_time_re.debug(line), str(render_time_partial_match_re))

    # capture
    test('bc' + Dinant('a', capture='a') + 'de', 'bcade', ('bcade', 'a'))
    test('bc' + text('a', capture='a') + 'de', 'bcade', ('bcade', 'a'))

    test(digit, '1', ('1', ))
    test(digit(capture='foo'), '1', ('1', ))
    test(integer(capture='foo'), '123', ('123', ))

    identifier_re = one_or_more(any_of('A-Za-z0-9-'))
    line = """36569.12ms (cpu 35251.71ms) | rendering style for layer: 'terrain-small' and style 'terrain-small'"""
    render_time_re = ( bol + float(capture='wall_time') + 'ms ' +
                       #    v-- here the bug is fixed
                       '(cpu ' + float(capture='cpu_time') + 'ms)' + one_or_more(' ') + '| ' +
                       "rendering style for layer: '" + identifier_re(capture='layer') + "' " +
                       "and style '" + identifier_re(capture='style') + "'" + eol )
    test(render_time_re, line, (line, '36569.12', '35251.71', 'terrain-small', 'terrain-small'))

    # name variant
    test(digit(name='foo'), '1', ('1', ))
    test(integer(name='foo'), '123', ('123', ))

    # times
    test(digit(times=[0, ]), '', ('', ))
    test(digit(times=[0, ]), '123', ('123', ))

    test(digit(times=[1, ]), '')
    test(digit(times=[1, ]), '1', ('1', ))
    test(digit(times=[1, ]), '123', ('123', ))

    test(digit(times=3), '')
    test(digit(times=3), '1')
    test(digit(times=3), '12')
    test(digit(times=3), '123', ('123', ))

    test(digit(times=[1, 3]), '')
    test(digit(times=[1, 3]), '1', ('1', ))
    test(digit(times=[1, 3]), '123', ('123', ))

    # between
    test(between(1, None, digit), '')
    test(between(1, None, digit), '1', ('1', ))
    test(between(1, None, digit), '1234567890', ('1234567890', ))

    print('A-OK!')


if __name__ == '__main__':
    s = ' '.join(sys.argv[1:])
    # eat your own dog food
    run_tests_re = bol + 'run' + any_of('-_ ') + 'test' + maybe('s') + eol
    if run_tests_re.matches(s):
        run_tests()
    else:
        print(eval(s))


del run_tests
