**NOTE**: This is not abandoned code, it's just that is so simple, it really
doesn't need much maintenance. Still, any issues will be treated with due
diligence.

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
