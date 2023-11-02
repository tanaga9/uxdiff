
uxdiff
******

Compares the two sequences well and outputs the difference


overview
========


Install
-------

.. code-block:: shell

   pip install uxdiff


Example
-------

text1.txt

::

   1. Beautiful is better than ugly.
   2. Explicit is better than implicit.
   3. Simple is better than complex.
   4. Complex is better than complicated.

text2.txt

::

   1. Beautiful is better than ugly.
   2.   Simple is better than complex.
   3. Complicated is better than complex.
   4. Flat is better than nested.

compare

.. code-block:: shell

   uxdiff text1.txt text2.txt --color never

::

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

See more `examples <examples>`_


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

**class uxdiff.Differ(linejunk=None, charjunk=None, cutoff=0.75, fuzzy=0.0, cutoffchar=False, context=3)**

   Bases: ``object``

   Differ is a class for comparing sequences.

   Differ uses SequenceMatcher both to compare sequences.

   **begin_textdiffs()**

   **compare(seq1, seq2)**

      Compare two sequences; return a generator of differences.

      Requirement is

      * both arguments are iterable.

      * items in a sequences must be hashable.

      If the items of a sequences are iterable, detect similar ones as needed.

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
       False,
       None]
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
       False,
       None]
      >>>
      >>> # like sdiff
      >>> pprint.pprint(list(Differ(cutoff=0, fuzzy=1).compare(text1, text2)), width=100)
      [True,
       (('|', 0, 'one\n', 0, 'ore\n'), [(' ', 'o', 'o'), ('!', 'n', 'r'), (' ', 'e\n', 'e\n')]),
       (('|', 1, 'two\n', 1, 'tree\n'), [(' ', 't', 't'), ('!', 'wo', 'ree'), (' ', '\n', '\n')]),
       (('|', 2, 'three\n', 2, 'emu\n'),
        [('-', 'thr', None), (' ', 'e', 'e'), ('!', 'e', 'mu'), (' ', '\n', '\n')]),
       False,
       None]
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
       False,
       None]

      +--------------+----------------------------------------------------------------------------------------------+
      | Yields       | Meaning                                                                                      |
      +==============+==============================================================================================+
      | True         | begin of a group of diff                                                                     |
      +--------------+----------------------------------------------------------------------------------------------+
      | False        | end of a group of diff                                                                       |
      +--------------+----------------------------------------------------------------------------------------------+
      | None         | context separator                                                                            |
      +--------------+----------------------------------------------------------------------------------------------+
      | Tuple        | ((Code, LineNum1 | None, Line1 | None, LineNum2 | None, Line2 | None),  InlineDiff | None)   |
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

      +--------------+----------------------------------------------------------------+
      | InlineDiff   | Meaning                                                        |
      +==============+================================================================+
      | None         | There is no InlineDiff (Code is not “|”)                       |
      +--------------+----------------------------------------------------------------+
      | List         | [(InlineCode, InlineItem1 | None, InlineItem2 | None), … ]     |
      +--------------+----------------------------------------------------------------+

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

   **end_textdiffs()**

   **formatlinetext(num1, num2, linediff, width, withcolor=False)**

   **formattext(tag, num1, text1, num2, text2, width, withcolor=False, linediff=None)**

   **pretty_compare(lines1, lines2, width, withcolor=False, offset1=0, offset2=0)**

   **textdiffs()**

   **textlinediffs()**

