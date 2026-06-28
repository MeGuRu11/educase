"""Приватные типобезопасные хелперы (де)сериализации доменных сущностей.

Назначение — сузить значения из ``Mapping[str, object]`` к конкретным типам без утечки
``Any`` (mypy strict) и единообразно сообщать об ошибках формата. Чистые функции, без I/O.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

# --- Сужение типа из object (TypeError при несовпадении) ---


def as_str(value: object) -> str:
    """Сузить значение до ``str`` (иначе ``TypeError``)."""
    if not isinstance(value, str):
        raise TypeError(f"ожидалась строка, получено {type(value).__name__}")
    return value


def as_bool(value: object) -> bool:
    """Сузить значение до ``bool`` (иначе ``TypeError``)."""
    if not isinstance(value, bool):
        raise TypeError(f"ожидался bool, получено {type(value).__name__}")
    return value


def as_int(value: object) -> int:
    """Сузить значение до ``int`` (``bool`` отвергается; иначе ``TypeError``)."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"ожидалось целое, получено {type(value).__name__}")
    return value


def as_float(value: object) -> float:
    """Сузить число (``int``/``float``, кроме ``bool``) до ``float`` (иначе ``TypeError``)."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"ожидалось число, получено {type(value).__name__}")
    return float(value)


def as_map(value: object) -> Mapping[str, object]:
    """Сузить значение до отображения (иначе ``TypeError``)."""
    if not isinstance(value, Mapping):
        raise TypeError(f"ожидался объект, получено {type(value).__name__}")
    return value


def as_seq(value: object) -> Sequence[object]:
    """Сузить значение до последовательности, кроме ``str``/``bytes`` (иначе ``TypeError``)."""
    if isinstance(value, str | bytes) or not isinstance(value, Sequence):
        raise TypeError(f"ожидался список, получено {type(value).__name__}")
    return value


# --- Доступ к полям отображения ---


def req_str(d: Mapping[str, object], key: str) -> str:
    """Обязательное строковое поле (``KeyError`` если отсутствует)."""
    return as_str(d[key])


def opt_str(d: Mapping[str, object], key: str, default: str = "") -> str:
    """Необязательное строковое поле (``default`` при отсутствии или ``null``)."""
    value = d.get(key)
    if value is None:
        return default
    return as_str(value)


def opt_str_or_none(d: Mapping[str, object], key: str) -> str | None:
    """Необязательное строковое поле, сохраняющее ``None`` (отсутствие или ``null``)."""
    value = d.get(key)
    if value is None:
        return None
    return as_str(value)


def opt_bool(d: Mapping[str, object], key: str, default: bool = False) -> bool:
    """Необязательное булево поле (``default`` при отсутствии или ``null``)."""
    value = d.get(key)
    if value is None:
        return default
    return as_bool(value)


def req_float(d: Mapping[str, object], key: str) -> float:
    """Обязательное числовое поле (``KeyError`` если отсутствует)."""
    return as_float(d[key])


def opt_float(d: Mapping[str, object], key: str, default: float = 0.0) -> float:
    """Необязательное числовое поле (``default`` при отсутствии или ``null``)."""
    value = d.get(key)
    if value is None:
        return default
    return as_float(value)


def opt_int(d: Mapping[str, object], key: str) -> int | None:
    """Необязательное целое поле, сохраняющее ``None`` (отсутствие или ``null``)."""
    value = d.get(key)
    if value is None:
        return None
    return as_int(value)


# --- Последовательности ---


def seq(d: Mapping[str, object], key: str) -> Sequence[object]:
    """Последовательность по ключу (пустая при отсутствии или ``null``)."""
    value = d.get(key)
    if value is None:
        return ()
    return as_seq(value)


def str_tuple(d: Mapping[str, object], key: str) -> tuple[str, ...]:
    """Кортеж строк по ключу."""
    return tuple(as_str(item) for item in seq(d, key))


def pair_tuple(d: Mapping[str, object], key: str) -> tuple[tuple[str, str], ...]:
    """Кортеж пар строк по ключу (каждый элемент — последовательность из двух строк)."""
    result: list[tuple[str, str]] = []
    for item in seq(d, key):
        pair = as_seq(item)
        if len(pair) != 2:
            raise ValueError(f"ожидалась пара из двух элементов, получено {len(pair)}")
        result.append((as_str(pair[0]), as_str(pair[1])))
    return tuple(result)
