# BPTK Test

This repo contains automated tests for BPTK_Py. 

This package is used as submodule for BPTK_Py. Please edit your tests here and push them. 
The script for publication in BPTK_Py automatically pulls all the newest tests from this repo

Current tests:

* [sd/test_xmile.py](sd/): Contains tests for XMILE operators
* [unittests/](unittests/): Unittests for BPTK_Py

## Add unit tests
Just write your tests in [unittests/](unittests/) or [sd/](sd/).
Make sure the filenames begin with ```test_```. Pytest will automatically discover the tests.

Each method inside the tests also needs to begin with the same ```test_``` prefix.

A valid test may be

```python
def test_xmile_operator():
    assert True == True
```

while 

```python
def xmile_operator():
    assert True == True
```

is invalid!
