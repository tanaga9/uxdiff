
udiff
========

Compares the two sequences well and outputs the difference


Install
---------

```
pip install git+https://github.com/tanaga9/udiff
```


Example
----------------

text1.txt

```
  1. Beautiful is better than ugly.
  2. Explicit is better than implicit.
  3. Simple is better than complex.
  4. Complex is better than complicated.
```

text2.txt

```
  1. Beautiful is better than ugly.
  3.   Simple is better than complex.
  4. Complicated is better than complex.
  5. Flat is better than nested.
```


`udiff text1.txt text2.txt --color never`

```
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

```

supported multi-byte string. set the encoding with an argument if you need.


License
--------------------

[`The MIT License (MIT)`](http://www.opensource.org/licenses/mit-license.php)
