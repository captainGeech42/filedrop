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

Use the hook to auto lint, `black` changes will be written to disk but not staged. Still need to manually run tests, though. Also, if a file has changes staged and more not staged, the file as it exists on disk is what is linted against, so need to re-add them.
```
$ ln -s $(pwd)hooks/pre-commit .git/hooks/pre-commit
```