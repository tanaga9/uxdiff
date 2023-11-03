.. uxdiff documentation master file, created by
   sphinx-quickstart on Tue Oct 31 16:55:40 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=====================
uxdiff
=====================

Compares the two sequences well and outputs the difference

Overview
===========

Install
---------

.. code-block:: shell

   pip install uxdiff


Example
----------------

text1.txt

.. program-output:: cat text1.txt

text2.txt

.. program-output:: cat text2.txt

compare

.. code-block:: shell

   uxdiff text1.txt text2.txt --color never

.. program-output:: uxdiff text1.txt text2.txt --color never

supported multi-byte string. set the encoding with an argument if you need.

See more examples_

.. _examples: docs/example.ipynb


Usage
------

.. program-output:: uxdiff --help

License
--------------------

`The MIT License (MIT) <http://www.opensource.org/licenses/mit-license.php>`_


Module interface
==================================

.. automodule:: uxdiff
   :members: tabulate
.. autoclass:: uxdiff.Differ
   :members: compare
