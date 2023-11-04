
uxdiff
******

Compares the two sequences well and outputs the difference.
Improves text comparison in GUI-less environments.


Overview
========


Install
-------

.. code-block:: shell

   pip install uxdiff


Example
-------

text1.txt

.. code-block:: text

     1. Beautiful is better than ugly.
     2. Explicit is better than implicit.
     3. Simple is better than complex.
     4. Complex is better than complicated.

text2.txt

.. code-block:: text

     1. Beautiful is better than ugly.
     3.   Simple is better than complex.
     4. Complicated is better than complex.
     5. Flat is better than nested.

compare

.. code-block:: shell

   uxdiff text1.txt text2.txt --color never

.. code-block:: text

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

See more `examples <https://github.com/tanaga9/uxdiff/blob/master/docs/example.ipynb>`_


Usage
-----

.. code-block:: text

   usage: uxdiff [-h] [--version] [-y] [-f] [-c NUM] [-w WIDTH] [-r]
                 [--linejunk LINEJUNK] [--charjunk CHARJUNK] [--cutoff RATIO]
                 [--fuzzy RATIO] [--cutoffchar] [--enc-file1 ENCODING]
                 [--enc-file2 ENCODING] [--enc-stdin ENCODING]
                 [--enc-stdout ENCODING] [--enc-filepath ENCODING]
                 [--ignore-crlf] [--color [WHEN]] [--no-color] [--withbg]
                 [file_or_dir_1] [file_or_dir_2]

   positional arguments:
     file_or_dir_1         file or dir 1
     file_or_dir_2         file or dir 2

   options:
     -h, --help            show this help message and exit
     --version             show program's version number and exit
     -y, -s, --side-by-side
                           output in two columns
     -f, --full            Fulltext diff (default False) (disable context option)
     -c NUM, --context NUM
                           Set number of context lines (default 5)
     -w WIDTH, --width WIDTH
                           Set number of width (default auto(or 130))
     -r, --recursive       Recursively compare any subdirectories found. (default
                           False) (enable only compare directories)
     --linejunk LINEJUNK   linejunk
     --charjunk CHARJUNK   charjunk
     --cutoff RATIO        Set number of cutoff ratio (default 0.75)
                           (0.0<=ratio<=1.0)
     --fuzzy RATIO         Set number of fuzzy matching ratio (default 0.0)
                           (0.0<=ratio<=1.0)
     --cutoffchar          Cutoff character in line diffs (default False)
     --enc-file1 ENCODING  Set encoding of leftside inputfile1 (default utf-8)
     --enc-file2 ENCODING  Set encoding of rightside inputfile2 (default utf-8)
     --enc-stdin ENCODING  Set encoding of standard input (default
                           `defaultencoding`)
     --enc-stdout ENCODING
                           Set encoding of standard output (default
                           `defaultencoding`)
     --enc-filepath ENCODING
                           Set encoding of filepath (default `defaultencoding`)
     --ignore-crlf         Ignore carriage return ('\r') and line feed ('\n')
                           (default False)
     --color [WHEN]        Show colored diff. --color is the same as
                           --color=always. WHEN can be one of always, never, or
                           auto. (default auto)
     --no-color            Turn off colored diff. override color option if both.
                           (default False)
     --withbg              Colored diff with background color. It will be ignored
                           if no-color option. (default False)


License
-------

`The MIT License (MIT) <http://www.opensource.org/licenses/mit-license.php>`_


Module interface
================

Compare two text files or directories (or sequences); generate the differences.

+-----------------+----------------------------+-------------------------------------+
| Environment     | Diff Representation        | target of the intended compare      |
+=================+============================+=====================================+
| ANSI terminal   | ANSI escape code (color)   | two text files or directories       |
+-----------------+----------------------------+-------------------------------------+
| Jupyter         | HTML Table                 | two sequences of hashable objects   |
+-----------------+----------------------------+-------------------------------------+

**uxdiff.tabulate(diffs, truncate=None)**

   Output the detected difference as an HTML table (for Jupyter).

