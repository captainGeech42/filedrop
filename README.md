# filedrop
File sharing website

## Dev

Lint:
```
$ mypy; black .; pylint filedrop
```

Test:
```
$ python -m pytest filedrop/tests
```

Use the hook to auto lint, `black` changes will be written to disk but not staged. Still need to manually run tests, though.
```
$ ln -s $(pwd)hooks/pre-commit .git/hooks/pre-commit
```