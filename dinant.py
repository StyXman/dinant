import re

def _any(*args):
    if len(args) == 0:
        return '.'
    elif len(args) == 1:
        return '[%s]' % args[0]
    else:
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

def lookbehiind(s):
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

def _not(s):
    return '^'+s

def exactly(n, s):
    return "%s{%d}" % (s, n)

def between(m, n, s, greedy=True):
    result = "%s{%d,%d}" % (s, m, n)
    if greedy:
        result += '?'
    return result

def exactly(n, s):
    return "%s{%d}" % (s, n)

def run_tests():
    def ass(x, y):
        try:
            assert x == y
        except AssertionError:
            print("%r != %r" % (x, y))
            raise

    ass(then('a'), 'a')
    ass(then('[]'), '\[\]')

    ass(re.compile(capture(_any('a-z'))).match('abc').groups(), ('a', ))
    ass(re.compile(capture(zero_or_more(_any('a-z')))).match('abc').groups(), ('abc', ))
    ass(re.compile(capture(zero_or_more(_any('a-z')))).match('').groups(), ('', ))
    ass(re.compile(capture(one_or_more(_any('a-z')))).match(''), None)
    ass(re.compile(capture(one_or_more(_any('a-z')))).match('a').groups(), ('a', ))

    ass(re.compile(capture(_any('abc', 'def'))).match('abc').groups(), ('abc', ))
    ass(re.compile(capture(_any('abc', 'def'))).match('def').groups(), ('def', ))

    ass(re.compile(capture(_any())).match('def').groups(), ('d', ))

    ass(re.compile(bol+capture(_any())+eol).match('def'), None)
    ass(re.compile(bol+capture(_any('abc', 'def'))+eol).match('def').groups(), ('def', ))

    ass(re.compile(bol+capture(maybe('foo')+_any('bar', 'baz'))+eol).match('bar').groups(), ('bar', ))
    ass(re.compile(bol+capture(maybe('foo')+_any('bar', 'baz'))+eol).match('foobaz').groups(), ('foobaz', ))

    # ass(capture(one_or_more(_any('a-z')))+zero_or_more(then('[')+capture(one_or_more(_any('a-z')))+then(']')), '')
    # '((?:[a-z])+)(?:[((?:[a-z])+)])*'
    #  ((?:[a-z])+)(?:[((?:[a-z])+)])*
    #  ([a-z]+)(?:[([a-z]+)])*

    foo = ( capture( one_or_more(_any('a-z')) ) +
            zero_or_more(then('[') +
                         capture( zero_or_more(_any('a-z')) ) +
                         then(']')) )

    ass(re.compile(foo).match('foo').groups(), ('foo', None))
    ass(re.compile(foo).match('foo[]').groups(), ('foo', ''))
    ass(re.compile(foo).match('foo[bar]').groups(), ('foo', 'bar'))
    ass(re.compile(foo).match('foo[bar][]').groups(), ('foo', 'bar'))
    # ass(re.compile(foo).match('foo[bar][baz]').groups(), ('foo', 'bar', 'baz'))
    ass(re.compile(foo).match('foo[bar][baz][quux]').groups(),
        ('foo', 'bar', 'baz', 'quux'))

if __name__ == '__main__':
    run_tests()