**class uxdiff.SidebysideDiffer(*args, **kwargs)**

   Bases: ``Differ``

   **begin_textdiffs()**

   **end_textdiffs()**

   **formatlinetext(num1, num2, linediff, width, withcolor=False)**

      Example:

      >>> import pprint
      >>> differ = SidebysideDiffer()
      >>> differ.formatlinetext(
      ...     1, 2,
      ...     [('!', 'bbb', 'aaaaa'),
      ...      (' ', 'cc', 'cc'),
      ...      ('+', None, 'dd'),
      ...      ('-', 'ee', None)], 80)
      >>> pprint.pprint(list(differ.textlinediffs()))
      ['',
       '[     ]      |!!!++  ++--',
       '[ <-  ]     2|bbb  cc  ee',
       '[  -> ]     3|aaaaaccdd  ',
       '']

   **formattext(tag, num1, text1, num2, text2, width, withcolor=False, linediff=None)**

      Example:

      >>> differ = SidebysideDiffer()
      >>> differ.formattext('|', 1, 'aaa', 2, 'bbb', 80)
      >>> list(differ.textdiffs())
      ['     2|aaa                             |      3|bbb']

      >>> differ.formattext('|', 1, 'aaa', 2, 'bbb', 60)
      >>> list(differ.textdiffs())
      ['     2|aaa                   |      3|bbb']

      >>> differ.formattext(' ', 1, 'aaa', 2, 'aaa', 80)
      >>> list(differ.textdiffs())
      ['     2|aaa                                    3|aaa']

      >>> differ.formattext('<', 1, 'aaa', None, None, 80)
      >>> list(differ.textdiffs())
      ['     2|aaa                             <       |']

      >>> differ.formattext('>', None, None, 2, 'bbb', 80)
      >>> list(differ.textdiffs())
      ['      |                                >      3|bbb']

      >>> import pprint
      >>> differ.formattext(
      ...     '>',
      ...     1, 'a' * 60,
      ...     2, 'b' * 20, 60)
      >>> pprint.pprint(list(differ.textdiffs()))
      ['     2|aaaaaaaaaaaaaaaaaaaaa >      3|bbbbbbbbbbbbbbbbbbbb',
       '     ^|aaaaaaaaaaaaaaaaaaaaa ^       |',
       '     ^|aaaaaaaaaaaaaaaaaa    ^       |']

   **textdiffs()**

   **textlinediffs()**

**class uxdiff.UniLikeDiffer(*args, **kwargs)**

   Bases: ``SidebysideDiffer``

   **end_textdiffs()**

   **formattext(tag, num1, text1, num2, text2, width, withcolor=False, linediff=None)**

      Example:

      >>> differ = SidebysideDiffer()
      >>> differ.formattext('|', 1, 'aaa', 2, 'bbb', 80)
      >>> list(differ.textdiffs())
      ['     2|aaa                             |      3|bbb']

      >>> differ.formattext('|', 1, 'aaa', 2, 'bbb', 60)
      >>> list(differ.textdiffs())
      ['     2|aaa                   |      3|bbb']

      >>> differ.formattext(' ', 1, 'aaa', 2, 'aaa', 80)
      >>> list(differ.textdiffs())
      ['     2|aaa                                    3|aaa']

      >>> differ.formattext('<', 1, 'aaa', None, None, 80)
      >>> list(differ.textdiffs())
      ['     2|aaa                             <       |']

      >>> differ.formattext('>', None, None, 2, 'bbb', 80)
      >>> list(differ.textdiffs())
      ['      |                                >      3|bbb']

      >>> import pprint
      >>> differ.formattext(
      ...     '>',
      ...     1, 'a' * 60,
      ...     2, 'b' * 20, 60)
      >>> pprint.pprint(list(differ.textdiffs()))
      ['     2|aaaaaaaaaaaaaaaaaaaaa >      3|bbbbbbbbbbbbbbbbbbbb',
       '     ^|aaaaaaaaaaaaaaaaaaaaa ^       |',
       '     ^|aaaaaaaaaaaaaaaaaa    ^       |']

**uxdiff.dircmp(dir1, dir2, enc_filepath='utf-8', recursive=False)**

   Compare directories.

**uxdiff.expandtabs(text, tabsize=8, expandto='\t')**

   Expand tabs(supports multibytes chars)

   Example:

   >>> expandtabs('text')
   'text'

   >>> expandtabs('\ta\tab\tend')
   '\t\t\t\t\t\t\t\ta\t\t\t\t\t\t\tab\t\t\t\t\t\tend'

   >>> expandtabs('abcdabc\tabcdabcd\tabcdabcda\tend')
   'abcdabc\tabcdabcd\t\t\t\t\t\t\t\tabcdabcda\t\t\t\t\t\t\tend'

   >>> expandtabs('\ta\tab\tabc\tabcd\tend', tabsize=4, expandto='@')
   '@@@@a@@@ab@@abc@abcd@@@@end'

**class uxdiff.ext_dircmp(a, b, ignore=None, hide=None)**

   Bases: ``dircmp``

   **dirtree()**

   **phase1()**

   **phase2()**

   **phase3()**

   **phase4()**

