from collections.abc import Callable

from ecoindex.best_practices.context import BestPracticesContext
from ecoindex.best_practices.models import CheckOutcome, RuleDefinition

Checker = Callable[[BestPracticesContext, RuleDefinition], CheckOutcome]

_REGISTRY: dict[str, Checker] = {}


def register(name: str) -> Callable[[Checker], Checker]:
    def decorator(func: Checker) -> Checker:
        _REGISTRY[name] = func
        return func

    return decorator


def get_checker(name: str) -> Checker:
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"Unknown best-practice checker: {name!r}") from exc


def list_checkers() -> list[str]:
    return sorted(_REGISTRY.keys())
