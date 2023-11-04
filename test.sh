set -eu

CMD="pip install unidiff && python uxdiff.py --test && python uxdiff.py docs/text1.txt docs/text2.txt"

docker run --rm -it -w /work -v $PWD:/work python:3.11 /bin/sh -euc "$CMD"
docker run --rm -it -w /work -v $PWD:/work python:3.10 /bin/sh -euc "$CMD"
docker run --rm -it -w /work -v $PWD:/work python:3.9  /bin/sh -euc "$CMD"
docker run --rm -it -w /work -v $PWD:/work python:3.8  /bin/sh -euc "$CMD"
docker run --rm -it -w /work -v $PWD:/work python:3.7  /bin/sh -euc "$CMD"
docker run --rm -it -w /work -v $PWD:/work python:3.6  /bin/sh -euc "$CMD"
docker run --rm -it -w /work -v $PWD:/work python:3.5  /bin/sh -euc "$CMD"
docker run --rm -it -w /work -v $PWD:/work python:2.7  /bin/sh -euc "$CMD"
echo "----- success -----"
