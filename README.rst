
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


Retrocookie imports commits from a Cookiecutter_ instance into the template.

When developing Cookiecutter templates,
you often need to work in a generated project rather than the template itself.
Reasons for this include the following:

- You need to run the Continuous Integration suite for the generated project
- Your development tools choke when running on the templated project

Any changes you make in the generated project
need to be backported into the template,
carefully replacing expanded variables from ``cookiecutter.json`` by templating tags,
and escaping any use of ``{{`` and ``}}``.

Retrocookie helps you in this situation.

It is designed to fetch commits from the repository of a generated project,
and import them onto a feature branch in your Cookiecutter repository,
rewriting them on the fly to insert templating tags
and escape Jinja-special constructs.

Invoke retrocookie with the name of a branch via the ``--ref`` option,
and it will fetch the commits on that branch from the project,
rewrite them, and cherry-pick them onto an equally-named branch in the Cookiecutter.

If the repository of the generated project has a URL or path
like the Cookiecutter, with ``-instance`` appended,
you're already good to go.
Otherwise, pass the location of the generated project via the ``--url`` option.

Under the hood,
Retrocookie clones the generated project to a temporary directory
and rewrites the clone using git-filter-repo_.
It then fetches the rewritten branch into the template,
and uses `git rebase`_ to copy the commits onto a new branch,
off your current branch.

Maybe you're thinking,
how can this possibly work?
Rewriting a generated project as a project template is
like replacing the output of a program by its code.
And you're right.
But while the general problem of reconstructing the template code is unsolvable,
in practise it is often enough to perform simple replacements of template variables.
One reason this works so well is that
the rewrite only needs to be correct for the handful of commits you're importing.

When it doesn't work,
you will usually get merge conflicts,
with the entire git machinery at your fingertips.
Use ``git rebase --abort`` to bail out into a clean state,
or resolve the conflicts and run ``git rebase --continue``.
Even if there are no merge conflicts,
always inspect the generated commits to make sure you got what you wanted.


Features
--------

* Import commits from a Cookiecutter instance into the template


Requirements
------------

* Python 3.6+
* git >= 2.22.0


Installation
------------

You can install *Retrocookie* via pip_ from PyPI_:

.. code:: console

   $ pip install retrocookie


Usage
-----

Use Retrocookie like this:

.. code:: console

   $ retrocookie -r <branch>


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
.. github-only
.. _Contributor Guide: CONTRIBUTING.rst
