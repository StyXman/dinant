import re
import sys

anything = '.'

def any_of(s):
    return '[%s]' % s

def either(*args):
    return '(?:%s)' % '|'.join(args)

def capture(s, name=None):
    if name is None:
        return '(%s)' % s
    else:
        return '(?P<%s>%s)' % (name, s)

def backref(name):
    return '(?P=%s)' % name

def comment(text):
    return '(?# %s )' % text

def lookahead(s):
    return '(?=%s)' % s

def neg_lookahead(s):
    return '(?!%s)' % s

def lookbehind(s):
    return '(?<=%s)' % s

def neg_lookbehind(s):
    return '(?<!%s)' % s

def one_or_more(s, greedy=True):
    result = '(?:%s)+' % s
    if not greedy:
        result += '?'
    return result

def zero_or_more(s, greedy=True):
    result = '(?:%s)*' % s
    if not greedy:
        result += '?'
    return result

def maybe(s, greedy=True):
    result = '(?:%s)?' % s
    if not greedy:
        result += '?'
    return result

def then(s):
    return re.escape(s)

bol = '^'
eol = '$'

def none_of(s):
    return '[^%s]' % s

def exactly(n, s):
    return "%s{%d}" % (s, n)

def between(m, n, s, greedy=True):
    result = "%s{%d,%d}" % (s, m, n)
    if greedy:
        result += '?'
    return result

def exactly(n, s):
    return "%s{%d}" % (s, n)

# useful shit
digit = '\d'
digits = digit
int = maybe('-') + one_or_more(digits)
integer = int
# the order is important or the regexp stops at the first match
float = either(maybe('-') + maybe(one_or_more(digits)) + then('.') + one_or_more(digits), integer + then('.'), integer)

# none of these regexps do any value checking (%H between 00-23, etc)
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
def datetime(s=None):
    # NOTE: this must be kept in sync with
    # https://docs.python.org/3/library/time.html#time.strptime
    if s is None:
        s = "%a %b %d %H:%M:%S %Y"

    for fmt in ('%c', '%x', '%X'):
        if fmt in s:
            raise ValueError('%r not supported.' % fmt)

    # TODO: support escaped %%a
    for fmt, regexp in __dt_format_to_re.items():
        s = s.replace(fmt, regexp)

    return s


def run_tests():
    def ass(x, y):
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
                ass(re.compile(regexp).match(src).groups(), dst)
            else:
                ass(re.compile(regexp).match(src), dst)
        except AssertionError:
            print(regexp)
            raise

    ass(then('a'), 'a')
    ass(then('[]'), '\[\]')

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
    ass(re.compile(lookbehind('foo') + capture('bar')).search('foobar').groups(),
        ('bar', ))

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

    print('A-OK!')

if __name__ == '__main__':
    s = ' '.join(sys.argv[1:])
    # eat your own dog food
    run_tests_re = re.compile(bol + 'run' + any_of('-_ ') + 'test' + maybe('s') + eol)
    g = run_tests_re.match(s)
    if g is not None:
        run_tests()
    else:
        print(eval(s))
