docker run --rm -t -w /work -v $PWD:/work python:3.10 /bin/sh -c '
set -eu
pip install \
sphinx~=6.2.1 sphinxcontrib-programoutput sphinx-rst-builder .
# nbconvert
# jupyter nbconvert --to rst docs/example.ipynb
sphinx-build -b rst ./docs ./docs/_build
cat ./docs/_build/index.rst > README.rst
'
