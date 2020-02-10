import unittest

from click.testing import CliRunner
from canyantester import canyantester


class canyantesterTest(unittest.TestCase):
    def test_canyantester_missing_parameters(self):

        runner = CliRunner()
        result = runner.invoke(canyantester)
        self.assertNotEqual(0, result.exit_code)
