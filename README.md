# filedrop
File sharing website

## Dev

todo: git precommit hook

```
$ mypy
$ black .
$ pylint filedrop
$ python -m pytest filedrop/tests
```

```
$ ln -s $(pwd)hooks/pre-commit .git/hooks/pre-commit
```