cd docs
echo "Install Jupyter..."
pip install jupyter --quiet
echo "Build notebooks..."
python -m jupyter nbconvert --to html --execute examples.ipynb --log-level=CRITICAL > notebook_log.txt 2>&1
python -m jupyter nbconvert --to python --execute examples.ipynb --log-level=CRITICAL > notebook_log2.txt 2>&1
echo "Build Doxygen..."
doxygen Doxyfile > doxygen_log.txt 2>&1
cd ..
