docker run --rm -t -w /work -v $PWD:/work python:3.10 /bin/sh -c '
pip install \
sphinx~=6.2.1 sphinx-argparse sphinxcontrib-programoutput \
nbsphinx sphinx-rst-builder .
sphinx-build -b rst ./docs ./docs/_build
mv ./docs/_build/index.rst README.rst
'
