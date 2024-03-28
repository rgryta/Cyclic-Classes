"""
Base cyclic classes unit tests
"""


def test_cc_one():
    """
    Check if bi-directional imports work properly
    """
    import cc_one  # pylint:disable=import-outside-toplevel

    main = cc_one.Main()

    assert isinstance(main.s, cc_one.S)
    assert isinstance(main.ms, cc_one.MS)
    assert isinstance(main.cc_am, cc_one.CC_AM)
    assert isinstance(main.nm, cc_one.NM)
    assert isinstance(main.an, cc_one.AN)
    assert isinstance(main.sma, cc_one.SMA)
    assert isinstance(main.asma, cc_one.ASMA)
    assert isinstance(main.cc_mm, cc_one.CC_MM)

    assert isinstance(main.s.main, cc_one.Main)
    assert isinstance(main.ms.main, cc_one.Main)
    assert isinstance(main.cc_am.main, cc_one.Main)
    assert isinstance(main.nm.main, cc_one.Main)
    assert isinstance(main.an.main, cc_one.Main)
    assert isinstance(main.sma.main, cc_one.Main)
    assert isinstance(main.asma.main, cc_one.Main)
    assert isinstance(main.cc_mm.main, cc_one.Main)
