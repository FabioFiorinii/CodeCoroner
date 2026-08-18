import pytest
from fastapi import HTTPException

from agents import agent_server


def test_validate_input_size_accepts_small_payload():
    agent_server._validate_input_size({'logs': 'x' * 100}, 'profile')
    agent_server._validate_input_size(None)


def test_validate_input_size_rejects_oversized_payload():
    with pytest.raises(HTTPException) as exc:
        agent_server._validate_input_size({'stacktrace': 'x' * 300_000})
    assert exc.value.status_code == 400


def test_validate_input_size_counts_across_parts():
    big = 'y' * 150_000
    with pytest.raises(HTTPException):
        agent_server._validate_input_size({'a': big}, {'b': big})