**uxdiff.formatdircmp(tag, head1, text1, head2, text2, width, cont_mark1='^', cont_mark2='^', sep_mark='|', withcolor=False)**

**uxdiff.getTerminalSize()**

**uxdiff.getcolor(withcolor, tag, side, openclose, isdircmp=False, withbg=None)**

**uxdiff.getdefaultencoding()**

**uxdiff.is_text(filepath)**

**uxdiff.main()**

   main function

**uxdiff.make_argparser()**

**uxdiff.original_diff(differ, lines1, lines2, width, withcolor=False)**

   Example:

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
   >>> differ = SidebysideDiffer(
   ...     linejunk=None,
   ...     charjunk=None,
   ...     cutoff=0.1,
   ...     fuzzy=0,
   ...     cutoffchar=False,
   ...     context=5)
   >>> diff = original_diff(differ, text1, text2, width=100)
   >>> for line in diff: print('\'' + line + '\'')
   '     1|  1. Beautiful is better than ugly.              1|  1. Beautiful is better than ugly.'
   '     2|  2. Explicit is better than implicit.    <       |'
   '     3|  3. Simple is better than complex.       |      2|  3.   Simple is better than complex.'
   '     4|  4. Complex is better than complicated.  |      3|  4. Complicated is better than complex.'
   '      |                                          >      4|  5. Flat is better than nested.'
   ''
   '[     ]      |    ++                                '
   '[ <-  ]     3|  3.   Simple is better than complex. '
   '[  -> ]     2|  3.   Simple is better than complex. '
   ''
   '[     ]      |          ++++ !                     ---- !  '
   '[ <-  ]     4|  4. Compl    ex is better than complicated. '
   '[  -> ]     3|  4. Complicated is better than compl    ex. '
   ''

**uxdiff.parse_unidiff(diff)**

   Unified diff parser, takes a file-like object as argument.

   Example:

   >>> hg_diff = r'''diff -r dab26450e4b1 text2.txt
   ... --- a/text2.txt     Sun Dec 15 17:38:49 2013 +0900
   ... +++ b/text2.txt     Sun Dec 15 17:43:09 2013 +0900
   ... @@ -1,3 +1,3 @@
   ... -hoge
   ... +hogee
   ... +bar
   ...  foo
   ... -bar
   ... '''
   >>> diffs = parse_unidiff((line for line in hg_diff.splitlines()))
   >>> for (flag, diff) in diffs:
   ...     if flag: print(diff)
   ...     else:
   ...         for hunk in diff:
   ...             import pprint
   ...             pprint.pprint([s[1:] for s in hunk.source])
   ...             pprint.pprint([s[1:] for s in hunk.target])
   ...
   diff -r dab26450e4b1 text2.txt
   --- a/text2.txt     Sun Dec 15 17:38:49 2013 +0900
   +++ b/text2.txt     Sun Dec 15 17:43:09 2013 +0900
   ['hoge', 'foo', 'bar']
   ['hogee', 'bar', 'foo']
   >>>

