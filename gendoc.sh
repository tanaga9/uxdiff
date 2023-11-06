set -eu

CMD="
pip install \
sphinx~=6.2.1 sphinxcontrib-programoutput sphinx-argparse-cli sphinx-rst-builder ipython ipykernel nbconvert pandas .
jupyter nbconvert --execute --to notebook --inplace docs/example.ipynb
# jupyter nbconvert --to rst docs/example.ipynb
rm -r ./docs/_rst ./docs/_html
sphinx-build -b rst  ./docs ./docs/_rst
sphinx-build -b html ./docs ./docs/_html
cat ./docs/_rst/index.rst > README.rst
"

docker run --rm -it -w /work -v $PWD:/work python:3.10 /bin/sh -euc "$CMD"