**class uxdiff.Differ(linejunk=None, charjunk=None, cutoff=0.75, fuzzy=0.0, cutoffchar=False, context=3)**

   Differ is a class for comparing sequences.

   Differ uses SequenceMatcher both to compare sequences.

   **compare(seq1, seq2)**

      Compare two sequences; return a generator of differences.

      Requirement is

      * both sequences must be iterable (no generator).

      * items in a sequence must be (recursively) hashable.

      If the items of a sequences are iterable, detect similar ones as needed.

      * Examples of hashable and iterable object (containing only hashable objects)
           * string

           * bytes

           * tuple

           * namedtuple

           * …

      Example:

      >>> import pprint
      >>>
      >>> pprint.pprint(list(Differ().compare([
      ...    1, 2, 3, (4, 5), 6, 7, 8
      ... ], [
      ...    1, 2, 33, 4, 5, 6, 7, 8
      ... ])))
      [True,
       ((' ', 0, 1, 0, 1), None),
       ((' ', 1, 2, 1, 2), None),
       False,
       True,
       (('|', 2, 3, 2, 33), None),
       (('|', 3, (4, 5), 3, 4), None),
       (('>', None, None, 4, 5), None),
       False,
       True,
       ((' ', 4, 6, 5, 6), None),
       ((' ', 5, 7, 6, 7), None),
       ((' ', 6, 8, 7, 8), None),
       False]
      >>>
      >>> text1 = '''one
      ... two
      ... three
      ... '''.splitlines(1)
      >>>
      >>> text2 = '''ore
      ... tree
      ... emu
      ... '''.splitlines(1)
      >>>
      >>> pprint.pprint(list(Differ().compare(text1, text2)), width=100)
      [True,
       (('>', None, None, 0, 'ore\n'), None),
       (('<', 0, 'one\n', None, None), None),
       (('<', 1, 'two\n', None, None), None),
       (('|', 2, 'three\n', 1, 'tree\n'), [(' ', 't', 't'), ('-', 'h', None), (' ', 'ree\n', 'ree\n')]),
       (('>', None, None, 2, 'emu\n'), None),
       False]
      >>>
      >>> # like sdiff
      >>> pprint.pprint(list(Differ(cutoff=0, fuzzy=1).compare(text1, text2)), width=100)
      [True,
       (('|', 0, 'one\n', 0, 'ore\n'), [(' ', 'o', 'o'), ('!', 'n', 'r'), (' ', 'e\n', 'e\n')]),
       (('|', 1, 'two\n', 1, 'tree\n'), [(' ', 't', 't'), ('!', 'wo', 'ree'), (' ', '\n', '\n')]),
       (('|', 2, 'three\n', 2, 'emu\n'),
        [('-', 'thr', None), (' ', 'e', 'e'), ('!', 'e', 'mu'), (' ', '\n', '\n')]),
       False]
      >>>
      >>> text1 = '''  1. Beautiful is better than ugly.
      ...   2. Explicit is better than implicit.
      ...   3. Simple is better than complex.
      ...   4. Complex is better than complicated.
      ... '''.splitlines(1)
      >>>
      >>> text2 = '''  1. Beautiful is better than ugly.
      ...   3.   Simple is better than complex.
      ...   4. Complicated is better than complex.
      ...   5. Flat is better than nested.
      ... '''.splitlines(1)
      >>>
      >>> diff = Differ().compare(text1, text2)
      >>> pprint.pprint(list(diff), width=120)
      [True,
       ((' ', 0, '  1. Beautiful is better than ugly.\n', 0, '  1. Beautiful is better than ugly.\n'), None),
       False,
       True,
       (('<', 1, '  2. Explicit is better than implicit.\n', None, None), None),
       (('|', 2, '  3. Simple is better than complex.\n', 1, '  3.   Simple is better than complex.\n'),
        [(' ', '  3.', '  3.'),
         ('+', None, '  '),
         (' ', ' Simple is better than complex.\n', ' Simple is better than complex.\n')]),
       (('|', 3, '  4. Complex is better than complicated.\n', 2, '  4. Complicated is better than complex.\n'),
        [(' ', '  4. Compl', '  4. Compl'),
         ('+', None, 'icat'),
         (' ', 'e', 'e'),
         ('!', 'x', 'd'),
         (' ', ' is better than compl', ' is better than compl'),
         ('-', 'icat', None),
         (' ', 'e', 'e'),
         ('!', 'd', 'x'),
         (' ', '.\n', '.\n')]),
       (('>', None, None, 3, '  5. Flat is better than nested.\n'), None),
       False]

      +--------------+----------------------------------------------------------------------------------------------+
      | Yields       | Meaning                                                                                      |
      +==============+==============================================================================================+
      | True         | begin of a group of diff                                                                     |
      +--------------+----------------------------------------------------------------------------------------------+
      | False        | end of a group of diff                                                                       |
      +--------------+----------------------------------------------------------------------------------------------+
      | None         | omitted matches beyond the number of contexts                                                |
      +--------------+----------------------------------------------------------------------------------------------+
      | Tuple        | ((Code, Index1 | None, Item1 | None, Index2 | None, Item2 | None), InlineDiff | None)        |
      +--------------+----------------------------------------------------------------------------------------------+

      +--------------+--------------------------------------+
      | Code         | Meaning                              |
      +==============+======================================+
      | “<”          | unique to sequence 1                 |
      +--------------+--------------------------------------+
      | “>”          | unique to sequence 2                 |
      +--------------+--------------------------------------+
      | “ “          | common to both sequences             |
      +--------------+--------------------------------------+
      | “|”          | different to both sequences          |
      +--------------+--------------------------------------+

      +--------------+----------------------------------------------------------------------+
      | InlineDiff   | Meaning                                                              |
      +==============+======================================================================+
      | None         | There is no InlineDiff (Code is not “|” or items are not iterable)   |
      +--------------+----------------------------------------------------------------------+
      | List         | [(InlineCode, SlicedItem1 | None, SlicedItem2 | None), … ]           |
      +--------------+----------------------------------------------------------------------+

      +--------------+--------------------------------------------------------+
      | InlineCode   | Meaning                                                |
      +==============+========================================================+
      | “-”          | unique to inline sequence 1 (item of sequence 1)       |
      +--------------+--------------------------------------------------------+
      | “+”          | unique to inline sequence 2 (item of sequence 2)       |
      +--------------+--------------------------------------------------------+
      | “ “          | common to both inline sequences                        |
      +--------------+--------------------------------------------------------+
      | “!”          | different to both inline sequences                     |
      +--------------+--------------------------------------------------------+

**class uxdiff.UniLikeDiffer(*args, **kwargs)**

   **pretty_compare(lines1, lines2, width=130, withcolor=False, offset1=0, offset2=0)**

      Compare two sequences of string; return a generator of pretty difference representations.

**class uxdiff.SidebysideDiffer(*args, **kwargs)**

   **pretty_compare(lines1, lines2, width=130, withcolor=False, offset1=0, offset2=0)**

      Compare two sequences of string; return a generator of pretty difference representations.
