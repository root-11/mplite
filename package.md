# Packaging instructions for mplite for pypi

------------------------------------------
run:

```cmd
python -m build --wheel
twine check dist\*
twine upload dist\*
```

based on [packaging guides](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/)