**uxdiff.parse_unidiff_and_original_diff(differ, udiffs, width, withcolor=False)**

   Example:

   >>> svn_diff = u'''Index: some.png
   ... ===================================================================
   ... Cannot display: file marked as a binary type.
   ... svn:mime-type = application/octet-stream
   ... Index: text1.txt
   ... ===================================================================
   ... --- text1.txt       (revision 1)
   ... +++ text1.txt       (working copy)
   ... @@ -1,4 +1,4 @@
   ...  1. Beautiful is better than ugly.
   ... -2. Explicit is better than implicit.
   ... -3. Simple is better than complex.
   ... -4. Complex is better than complicated.
   ... +3.   Simple is better than complex.
   ... +4. Complicated is better than complex.
   ... +5. Flat is better than nested.
   ... '''
   >>> differ = SidebysideDiffer(
   ...     linejunk=None, charjunk=None,
   ...     cutoff=0.1, fuzzy=0,
   ...     cutoffchar=False, context=5)
   >>> diff = parse_unidiff_and_original_diff(
   ...     differ,
   ...     (line for line in svn_diff.splitlines()),
   ...     width=100)
   >>> for line in diff: print('\'' + line + '\'')
   'Index: some.png'
   '==================================================================='
   'Cannot display: file marked as a binary type.'
   'svn:mime-type = application/octet-stream'
   'Index: text1.txt'
   '==================================================================='
   '--- text1.txt       (revision 1)'
   '+++ text1.txt       (working copy)'
   '     1|1. Beautiful is better than ugly.                1|1. Beautiful is better than ugly.'
   '     2|2. Explicit is better than implicit.      <       |'
   '     3|3. Simple is better than complex.         |      2|3.   Simple is better than complex.'
   '     4|4. Complex is better than complicated.    |      3|4. Complicated is better than complex.'
   '      |                                          >      4|5. Flat is better than nested.'
   ''
   '[     ]      |  ++                               '
   '[ <-  ]     3|3.   Simple is better than complex.'
   '[  -> ]     2|3.   Simple is better than complex.'
   ''
   '[     ]      |        ++++ !                     ---- ! '
   '[ <-  ]     4|4. Compl    ex is better than complicated.'
   '[  -> ]     3|4. Complicated is better than compl    ex.'
   ''
   >>>
   >>> hg_diff = u'''diff -r dab26450e4b1 some.png
   ... Binary file some.png has changed
   ... diff -r dab26450e4b1 text1.txt
   ... --- a/text1.txt     Sun Dec 15 17:38:49 2013 +0900
   ... +++ b/text1.txt     Sun Dec 15 17:43:09 2013 +0900
   ... @@ -1,4 +1,4 @@
   ...  1. Beautiful is better than ugly.
   ... -2. Explicit is better than implicit.
   ... -3. Simple is better than complex.
   ... -4. Complex is better than complicated.
   ... +3.   Simple is better than complex.
   ... +4. Complicated is better than complex.
   ... +5. Flat is better than nested.
   ... '''
   >>> differ = SidebysideDiffer(
   ...     linejunk=None, charjunk=None,
   ...     cutoff=0.1, fuzzy=0,
   ...     cutoffchar=False, context=5)
   >>> diff = parse_unidiff_and_original_diff(
   ...     differ,
   ...     (line for line in hg_diff.splitlines()),
   ...     width=100)
   >>> for line in diff: print('\'' + line + '\'')
   'diff -r dab26450e4b1 some.png'
   'Binary file some.png has changed'
   'diff -r dab26450e4b1 text1.txt'
   '--- a/text1.txt     Sun Dec 15 17:38:49 2013 +0900'
   '+++ b/text1.txt     Sun Dec 15 17:43:09 2013 +0900'
   '     1|1. Beautiful is better than ugly.                1|1. Beautiful is better than ugly.'
   '     2|2. Explicit is better than implicit.      <       |'
   '     3|3. Simple is better than complex.         |      2|3.   Simple is better than complex.'
   '     4|4. Complex is better than complicated.    |      3|4. Complicated is better than complex.'
   '      |                                          >      4|5. Flat is better than nested.'
   ''
   '[     ]      |  ++                               '
   '[ <-  ]     3|3.   Simple is better than complex.'
   '[  -> ]     2|3.   Simple is better than complex.'
   ''
   '[     ]      |        ++++ !                     ---- ! '
   '[ <-  ]     4|4. Compl    ex is better than complicated.'
   '[  -> ]     3|4. Complicated is better than compl    ex.'
   ''
   >>>

**uxdiff.strwidth(text, ambiguous_wide=True)**

   A function to give back the width (a character width) of string.

   Unit of width is one ASCII displayed by a monospaced font
   (This function is for environment using a wide character for)

   Example:

   >>> strwidth('teststring')
   10

**uxdiff.strwidthdiv(text, width=180)**

   divide string by appointed width

   Example:

   >>> strwidthdiv('teststring', 2)
   ['te', 'st', 'st', 'ri', 'ng']

   >>> strwidthdiv('teststring', 3)
   ['tes', 'tst', 'rin', 'g']

   >>> strwidthdiv('teststring', 8)
   ['teststri', 'ng']

   >>> strwidthdiv('teststring', 15)
   ['teststring']

**uxdiff.strwidthdivsync(textarray, width=180)**

   synclonize divide some string by appointed width

   Example:

   >>> strwidthdivsync(('test', 'string', ''), width=2)
   [['te', 'st', ''], ['st', 'ri', 'ng'], ['', '', '']]

   >>> strwidthdivsync(('test', 'string', ''), width=3)
   [['tes', 't'], ['str', 'ing'], ['', '']]

**uxdiff.uxdiff(args, parser)**
