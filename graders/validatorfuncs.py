"""Standalone validator functions for use in voluptuous Schema."""

def PercentageString(value):
    """Validate that a string can be interpretted as a percentage."""
    if isinstance(value, str) and value.endswith("%"):
        try:
            percent = float(value[:-1])
            return percent
        except:
            pass
    
    raise ValueError("Not a percentage string.")