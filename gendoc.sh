docker run --rm -it -w /work -v $PWD:/work python:3.10 /bin/sh -c '
set -eu
pip install \
sphinx~=6.2.1 sphinxcontrib-programoutput sphinx-rst-builder ipython ipykernel nbconvert pandas .
jupyter nbconvert --execute --to notebook --inplace docs/example.ipynb
# jupyter nbconvert --to rst docs/example.ipynb
sphinx-build -b rst ./docs ./docs/_build
cat ./docs/_build/index.rst > README.rst
'
