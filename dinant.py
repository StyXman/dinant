#! /usr/bin/env python3

import re
import sys
import copy

class Dinant:
    # TODO: *others, should help fixing either()
    def __init__(self, other, escape=True):
        if isinstance(other, str):
            if escape:
                self.strings = [ re.escape(other) ]
            else:
                self.strings = [ other ]
        else:
            # Dinant(Dinant('a')) == Dinant('a') but
            # id(Dinant('a')) != id(Dinant('a'))
            self.strings = copy.copy(other.strings)

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


anything = Dinant('.', escape=False)


def wrap(left, middle, right):
    # this is a common structure used below
    return Dinant(left, escape=False) + middle + Dinant(right, escape=False)


def any_of(s):
    """s must be in the right format.
    See https://docs.python.org/3/library/re.html#regular-expression-syntax ."""
    return wrap('[', Dinant(s, escape=False), ']')


def either(*args):
    # TODO: this is the only point where we pre compact
    return ( wrap('(?:', Dinant('|'.join([ str(Dinant(s) if isinstance(s, str) else s) for s in args ]), escape=False), ')') )


def capture(s, name=None):
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

def then(s):
    return Dinant(s)

bol = Dinant('^', escape=False)
eol = Dinant('$', escape=False)

def none_of(s):
    return wrap('[^', Dinant(s), ']')

def exactly(n, s):
    return s + wrap('{', str(n), '}')

def between(m, n, s, greedy=True):
    result =  s + wrap('{', Dinant("%d,%d" % (m, n), escape=False), '}')
    if not greedy:
        result += '?'

    return result


# useful shit
digit = Dinant('\d', escape=False)
digits = digit
uint = one_or_more(digits)
int = maybe('-') + uint
integer = int
# NOTE: the order is important or the regexp stops at the first match
float = either(maybe('-') + maybe(one_or_more(digits)) + then('.') + one_or_more(digits), integer + then('.'), integer)
hex = one_or_more(any_of('0-9A-Fa-f'))
hexa = hex

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

    def test(regexp, src, dst, capt=True):
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
    test(zero_or_more(any_of('a-z')), 'abc', ('abc', ))
    test(zero_or_more(any_of('a-z')), '', ('', ))
    test(one_or_more(any_of('a-z')), '', None)
    test(one_or_more(any_of('a-z')), 'a', ('a', ))

    test(either('abc', 'def'), 'abc', ('abc', ))
    test(either('abc', 'def'), 'def', ('def', ))

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
    test(integer, '-1942', ('-1942', ))

    test(float, '1942', ('1942', ))
    test(float, '-1942', ('-1942', ))
    # -?\d+ | -?\d+\. | (?:-)?(?:(?:\d)+)?\.(?:\d)+
    test(float, '-1942.', ('-1942.', ))
    test(float, '-1942.736', ('-1942.736', ))
    test(float, '-.736', ('-.736', ))
    test(float, '.736', ('.736', ))

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
