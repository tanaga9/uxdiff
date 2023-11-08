.. uxdiff documentation master file, created by
   sphinx-quickstart on Tue Oct 31 16:55:40 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=====================
uxdiff
=====================

Compares the two sequences well and outputs the difference.
Improves text comparison in GUI-less environments.

Overview
===========

Install
---------

.. code-block:: shell

   pip install uxdiff


Example_
----------------

text1.txt

.. program-output:: cat text1.txt

text2.txt

.. program-output:: cat text2.txt

compare

.. code-block:: shell

   uxdiff text1.txt text2.txt

Automatically determine whether coloring is possible and display the difference in the best way.

.. program-output:: uxdiff text1.txt text2.txt

supported multi-byte string. set the encoding with an argument if you need.

See more Example_

.. _Example: https://tanaga9.github.io/uxdiff/example.html


Usage
------

.. sphinx_argparse_cli::
  :module: uxdiff
  :func: _make_argparser
  :prog: uxdiff
  :usage_width: 50


License
--------------------

`The MIT License (MIT) <http://www.opensource.org/licenses/mit-license.php>`_


Module interface
==================================

.. automodule:: uxdiff
   :members: tabulate
.. autoclass:: uxdiff.Differ
   :members: compare
.. autoclass:: uxdiff.LikeUnifiedDiffer
   :members: pretty_compare
.. autoclass:: uxdiff.SideBySideDiffer
   :members: pretty_compare
