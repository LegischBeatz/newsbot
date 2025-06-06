import sys
from pathlib import Path
import types
import importlib

# Provide dummy modules for missing dependencies
requests_mock = types.ModuleType('requests')
tweepy_mock = types.ModuleType('tweepy')
# minimal attribute used in main
setattr(tweepy_mock, 'Client', object)

sys.modules.setdefault('requests', requests_mock)
sys.modules.setdefault('tweepy', tweepy_mock)

# Ensure the project root is on sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

main = importlib.import_module('main')
strip_think = main.strip_think


def test_strip_think_removes_think_block():
    input_text = "Visible<think>hidden</think> text"
    expected = "Visible text"
    assert strip_think(input_text) == expected
    assert "<think>" not in strip_think(input_text)
