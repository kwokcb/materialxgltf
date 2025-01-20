cd docs
echo "Install Jupyter..."
pip install jupyter --quiet
echo "Build notebooks..."
python -m jupyter execute --inplace examples.ipynb
python -m jupyter nbconvert --to html examples.ipynb 
python -m jupyter nbconvert --to python examples.ipynb 
echo "Build Doxygen..."
doxygen Doxyfile > doxygen_log.txt 2>&1
cd ..
