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

def run_tests():
    def ass(x, y):
        try:
            assert x == y
        except AssertionError:
            print("%r != %r" % (x, y))
            raise

    def test(regexp, src, dst):
        try:
            ass(re.compile(capture(regexp)).match(src).groups(), dst)
        except AssertionError:
            print(regexp)
            raise

    ass(then('a'), 'a')
    ass(then('[]'), '\[\]')

    ass(re.compile(capture(any_of('a-z'))).match('abc').groups(), ('a', ))
    test(zero_or_more(any_of('a-z')), 'abc', ('abc', ))
    test(zero_or_more(any_of('a-z')), '', ('', ))
    ass(re.compile(capture(one_or_more(any_of('a-z')))).match(''), None)
    test(one_or_more(any_of('a-z')), 'a', ('a', ))

    test(either('abc', 'def'), 'abc', ('abc', ))
    test(either('abc', 'def'), 'def', ('def', ))

    test(anything, 'def', ('d', ))

    ass(re.compile(bol+capture(anything)+eol).match('def'), None)
    ass(re.compile(bol+capture(either('abc', 'def'))+eol).match('def').groups(), ('def', ))

    ass(re.compile(bol+capture(maybe('foo')+either('bar', 'baz'))+eol).match('bar').groups(), ('bar', ))
    ass(re.compile(bol+capture(maybe('foo')+either('bar', 'baz'))+eol).match('foobaz').groups(), ('foobaz', ))

    # ass(capture(one_or_more(any_of('a-z')))+zero_or_more(then('[')+capture(one_or_more(any_of('a-z')))+then(']')), '')
    # '((?:[a-z])+)(?:[((?:[a-z])+)])*'
    #  ((?:[a-z])+)(?:[((?:[a-z])+)])*
    #  ([a-z]+)(?:[([a-z]+)])*

    name = one_or_more(any_of('a-z'))
    key = zero_or_more(any_of('a-z'))
    subexp = re.compile( capture(name) +
                         zero_or_more(then('[') + capture( key ) + then(']')) )

    # some of these fail because of this:
    # https://stackoverflow.com/questions/9764930/capturing-repeating-subpatterns-in-python-regex/9765390#9765390
    ass(subexp.match('foo').groups(), ('foo', None))
    ass(subexp.match('foo[]').groups(), ('foo', ''))
    ass(subexp.match('foo[bar]').groups(), ('foo', 'bar'))
    # ass(subexp.match('foo[bar][]').groups(), ('foo', 'bar'))
    # ass(subexp.match('foo[bar][baz]').groups(), ('foo', 'bar', 'baz'))
    # ass(subexp.match('foo[bar][baz][quux]').groups(),
    #     ('foo', 'bar', 'baz', 'quux'))

    test(anything, 'a', ('a', ))

    ass(re.compile(capture(capture(anything, name='foo') +
                           backref('foo'))).match('aa').groups(), ('aa', 'a'))

    test(anything + comment('foo'), 'a', ('a', ))

    ass(re.compile(capture('foo') + lookahead('bar')).match('foobar').groups(),
        ('foo', ))

    ass(re.compile(capture('foo') + neg_lookahead('bar')).match('foobaz').groups(),
        ('foo', ))

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


if __name__ == '__main__':
    s = ' '.join(sys.argv[1:])
    # eat your own dog food
    run_tests_re = re.compile(bol + 'run' + any_of('-_ ') + 'test' + maybe('s') + eol)
    g = run_tests_re.match(s)
    if g is not None:
        run_tests()
    else:
        print(eval(s))
