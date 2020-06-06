
Retrocookie
===========

|Tests| |Codecov| |PyPI| |Python Version| |Read the Docs| |License| |Black| |pre-commit| |Dependabot|

.. |Tests| image:: https://github.com/cjolowicz/retrocookie/workflows/Tests/badge.svg
   :target: https://github.com/cjolowicz/retrocookie/actions?workflow=Tests
   :alt: Tests
.. |Codecov| image:: https://codecov.io/gh/cjolowicz/retrocookie/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/cjolowicz/retrocookie
   :alt: Codecov
.. |PyPI| image:: https://img.shields.io/pypi/v/retrocookie.svg
   :target: https://pypi.org/project/retrocookie/
   :alt: PyPI
.. |Python Version| image:: https://img.shields.io/pypi/pyversions/retrocookie
   :target: https://pypi.org/project/retrocookie
   :alt: Python Version
.. |Read the Docs| image:: https://readthedocs.org/projects/retrocookie/badge/
   :target: https://retrocookie.readthedocs.io/
   :alt: Read the Docs
.. |License| image:: https://img.shields.io/pypi/l/retrocookie
   :target: https://opensource.org/licenses/MIT
   :alt: License
.. |Black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Black
.. |pre-commit| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit
.. |Dependabot| image:: https://api.dependabot.com/badges/status?host=github&repo=cjolowicz/retrocookie
   :target: https://dependabot.com
   :alt: Dependabot


Retrocookie updates Cookiecutter_ templates with changes from their instances.

When developing Cookiecutter templates,
you often need to work in a generated project rather than the template itself.
Reasons for this include the following:

- You need to run the Continuous Integration suite for the generated project
- Your development tools choke when running on the templated project

Any changes you make in the generated project
need to be backported into the template,
carefully replacing expanded variables from ``cookiecutter.json`` by templating tags,
and escaping any use of ``{{`` and ``}}``
or other tokens with special meaning in Jinja.

Retrocookie helps you in this situation.

It is designed to fetch commits from the repository of a generated project,
and import them into your Cookiecutter repository,
rewriting them on the fly to insert templating tags,
escape Jinja-special constructs,
and place files in the template directory.

Under the hood,
Retrocookie rewrites the selected commits using git-filter-repo_,
saving them to a temporary repository.
It then fetches and cherry-picks the rewritten commits
from the temporary repository into the Cookiecutter template,
using pygit2_.

Maybe you're thinking,
how can this possibly work?
One cannot reconstruct a Jinja template from its rendered output.
However, simple replacements of template variables work well in practice
when you're only importing a handful of commits at a time.


Requirements
------------

* Python 3.7+
* git >= 2.22.0


Installation
------------

You can install *Retrocookie* via pip_ from PyPI_:

.. code:: console

   $ pip install retrocookie


Usage
-----

The basic form:

.. code::

   $ retrocookie <repository> [<commits>...]
   $ retrocookie <repository> -b <branch> [--create]

The ``<repository>`` is a filesystem path to the source repository.
For ``<commits>``, see `gitrevisions(7)`__.

__ https://git-scm.com/docs/gitrevisions

Import ``HEAD`` from ``<repository>``:

.. code::

   $ retrocookie <repository>

Import the last two commits:

.. code::

   $ retrocookie <repository> HEAD~2..

Import by commit hash:

.. code::

   $ retrocookie <repository> 53268f7 6a3368a c0b4c6c

Import commits from branch ``topic``:

.. code::

   $ retrocookie <repository> --branch=topic

Equivalently:

.. code::

   $ retrocookie <repository> master..topic

Import commits from ``topic`` into a branch with the same name:

.. code::

   $ retrocookie <repository> --branch=topic --create

Equivalently, using short options:

.. code::

   $ retrocookie <repository> -cb topic

Import commits from branch ``topic``, which was branched off ``1.0``:

.. code::

   $ retrocookie <repository> --branch=topic --upstream=1.0

Equivalently:

.. code::

   $ retrocookie <repository> 1.0..topic

Import ``HEAD`` into a new branch ``topic``:

.. code::

   $ retrocookie <repository> --create-branch=topic


Contributing
------------

Contributions are very welcome.
To learn more, see the `Contributor Guide`_.


License
-------

Distributed under the terms of the MIT_ license,
*Retrocookie* is free and open source software.


Issues
------

If you encounter any problems,
please `file an issue`_ along with a detailed description.


Credits
-------

This project was generated from `@cjolowicz`_'s `Hypermodern Python Cookiecutter`_ template.


.. _@cjolowicz: https://github.com/cjolowicz
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _Hypermodern Python Cookiecutter: https://github.com/cjolowicz/cookiecutter-hypermodern-python
.. _MIT: http://opensource.org/licenses/MIT
.. _PyPI: https://pypi.org/
.. _file an issue: https://github.com/cjolowicz/retrocookie/issues
.. _git-filter-repo: https://github.com/newren/git-filter-repo
.. _git rebase: https://git-scm.com/docs/git-rebase
.. _pip: https://pip.pypa.io/
.. _pygit2: https://github.com/libgit2/pygit2
.. github-only
.. _Contributor Guide: CONTRIBUTING.rst
