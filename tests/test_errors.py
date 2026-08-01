"""Unit tests for the orgflow exception hierarchy."""

import pytest

from orgflow.errors import ConfigError, OrgFlowError, TopologyError


@pytest.mark.unit
def test_base_is_exception() -> None:
    """``OrgFlowError`` roots the hierarchy at the standard ``Exception``."""
    assert issubclass(OrgFlowError, Exception)


@pytest.mark.unit
@pytest.mark.parametrize(
    "subclass",
    [
        pytest.param(TopologyError, id="TopologyError"),
        pytest.param(ConfigError, id="ConfigError"),
    ],
)
def test_domain_errors_subclass_base(subclass: type[OrgFlowError]) -> None:
    """Every domain error derives from ``OrgFlowError``."""
    assert issubclass(subclass, OrgFlowError)


@pytest.mark.unit
@pytest.mark.parametrize(
    "subclass",
    [
        pytest.param(TopologyError, id="TopologyError"),
        pytest.param(ConfigError, id="ConfigError"),
    ],
)
def test_base_catches_subclass_instances(subclass: type[OrgFlowError]) -> None:
    """Catching ``OrgFlowError`` also catches any raised subclass instance."""
    with pytest.raises(OrgFlowError):
        raise subclass("boom")
