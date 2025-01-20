## Build Utilities

- `build.sh` : Install package and build dependents. Generate package data.
- `build_docs` : Build Jupyter notebooks and run Doxygen to build documentation. Note that this will install the `jupyter` package from PyPi. Users can all install development dependencies using `pip install '.[dev]'` from the root folder.
- `build_examples` : Build example content. This is WIP.
- `build_dist` : Build  distribution in a top level `dist` folder. This can be used to deploy to `PyPi`. Only owners of this repository should deploy.

- `build_all` : Calls build, build_docs, and build_examples.