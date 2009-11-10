

from twisted.trial import unittest
from pymeta.runtime import OMetaBase, ParseError, expected, expectedOneOf, eof

class RuntimeTests(unittest.TestCase):
    """
    Tests for L{pymeta.runtime}.
    """

    def test_anything(self):
        """
        L{OMetaBase.rule_anything} returns each item from the input along with its position.
        """

        data = "foo"
        o = OMetaBase(data)

        for i, c in enumerate(data):
            v, e = o.rule_anything()
            self.assertEqual((c, i), (v, e.position))


    def test_exactly(self):
        """
        L{OMetaBase.rule_exactly} returns the requested item from the input
        string along with its position, if it's there.
        """

        data = "foo"
        o = OMetaBase(data)
        v, e = o.rule_exactly("f")
        self.assertEqual(v, "f")
        self.assertEqual(e.position, 0)

    def test_exactlyFail(self):
        """
        L{OMetaBase.rule_exactly} raises L{ParseError} when the requested item
        doesn't match the input. The error contains info on what was expected
        and the position.
        """

        data = "foo"
        o = OMetaBase(data)
        e = self.assertRaises(ParseError, o.rule_exactly, "g")
        self.assertEquals(e.error, expected("g"))
        self.assertEquals(e.position, 0)



    def test_token(self):
        """
        L{OMetaBase.rule_token} matches all the characters in the given string
        plus any preceding whitespace.
        """

        data = "  foo bar"
        o = OMetaBase(data)
        v, e = o.rule_token("foo")
        self.assertEqual(v, "foo")
        self.assertEqual(e.position, 4)
        v, e = o.rule_token("bar")
        self.assertEqual(v, "bar")
        self.assertEqual(e.position, 8)


    def test_tokenFailed(self):
        """
        On failure, L{OMetaBase.rule_token} produces an error indicating the
        position where match failure occurred and the expected character.
        """
        data = "foozle"
        o = OMetaBase(data)
        e = self.assertRaises(ParseError, o.rule_token, "fog")
        self.assertEqual(e.position, 2)
        self.assertEqual(e.error, expected("g"))


    def test_many(self):
        """
        L{OMetaBase.many} returns a list of parsed values and the error that
        caused the end of the loop.
        """

        data = "ooops"
        o  = OMetaBase(data)
        self.assertEqual(o.many(lambda: o.rule_exactly('o')), (['o'] * 3, ParseError(3, expected('o'))))


    def test_or(self):
        """
        L{OMetaBase._or} returns the result of the first of its arguments to succeed.
        """

        data = "a"

        o = OMetaBase(data)
        called = [False, False, False]
        targets = ['b', 'a', 'c']
        matchers = []
        for i, m in enumerate(targets):
            def match(i=i, m=m):
                called[i] = True
                return o.exactly(m)
            matchers.append(match)

        v, e = o._or(matchers)
        self.assertEqual(called, [True, True, False])
        self.assertEqual(v, 'a')
        self.assertEqual(e.position, 0)


    def test_orSimpleFailure(self):
        """
        When none of the alternatives passed to L{OMetaBase._or} succeed, the
        one that got the furthest is returned.
        """

        data = "foozle"
        o = OMetaBase(data)

        e = self.assertRaises(ParseError, o._or,
                              [lambda: o.token("fog"),
                               lambda: o.token("foozik"),
                               lambda: o.token("woozle")])
        self.assertEqual(e.position, 4)
        self.assertEqual(e.error, expected("i"))


    def test_orFalseSuccess(self):
        """
        When a failing branch of L{OMetaBase._or} gets further than a
        succeeding one, its error is returned instead of the success branch's.
        """

        data = "foozle"
        o = OMetaBase(data)

        v, e = o._or( [lambda: o.token("fog"),
                               lambda: o.token("foozik"),
                               lambda: o.token("f")])
        self.assertEqual(e.position, 4)
        self.assertEqual(e.error, expected("i"))

    def test_orErrorTie(self):
        """
        When branches of L{OMetaBase._or} produce errors that tie for rightmost
        position, they are merged.
        """

        data = "foozle"
        o = OMetaBase(data)

        v, e = o._or( [lambda: o.token("fog"),
                               lambda: o.token("foz"),
                               lambda: o.token("f")])
        self.assertEqual(e.position, 2)
        self.assertEqual(e.error, expectedOneOf(["g", "z"]))


    def test_notError(self):
        """
        When L{OMetaBase._not} fails, its error contains the current input position and no error info.
        """

        data = "xy"
        o = OMetaBase(data)
        e = self.assertRaises(ParseError, o._not, lambda: o.exactly("x"))
        self.assertEqual(e.position, 1)
        self.assertEqual(e.error, None)


    def test_spaces(self):
        """
        L{OMetaBase.rule_spaces} provides error information.
        """

        data = "  xyz"
        o = OMetaBase(data)
        v, e = o.rule_spaces()

        self.assertEqual(e.position, 2)

    def test_predSuccess(self):
        """
        L{OMetaBase.pred} returns True and empty error info on success.
        """

        o = OMetaBase("")
        v, e = o.pred(lambda: (True, ParseError(0, None)))
        self.assertEqual((v, e), (True, ParseError(0, None)))


    def test_predFailure(self):
        """
        L{OMetaBase.pred} returns True and empty error info on success.
        """

        o = OMetaBase("")
        e = self.assertRaises(ParseError, o.pred, lambda: (False, ParseError(0, None)))
        self.assertEqual(e, ParseError(0, None))


    def test_end(self):
        """
        L{OMetaBase.rule_end} matches the end of input and raises L{ParseError}
        if input is left.
        """
        o = OMetaBase("abc")
        e = self.assertRaises(ParseError, o.rule_end)
        self.assertEqual(e, ParseError(1, None))
        o.many(o.rule_anything)
        self.assertEqual(o.rule_end(), (True, ParseError(3, None)))


    def test_letter(self):
        """
        L{OMetaBase.rule_letter} matches letters.
        """

        o = OMetaBase("a1")
        v, e = o.rule_letter()
        self.assertEqual((v, e), ("a", ParseError(0, None)))
        e = self.assertRaises(ParseError, o.rule_letter)
        self.assertEqual(e, ParseError(1, expected("letter")))


    def test_letterOrDigit(self):
        """
        L{OMetaBase.rule_letterOrDigit} matches alphanumerics.
        """
        o = OMetaBase("a1@")
        v, e = o.rule_letterOrDigit()
        self.assertEqual((v, e), ("a", ParseError(0, None)))
        v, e = o.rule_letterOrDigit()
        self.assertEqual((v, e), ("1", ParseError(1, None)))
        e = self.assertRaises(ParseError, o.rule_letterOrDigit)
        self.assertEqual(e, ParseError(2, expected("letter or digit")))


    def test_digit(self):
        """
        L{OMetaBase.rule_digit} matches digits.
        """
        o = OMetaBase("1a")
        v, e = o.rule_digit()
        self.assertEqual((v, e), ("1", ParseError(0, None)))
        e = self.assertRaises(ParseError, o.rule_digit)
        self.assertEqual(e, ParseError(1, expected("digit")))



    def test_listpattern(self):
        """
        L{OMetaBase.rule_listpattern} matches contents of lists.
        """
        o = OMetaBase([["a"]])
        v, e = o.listpattern(lambda: o.exactly("a"))
        self.assertEqual((v, e), (["a"], ParseError(0, None)))