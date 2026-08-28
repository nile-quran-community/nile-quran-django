import re

from django.utils.translation import gettext as _


class DynamicErrorTranslator:
    _ERROR_STRINGS: list[tuple[str, str]] = [
        # NOTE: Django ORM
        (
            r"^No (?P<model>[a-zA-Z]+) matches the given query\.$",
            "No %(model)s matches the given query.",
        ),
        # NOTE: DRF fields — CharField, ModelField max_length
        (
            r"^Ensure this field has no more than (?P<max_length>\d+) characters\.$",
            "Ensure this field has no more than %(max_length)s characters.",
        ),
        (
            r"^Ensure this field has at least (?P<min_length>\d+) characters\.$",
            "Ensure this field has at least %(min_length)s characters.",
        ),
        # NOTE: DRF fields — IntegerField, FloatField, DecimalField, DurationField max/min value
        (
            r"^Ensure this value is less than or equal to (?P<max_value>.+)\.$",
            "Ensure this value is less than or equal to %(max_value)s.",
        ),
        (
            r"^Ensure this value is greater than or equal to (?P<min_value>.+)\.$",
            "Ensure this value is greater than or equal to %(min_value)s.",
        ),
        # NOTE: DRF fields — DecimalField specific
        (
            r"^Ensure that there are no more than (?P<max_digits>\d+) digits in total\.$",
            "Ensure that there are no more than %(max_digits)s digits in total.",
        ),
        (
            r"^Ensure that there are no more than (?P<max_decimal_places>\d+) decimal places\.$",
            "Ensure that there are no more than %(max_decimal_places)s decimal places.",
        ),
        (
            r"^Ensure that there are no more than (?P<max_whole_digits>\d+) digits before the decimal point\.$",
            "Ensure that there are no more than %(max_whole_digits)s digits before the decimal point.",
        ),
        # NOTE: DRF fields — DateTimeField
        (
            r"^Datetime has wrong format\. Use one of these formats instead: (?P<format>.+)\.$",
            "Datetime has wrong format. Use one of these formats instead: %(format)s.",
        ),
        (
            r"^Invalid datetime for the timezone \"(?P<timezone>[^\"]+)\"\.$",
            'Invalid datetime for the timezone "%(timezone)s".',
        ),
        # NOTE: DRF fields — DateField
        (
            r"^Date has wrong format\. Use one of these formats instead: (?P<format>.+)\.$",
            "Date has wrong format. Use one of these formats instead: %(format)s.",
        ),
        # NOTE: DRF fields — TimeField
        (
            r"^Time has wrong format\. Use one of these formats instead: (?P<format>.+)\.$",
            "Time has wrong format. Use one of these formats instead: %(format)s.",
        ),
        # NOTE: DRF fields — DurationField
        (
            r"^Duration has wrong format\. Use one of these formats instead: (?P<format>.+)\.$",
            "Duration has wrong format. Use one of these formats instead: %(format)s.",
        ),
        (
            r"^The number of days must be between (?P<min_days>-?\d+) and (?P<max_days>\d+)\.$",
            "The number of days must be between %(min_days)s and %(max_days)s.",
        ),
        # NOTE: DRF fields — ListField, ListSerializer, ManyRelatedField
        (
            r"^Ensure this field has no more than (?P<max_length>\d+) elements\.$",
            "Ensure this field has no more than %(max_length)s elements.",
        ),
        (
            r"^Ensure this field has at least (?P<min_length>\d+) elements\.$",
            "Ensure this field has at least %(min_length)s elements.",
        ),
        (
            r"^Expected a list of items but got type \"(?P<input_type>[^\"]+)\"\.$",
            'Expected a list of items but got type "%(input_type)s".',
        ),
        # NOTE: DRF fields — DictField
        (
            r"^Expected a dictionary of items but got type \"(?P<input_type>[^\"]+)\"\.$",
            'Expected a dictionary of items but got type "%(input_type)s".',
        ),
        # NOTE: DRF fields — ChoiceField, MultipleChoiceField, FilePathField
        (
            r"^\"(?P<input>.+)\" is not a valid choice\.$",
            '"%(input)s" is not a valid choice.',
        ),
        (
            r"^\"(?P<input>.+)\" is not a valid path choice\.$",
            '"%(input)s" is not a valid path choice.',
        ),
        # NOTE: DRF fields — ModelField
        (
            r"^Model has no field named \"(?P<field_name>[^\"]+)\"\.$",
            'Model has no field named "%(field_name)s".',
        ),
        # NOTE: DRF fields — FileField
        (
            r"^Ensure this filename has at most (?P<max_length>\d+) characters \(it has (?P<length>\d+)\)\.$",
            "Ensure this filename has at most %(max_length)s characters (it has %(length)s).",
        ),
        # NOTE: DRF relations — PrimaryKeyRelatedField
        (
            r"^Invalid pk \"(?P<pk_value>[^\"]+)\" - object does not exist\.$",
            'Invalid pk "%(pk_value)s" - object does not exist.',
        ),
        (
            r"^Incorrect type\. Expected pk value, received (?P<data_type>\w+)\.$",
            "Incorrect type. Expected pk value, received %(data_type)s.",
        ),
        # NOTE: DRF relations — HyperlinkedRelatedField
        (
            r"^Incorrect type\. Expected URL string, received (?P<data_type>\w+)\.$",
            "Incorrect type. Expected URL string, received %(data_type)s.",
        ),
        # NOTE: DRF relations — SlugRelatedField
        (
            r"^Object with (?P<slug_name>\w+)=(?P<value>.+) does not exist\.$",
            "Object with %(slug_name)s=%(value)s does not exist.",
        ),
        # NOTE: DRF exceptions
        (
            r"^Method \"(?P<method>\w+)\" not allowed\.$",
            'Method "%(method)s" not allowed.',
        ),
        (
            r"^Unsupported media type \"(?P<media_type>[^\"]+)\" in request\.$",
            'Unsupported media type "%(media_type)s" in request.',
        ),
        (
            r"^Request was throttled\. Expected available in (?P<wait>\d+) seconds?\.$",
            "Request was throttled. Expected available in %(wait)s seconds.",
        ),
        # NOTE: DRF validators
        (
            r"^The fields (?P<field_names>.+) must make a unique set\.$",
            "The fields %(field_names)s must make a unique set.",
        ),
        (
            r"^This field must be unique for the \"(?P<date_field>[^\"]+)\" date\.$",
            'This field must be unique for the "%(date_field)s" date.',
        ),
        (
            r"^This field must be unique for the \"(?P<date_field>[^\"]+)\" month\.$",
            'This field must be unique for the "%(date_field)s" month.',
        ),
        (
            r"^This field must be unique for the \"(?P<date_field>[^\"]+)\" year\.$",
            'This field must be unique for the "%(date_field)s" year.',
        ),
        # NOTE: DRF serializers
        (
            r"^Invalid data\. Expected a dictionary, but got (?P<datatype>\w+)\.$",
            "Invalid data. Expected a dictionary, but got %(datatype)s.",
        ),
        # NOTE: DRF validators — ProhibitSurrogateCharactersValidator
        (
            r"^Surrogate characters are not allowed: U\+(?P<code_point>[0-9A-F]+)\.$",
            "Surrogate characters are not allowed: U+%(code_point)s.",
        ),
        # NOTE: SimpleJWT
        (
            r"^Token has no '(?P<claim>[^']+)' claim$",
            "Token has no '%(claim)s' claim",
        ),
        (
            r"^Token '(?P<claim>[^']+)' claim has expired$",
            "Token '%(claim)s' claim has expired",
        ),
        (
            r"^Unrecognized algorithm type '(?P<algorithm>[^']+)'$",
            "Unrecognized algorithm type '%(algorithm)s'",
        ),
        (
            r"^You must have cryptography installed to use (?P<algorithm>.+)\.$",
            "You must have cryptography installed to use %(algorithm)s.",
        ),
    ]

    def translate(self, msg: str) -> str:
        # NOTE: Fallback to literal translation
        translated: str = _(msg)

        for regex, msgid in self._ERROR_STRINGS:
            match: re.Match | None = re.fullmatch(regex, msg)
            if match:
                placeholders: set[str] = set(match.groupdict().keys()).difference(
                    ("default",)
                )

                # NOTE: Translate the message with placeholders set for each match group
                # Example:
                # msg = "No user matches the given query."
                # regex = r"^No (?P<model>[a-zA-Z]+) matches the given query\.$"
                # msgid = "No %(model)s matches the given query."
                # match groups = {"model": "user"}
                # placeholders = { "model" }
                # translated = _("No %(model)s matches the given query.") % { "model": _("user") }
                translated = _(msgid) % {
                    placeholder: _(match.group(placeholder))
                    for placeholder in placeholders
                }
                break

        return translated
