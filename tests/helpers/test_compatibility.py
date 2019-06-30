from pytest import raises
import six
from mitxgraders.helpers.compatibility import ensure_text, coerce_string_keys_to_text_type

# This test is copied from six repo:
# https://github.com/benjaminp/six/blob/aa4e90bcd7b7bc13a71dfaebcb2021f4caaa8432/test_six.py#L1000
def test_ensure_text():
    UNICODE_EMOJI = six.u("\U0001F600")
    BINARY_EMOJI = b"\xf0\x9f\x98\x80"
    converted_unicode = ensure_text(UNICODE_EMOJI, encoding='utf-8', errors='strict')
    converted_binary = ensure_text(BINARY_EMOJI, encoding="utf-8", errors='strict')
    if six.PY2:
        # PY2: unicode -> unicode
        assert converted_unicode == UNICODE_EMOJI and isinstance(converted_unicode, unicode)
        # PY2: str -> unicode
        assert converted_binary == UNICODE_EMOJI and isinstance(converted_unicode, unicode)
    else:
        # PY3: str -> str
        assert converted_unicode == UNICODE_EMOJI and isinstance(converted_unicode, str)
        # PY3: bytes -> str
        assert converted_binary == UNICODE_EMOJI and isinstance(converted_unicode, str)

# This behavior of ensure_text seems not to be tested in six.py repo ...
def test_ensure_text_raises_error():
    msg = "not expecting type '{int}'".format(int=int)
    with raises(TypeError, match=msg):
        ensure_text(5)

def test_coerce_string_keys_to_text_type():
    a_dict = {
        'cat': 'fur',
        six.u('lizard'): 'scales',
        0: 'digit'
    }

    # In Python 2, our dictionary contains some string keys that are not text
    # (unicode) strings
    if six.PY2:
        string_but_not_text = lambda x: (isinstance(x, six.string_types) and
                                         not isinstance(x, six.text_type))
        assert any(string_but_not_text(key) for key in a_dict)

    result = coerce_string_keys_to_text_type(a_dict)
    string_keys = [key for key in result if isinstance(key, six.string_types)]

    # We have two string keys, and they are all text
    assert len(string_keys) == 2
    assert all(isinstance(key, six.text_type) for key in string_keys)

    # The non-string key is still not a string.
    assert 0 in result
