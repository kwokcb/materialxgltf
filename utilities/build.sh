# Install package
echo "Install package..."
python -m pip install --upgrade pip
pip install . --quiet
# Build examples
source utilities/build_docs.sh
# Build examples
source utilities/build_examples.sh
