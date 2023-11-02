.. uxdiff documentation master file, created by
   sphinx-quickstart on Tue Oct 31 16:55:40 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=====================
uxdiff
=====================

Compares the two sequences well and outputs the difference

overview
===========

Install
---------

.. code-block:: shell

   pip install uxdiff


Example
----------------

text1.txt

.. code-block::

   1. Beautiful is better than ugly.
   2. Explicit is better than implicit.
   3. Simple is better than complex.
   4. Complex is better than complicated.

text2.txt

.. code-block::

   1. Beautiful is better than ugly.
   2.   Simple is better than complex.
   3. Complicated is better than complex.
   4. Flat is better than nested.

compare

.. code-block:: shell

   uxdiff text1.txt text2.txt --color never

.. code-block::

   --- text1.txt (utf-8)
   +++ text2.txt (utf-8)
        1      1|     1. Beautiful is better than ugly.
        2       | -   2. Explicit is better than implicit.
        3       | -   3. Simple is better than complex.
        4       | -   4. Complex is better than complicated.
               2| +   3.   Simple is better than complex.
               3| +   4. Complicated is better than complex.
               4| +   5. Flat is better than nested.
   
   [     ]      |    ++                                
   [ <-  ]     3|  3.   Simple is better than complex. 
   [  -> ]     2|  3.   Simple is better than complex. 
   
   [     ]      |          ++++ !                     ---- !  
   [ <-  ]     4|  4. Compl    ex is better than complicated. 
   [  -> ]     3|  4. Complicated is better than compl    ex. 


supported multi-byte string. set the encoding with an argument if you need.

See more examples_

.. _examples: examples


Usage
------

.. program-output:: uxdiff --help


License
--------------------

`The MIT License (MIT) <http://www.opensource.org/licenses/mit-license.php>`_


..
   Command-line interface
   ==================================
   
   .. argparse::
      :module: uxdiff
      :func: make_argparser
      :prog: uxdiff


Module interface
==================================
..
   .. automodule:: uxdiff
.. autoclass:: uxdiff.Differ
   :members: compare
