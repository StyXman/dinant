**NOTE**: This is not abandoned code, it's just that is so simple, it really
doesn't need much maintenance. Still, any issues will be treated with due
diligency.

`dinant` is an attempt, like may others, to make regular expressions more
readable and, like many others, fails miserably... but we try anyways.

You can find many examples in the source file, which includes unit tests to make
sure we don't make things worse. Because it's implementation is currently very,
very simple, it does not make any checks, so you can shoot you own foot. Also,
because it doesn't even attempt to, it does not makes any optimizations, and
resulting regexps can be more complex to read and less efficient. But the idea
is that you would never see them again. For instance:

```
capture( one_or_more(_any('a-z')) ) + zero_or_more(then('[') + capture( zero_or_more(_any('a-z')) ) + then(']'))
```

becomes `((?:[a-z])+)(?:\[((?:[a-z])*)\])*` and not `([a-z]+)(?:\[([a-z]*)\])*`.

One cool feature: a `Dinant` expression (object) can tell you which part of your
expression fails:

```
# this is a real world example!
In [1]: import dinant as d
In [2]: s = """36569.12ms (cpu 35251.71ms) | rendering style for layer: 'terrain-small' and style 'terrain-small'"""
In [3]: identifier_re = d.one_or_more(d.any_of('A-Za-z0-9-'))
# can you spot the error?
In [4]: render_time_re = ( d.bol + d.capture(d.float, name='wall_time') + 'ms ' +
   ...:                    '(cpu' + d.capture(d.float, name='cpu_time') + 'ms)' + d.one_or_more(' ') + '| ' +
   ...:                    "rendering style for layer: '" + d.capture(identifier_re, name='layer') + "' " +
   ...:                    "and style '" + d.capture(identifier_re, name='style') + "'" + d.eol )


In [5]: render_time_re.match(s, debug=True)
# ok, this is too verbose (I hope next version will be more human readable)
# but it's clear it's the second capture
Out[5]: '^(?P<wall_time>(?:(?:\\-)?(?:(?:\\d)+)?\\.(?:\\d)+|(?:\\-)?(?:\\d)+\\.|(?:\\-)?(?:\\d)+))ms\\ \\(cpu(?P<cpu_time>(?:(?:\\-)?(?:(?:\\d)+)?\\.(?:\\d)+|(?:\\-)?(?:\\d)+\\.|(?:\\-)?(?:\\d)+))'
# the error is that the text '(cpu' needs a space at the end
```

You might say that that expression is more difficult to read than a regular
expression, and I half agree with you. You could split your expression in its
components:

    name = one_or_more(_any('a-z'))
    key = zero_or_more(_any('a-z'))
    subexp = ( capture(name, 'name') +
               zero_or_more(then('[') + capture(key, 'key') + then(']')) )

If the module is run as a script, it will accept such an expression and print in
`stdout` the generated regexp:

    $ python3 -m dinant "bol + 'run' + _any('-_ ') + 'test' + maybe('s') + eol"
    ^run[-_ ]test(?:s)?$

What about the name? It's a nice town in België/Belgique/Belgien that I plan to
visit some time. It also could mean 'dinning person' in French[1], which makes
sense, as I wrote this during dinner.

[1] but the real word is 'dîneur'.
