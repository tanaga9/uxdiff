set -eu

CMD="
sudo apt-get update && sudo apt-get install -y pandoc
pip install \
sphinx~=6.2.1 sphinxcontrib-programoutput sphinx-argparse-cli nbsphinx sphinx-rst-builder ipython ipykernel nbconvert pandas .
jupyter nbconvert --execute --to notebook --inplace docs/example.ipynb
# jupyter nbconvert --to rst docs/example.ipynb
rm -rf ./docs/_rst ./docs/_html
BUILD=rst  sphinx-build -b rst  ./docs ./docs/_rst --keep-going
BUILD=html sphinx-build -b html ./docs ./docs/_html
cat ./docs/_rst/index.rst | perl -pe 's/\*\*\`\`(.*?)\`\`\*\*/\`\`\1\`\`/g' > README.rst
"
if [ $1 = "workflow" ]; then
  /bin/sh -euc "$CMD"
else
  docker run --rm -it -w /work -v $PWD:/work python:3.10 /bin/sh -euc "$CMD"
fi
