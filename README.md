`dinant` is an attempt, like may others, to make regular expressions more
readable, and, like many other, fails miserably... but we try anyways.

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

What about the name? It's a nice town in België/Belgique/Belgien that I plan to
visit some time. It also could mean 'dinning person' in French[1], which makes
sense, as I wrote this during dinner.

[1] but the real word is dîneur.
