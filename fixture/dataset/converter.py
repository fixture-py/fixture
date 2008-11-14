
"""Utilities for converting datasets."""

import datetime
import decimal
import types
from fixture.dataset import DataSet, DataRow
json = None
try:
    # 2.6
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        pass

def _obj_items(obj):
    for name in dir(obj):
        if name.startswith('__'):
            continue
        yield name, getattr(obj, name)

def default_json_converter(obj):
    """converts obj to a value safe for JSON serialization."""
    if isinstance(obj, (datetime.date, datetime.datetime, decimal.Decimal, float)):
        return str(obj)
    raise TypeError("%r is not JSON serializable" % (obj,))

def dataset_to_json(dataset, fp=None, default=default_json_converter, wrap=None):
    """Converts a :class:`DataSet <fixture.dataset.DataSet>` class or 
    instance to JSON (JavaScript Object Notation).
    
    See :ref:`using-dataset-to-json` for detailed usage.
    
    Keyword Arguments
    
    **fp**  
      An optional file-like object (must implement ``fp.write()``).  When
      this is not None, the output is written to the fp object, otherwise 
      the output is returned  
    
    **default**
      A callable that takes one argument (an object) and returns output 
      suitable for JSON serialization.  This will *only* be called if the 
      object cannot be serialized.  For example::
        
        >>> def encode_complex(obj):
        ...     if isinstance(obj, complex):
        ...         return [obj.real, obj.imag]
        ...     raise TypeError("%r is not JSON serializable" % (o,))
        ...
        >>> from fixture import DataSet
        >>> class ComplexData(DataSet):
        ...     class math_stuff:
        ...         complex = 2 + 1j
        ... 
        >>> dataset_to_json(ComplexData, default=encode_complex)
        '[{"complex": [2.0, 1.0]}]'
    
    **wrap**
      A callable that takes one argument, the list of dictionaries before 
      they are converted to JSON.  For example::
      
        >>> def wrap_in_dict(objects):
        ...     return {'data': objects}
        ... 
        >>> from fixture import DataSet
        >>> class ColorData(DataSet):
        ...     class red:
        ...         color = "red"
        ... 
        >>> dataset_to_json(ColorData, wrap=wrap_in_dict)
        '{"data": [{"color": "red"}]}'
    
    Returns a JSON encoded string unless you specified the **fp** keyword
    
    """
    assert json, (
        "You must have the simplejson or json module installed.  "
        "Neither could be imported")
    if isinstance(dataset, type):
        # we got a class so make it an instance
        # so that rows are resolved
        dataset = dataset()
    if not isinstance(dataset, DataSet):
        raise TypeError("First argument must be a class or instance of a DataSet")
    objects = []
    for name, row in _obj_items(dataset):
        try:
            if not issubclass(row, DataRow):
                continue
        except TypeError:
            continue
        row_dict = {}
        for col, val in _obj_items(row):
            if col=='_reserved_attr' or callable(val):
                continue
            row_dict[col] = val
        objects.append(row_dict)
    if wrap:
        objects = wrap(objects)
    if fp:
        return json.dump(objects, fp, default=default)
    else:
        return json.dumps(objects, default=default)

if __name__ == '__main__':
    import doctest
    doctest.testmod()