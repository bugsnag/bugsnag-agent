# Contributing

## Requesting a change

* [Fork](https://help.github.com/articles/fork-a-repo) the [library on GitHub](https://github.com/bugsnag/bugsnag-agent)
* Commit and push until you are happy with your contribution
* Test your changes
* [Make a pull request](https://help.github.com/articles/using-pull-requests)
* Thanks!

## Releasing a new version

### Prerequisites

* Create a PyPI account
* Get someone to add you as contributer on bugsnag-python in PyPI
* Create or edit the file ~/.pypirc

    ```
    [server-login]
    username: your-pypi-username
    password: your-pypi-password
    ```

* Install the distribution dependencies

      pip install -r dev_requirements.txt

### Making a release

* Update the version number in setup.py
* Update the CHANGELOG.md, and README.md if necessary
* Commit

    ```
    git commit -am v1.x.x
    ```

* Tag the release in git

    ```
    git tag v1.x.x
    ```

* Push to GitHub

    ```
    git push origin master && git push --tags
    ```

* Push the release to PyPI

      python setup.py sdist bdist_wheel
      twine upload dist/*
