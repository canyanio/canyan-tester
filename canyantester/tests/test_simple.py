import pytest  # type: ignore
import os

from canyantester import run_tester


def test_file_does_not_exist():
    with pytest.raises(FileNotFoundError):
        run_tester(config='/tmp/aaa.yaml')


def test_simple_command():
    with pytest.raises(FileNotFoundError):
        run_tester(
            executable='/bin/echo',
            config=os.path.join(
                os.path.dirname(__file__), 'scenarios', 'simple_command.yaml'
            ),
        )
