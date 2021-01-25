Retrocookie
===========

|PyPI| |Python Version| |License|

|Read the Docs| |Tests| |Codecov|

|pre-commit| |Black|

.. |PyPI| image:: https://img.shields.io/pypi/v/retrocookie.svg
   :target: https://pypi.org/project/retrocookie/
   :alt: PyPI
.. |Python Version| image:: https://img.shields.io/pypi/pyversions/retrocookie
   :target: https://pypi.org/project/retrocookie
   :alt: Python Version
.. |License| image:: https://img.shields.io/pypi/l/retrocookie
   :target: https://opensource.org/licenses/MIT
   :alt: License
.. |Read the Docs| image:: https://img.shields.io/readthedocs/retrocookie/latest.svg?label=Read%20the%20Docs
   :target: https://retrocookie.readthedocs.io/
   :alt: Read the documentation at https://retrocookie.readthedocs.io/
.. |Tests| image:: https://github.com/cjolowicz/retrocookie/workflows/Tests/badge.svg
   :target: https://github.com/cjolowicz/retrocookie/actions?workflow=Tests
   :alt: Tests
.. |Codecov| image:: https://codecov.io/gh/cjolowicz/retrocookie/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/cjolowicz/retrocookie
   :alt: Codecov
.. |pre-commit| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit
.. |Black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Black


Retrocookie updates Cookiecutter_ templates with changes from generated projects.

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

**Important:**

Retrocookie relies on a ``.cookiecutter.json`` file in the generated project
to work out how to rewrite commits.
This file is similar to the ``cookiecutter.json`` file in the template,
but contains the specific values chosen during project generation.
You can generate this file by putting it into the template directory in the Cookiecutter,
with the following contents:

.. code:: jinja

   {{ cookiecutter | jsonify }}


Requirements
------------

* Python 3.7+
* git >= 2.22.0


Installation
------------

You can install *Retrocookie* via pip_ from PyPI_:

.. code:: console

   $ pip install retrocookie

Optionally, install the ``pr`` extra for the retrocookie-pr_ command:

.. code:: console

   $ pip install retrocookie[pr]


Example
-------

Here's an example to demonstrate the general workflow.

To start with, we clone the repository of your Cookiecutter template.
For this example, I'll use my own `Hypermodern Python Cookiecutter`_.

.. code:: console

   $ git clone https://github.com/cjolowicz/cookiecutter-hypermodern-python

Next, we'll create a project from the template,
and set up a git repository for it:

.. code:: console

   $ cookiecutter --no-input cookiecutter-hypermodern-python
   $ cd hypermodern-python
   $ git init
   $ git add .
   $ git commit --message="Initial commit"

Let's open a feature branch in the project repository,
and make a fictitious change involving the default project name *hypermodern-python*:

.. code:: console

   $ git switch --create add-example
   $ echo '# hypermodern-python' > EXAMPLE.md
   $ git add EXAMPLE.md
   $ git commit --message="Add example"

Back in the Cookiecutter repository,
we can now invoke retrocookie to import the changes from the feature branch:

.. code:: console

   $ cd ../cookiecutter-hypermodern-python
   $ retrocookie --branch add-example --create ../hypermodern-python

A ``git show`` in the Cookiecutter shows the file under the template directory,
on a branch named as in the original repository,
with the project name replaced by a Jinja tag:

.. code:: diff

   commit abb4f823b9f1760e3a678c927ec9797c0a40a9b6 (HEAD -> add-example)
   Author: Your Name <your.name@example.com>
   Date:   Fri Dec 4 23:40:41 2020 +0100

       Add example

   diff --git a/{{cookiecutter.project_name}}/EXAMPLE.md b/{{cookiecutter.project_name}}/EXAMPLE.md
   new file mode 100644
   index 0000000..a158618
   --- /dev/null
   +++ b/{{cookiecutter.project_name}}/EXAMPLE.md
   @@ -0,0 +1 @@
   +# {{cookiecutter.project_name}}


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

Please see the `Command-line Reference <Usage_>`_ for further details.


.. _retrocookie-pr:

Importing pull requests from generated projects with retrocookie-pr
-------------------------------------------------------------------

You can import pull requests from a generated project to the project template,
assuming their repositories are on GitHub_.
This requires activating the ``pr`` extra when installing with pip_:

.. code::

  $ pip install retrocookie[pr]

The command ``retrocookie-pr`` has the basic form:

.. code::

   $ retrocookie-pr [-R <repository>] [<pr>...]
   $ retrocookie-pr [-R <repository>] --user=<user>
   $ retrocookie-pr [-R <repository>] --all

Command-line arguments specify pull requests to import, by number or by branch.
Pull requests from forks are currently not supported.

Use the ``-R <repository>`` option to specify the GitHub repository of the generated project
from which the pull requests should be imported.
Provide the full name of the repository on GitHub in the form ``owner/name``.
The owner can be omitted if the repository is owned by the authenticated user.
This option can be omitted when the command is invoked from a local clone.

You can also select pull requests by specifying the user that opened them, via the ``--user`` option.
This is handy for importing automated pull requests, such as dependency updates from Dependabot_.

Use the ``--all`` option to import all open pull requests in the generated project.

You can update previously imported pull requests by specifying ``--force``.
By default, ``retrocookie-pr`` refuses to overwrite existing pull requests.

The command needs a `personal access token`_ to access the GitHub API.
(This token is also used to push to the GitHub repository of the project template.)
You will be prompted for the token when you invoke the command for the first time.
On subsequent invocations, the token is read from the application cache.
Alternatively, you can specify the token using the ``--token`` option or the ``GITHUB_TOKEN`` environment variable;
both of these methods bypass the cache.

Use the ``--open`` option to open each imported pull request in a web browser.

Please see the `Command-line Reference <Usage_>`_ for further details.


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
.. _Dependabot: https://dependabot.com/
.. _GitHub: https://github.com/
.. _Hypermodern Python Cookiecutter: https://github.com/cjolowicz/cookiecutter-hypermodern-python
.. _MIT: http://opensource.org/licenses/MIT
.. _PyPI: https://pypi.org/
.. _file an issue: https://github.com/cjolowicz/retrocookie/issues
.. _git-filter-repo: https://github.com/newren/git-filter-repo
.. _git rebase: https://git-scm.com/docs/git-rebase
.. _pip: https://pip.pypa.io/
.. _personal access token: https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/creating-a-personal-access-token
.. _pygit2: https://github.com/libgit2/pygit2
.. github-only
.. _Contributor Guide: CONTRIBUTING.rst
.. _Usage: https://retrocookie.readthedocs.io/en/latest/usage.html
