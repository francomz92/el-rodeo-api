from typing import Literal

from data.locale.es import es_dict_errors

Locale = Literal["es", "us"]


def get_locale_errors(locale: Locale = "us") -> dict[str, str]:
    return LOCALE_ERRORS[locale]


LOCALE_ERRORS: dict[Locale, dict[str, str]] = {
    "es": es_dict_errors,
    "us": {},
}


def translate_errors(error_type: str, errors_detail: list[str], locale: Locale) -> list[str]:
    i18n_errors = get_locale_errors(locale).get(error_type, None)
    return errors_detail if not i18n_errors else [i18n_errors]
