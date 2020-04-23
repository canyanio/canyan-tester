import pytest  # type: ignore
import unittest

from canyantester import run_tester


class canyantesterTest(unittest.TestCase):
    def test_canyantester_missing_parameters(self):
        with pytest.raises(FileNotFoundError):
            run_tester(config='/tmp/aaa.yaml')
