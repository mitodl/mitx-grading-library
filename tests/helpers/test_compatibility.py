from pytest import raises
import six
from mitxgraders.helpers.compatibility import coerce_string_keys_to_text_type

def test_coerce_string_keys_to_text_type():
    a_dict = {
        'cat': 'fur',
        six.u('lizard'): 'scales',
        0: 'digit'
    }

    result = coerce_string_keys_to_text_type(a_dict)
    string_keys = [key for key in result if isinstance(key, str)]

    # We have two string keys, and they are all text
    assert len(string_keys) == 2
    assert all(isinstance(key, str) for key in string_keys)

    # The non-string key is still not a string.
    assert 0 in result
