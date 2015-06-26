from ..collector import DueCreditCollector, InactiveDueCreditCollector, \
    CollectorSummary, Citation
from ..entries import BibTeX, Doi
from ..io import PickleOutput

from mock import patch
from nose.tools import assert_equal, assert_is_instance, assert_raises, assert_true
import os
import tempfile


def _test_entry(due, entry):
    due.add(entry)

_sample_bibtex = """
@ARTICLE{XXX0,
  author = {Halchenko, Yaroslav O. and Hanke, Michael},
  title = {Open is not enough. Let{'}s take the next step: An integrated, community-driven
    computing platform for neuroscience},
  journal = {Frontiers in Neuroinformatics},
  year = {2012},
  volume = {6},
  number = {00022},
  doi = {10.3389/fninf.2012.00022},
  issn = {1662-5196},
  localfile = {HH12.pdf},
}
"""
_sample_bibtex2 = """
@ARTICLE{Atkins_2002,
  title = {title},
  volume = {666},
  url = {http://dx.doi.org/10.1038/nrd842},
  DOI = {10.1038/nrd842},
  number = {3009},
  journal = {My Fancy. Journ.},
  publisher = {The Publisher},
  author = {Atkins, Joshua H. and Gershell, Leland J.},
  year = {2002},
  month = {Jul},
}
"""
_sample_doi = "a.b.c/1.2.3"

def test_entry():
    entry = BibTeX(_sample_bibtex)
    yield _test_entry, DueCreditCollector(), entry

    entries = [BibTeX(_sample_bibtex), BibTeX(_sample_bibtex),
               Doi(_sample_doi)]
    yield _test_entry, DueCreditCollector(), entries


def _test_dcite_basic(due, callable):

    assert_equal(callable("magical", 1), "load")
    # verify that @wraps correctly passes all the docstrings etc
    assert_equal(callable.__name__, "method")
    assert_equal(callable.__doc__, "docstring")


def test_dcite_method():

    # Test basic wrapping that we don't mask out the arguments
    for due in [DueCreditCollector(), InactiveDueCreditCollector()]:
        active = isinstance(due, DueCreditCollector)
        due.add(BibTeX(_sample_bibtex))

        @due.dcite("XXX0")
        def method(arg1, kwarg2="blah"):
            """docstring"""
            assert_equal(arg1, "magical")
            assert_equal(kwarg2, 1)
            return "load"

        class SomeClass(object):
            @due.dcite("XXX0")
            def method(self, arg1, kwarg2="blah"):
                """docstring"""
                assert_equal(arg1, "magical")
                assert_equal(kwarg2, 1)
                return "load"
        if active:
            assert_equal(due.citations, {})
            assert_equal(len(due._entries), 1)

        yield _test_dcite_basic, due, method

        if active:
            assert_equal(len(due.citations), 1)
            assert_equal(len(due._entries), 1)
            citation = due.citations["XXX0"]
            assert_equal(citation.count, 1)
            assert_equal(citation.level, "func duecredit.tests."
                                         "test_collector.method")

        instance = SomeClass()
        yield _test_dcite_basic, due, instance.method

        if active:
            assert_equal(len(due.citations), 1)
            assert_equal(len(due._entries), 1)
            assert_equal(citation.count, 2)
            # TODO: we should actually get level/counts pairs so here
            # it is already a different level


def test_get_output_handler_method():
    with patch.dict(os.environ, {'DUECREDIT_OUTPUTS': 'pickle'}):
        entry = BibTeX(_sample_bibtex)
        collector = DueCreditCollector()
        collector.cite(entry)

        with tempfile.NamedTemporaryFile() as f:
            summary = CollectorSummary(collector, fn=f.name)
            handlers = [summary._get_output_handler(type_, collector)
                        for type_ in ['pickle']]

            #assert_is_instance(handlers[0], TextOutput)
            assert_is_instance(handlers[0], PickleOutput)

            assert_raises(NotImplementedError, summary._get_output_handler,
                          'nothing', collector)


def test_collectors_uniform_API():
    get_api = lambda obj: [x for x in sorted(dir(obj))
                           if not x.startswith('_')
                              or x in ('__call__')]
    assert_equal(get_api(DueCreditCollector), get_api(InactiveDueCreditCollector))


def _test__docs__(method):
    assert("entry:" in method.__doc__)
    assert("kind: (" in method.__doc__)

def test__docs__():
    yield _test__docs__, DueCreditCollector.cite
    yield _test__docs__, DueCreditCollector.dcite
    yield _test__docs__, Citation.__init__