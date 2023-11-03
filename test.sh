set -eu
docker run --rm -it -w /work -v $PWD:/work python:3.10 /bin/sh -c 'pip install unidiff && python uxdiff.py --test && python uxdiff.py docs/text1.txt docs/text2.txt'
docker run --rm -it -w /work -v $PWD:/work python:2.7  /bin/sh -c 'pip install unidiff && python uxdiff.py --test && python uxdiff.py docs/text1.txt docs/text2.txt'
