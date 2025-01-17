# materialxgltf

## Contents

- [Introduction](#Introduction)
- [Installation](#installation)
- [Usage](#usage)
- [Documentation](#documentation)
- [Build](#build)

## Introduction

This package supports the bi-directional translation between MaterialX materials and glTF materials. The minimum version of MaterialX required is 1.38.9 and the target glTF version is 2.0.1.  The current package is synced with MaterialX release 1.39.

See the [home page](https://kwokcb.github.io/materialxgltf/) for this project.

Below is an example of converting the "Sci Fi Helmet" asset (found in the **[glTF Sample Model repository](https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/SciFiHelmet)**) to MaterialX and previewing.
<!-- 
<img src="https://github.com/kwokcb/glTF_MaterialX/raw/main/docs/gltf_import-graphEditor2.png" width="80%"> -->
<img src="https://kwokcb.github.io/materialxgltf/docs/images/SciFiHelmet_graph.png" alt="SciFiLeHelmet" width="100%">

The functionality found here is equivalent to the C++ module available in
**[this repository](https://github.com/kwokcb/glTF_MaterialX)**. Note that additional documentation can be found on that site. 

## Installation

The minimum version of Python is assumed to be 3.9 and has been tested up to 3.11.

The package hosted on **[PyPi](https://pypi.org/project/materialxgltf/)** can be installed using `pip`:

```bash
pip install materialxgltf
```

or the **[source repository](https://github.com/kwokcb/materialxgltf)** can be cloned and the package built from the command line:

```bash
py -m build
```

This will build a distribution folder called `dist` which contains a zip file which can be installed using:

```bash
pip --install <name of zip>
```

### Requirements

Requires the installation of the following packages:

* `materialx` version 1.39 or higher: For MaterialX support.
* `pygltflib` : For conversion from `glTF` to `glb` including packaging dependent geometry and image resources.


## Documentation

### Command Line Utilities

The package provides basic command line utilities for converting between glTF and MaterialX. These can be found by running the module:

```bash
python -m materialxgltf -h
```
which will result in the following output:

```bash
Usage: python -m materialxgltf <command> [options] where command is mtlx2gltf or gltf2mtlx
```

Querying for help for each command will provide more detailed information:

#### glTF to MaterialX Conversion

```bash
python -m materialxgltf gltf2mtlx -h
```

```bash
usage: gltf2mtlx.py [-h] [--mtlxFileName MTLXFILENAME] [--createAssignments CREATEASSIGNMENTS] [--addAllInputs ADDALLINPUTS] gltfFileName

Utility to convert a glTF file to MaterialX file

positional arguments:
  gltfFileName          Path containing glTF file to convert.

options:
  -h, --help            show this help message and exit
  --mtlxFileName MTLXFILENAME
                        Name of MaterialX output file. If not specified the glTF name with "_tomtlx.mtlx" suffix will be used
  --createAssignments CREATEASSIGNMENTS
                        Create material assignments. Default is True
  --addAllInputs ADDALLINPUTS
                        Add all definition inputs to MaterialX shader nodes. Default is False
```

#### MaterialX to glTF Conversion

```bash
python -m materialxgltf mtlx2gltf -h
```

```bash
usage: mtlx2gltf.py [-h] [--gltfFileName GLTFFILENAME] [--gltfGeomFileName GLTFGEOMFILENAME] [--primsPerMaterial PRIMSPERMATERIAL] [--packageBinary PACKAGEBINARY] [--translateShaders TRANSLATESHADERS] [--bakeTextures BAKETEXTURES][--bakeResolution BAKERESOLUTION] [--writeDefaultInputs WRITEDEFAULTINPUTS]
 mtlxFileName

Utility to convert a MaterialX file to a glTF file

positional arguments:
  mtlxFileName          Path containing MaterialX file to convert.

options:
  -h, --help            show this help message and exit
  --gltfFileName GLTFFILENAME
                        Name of MaterialX output file. If not specified the glTF name with "_tomtlx.mtlx" suffix will be used
  --gltfGeomFileName GLTFGEOMFILENAME
                        Name of MaterialX output file. If not specified the glTF name with "_tomtlx.mtlx" suffix will be used
  --primsPerMaterial PRIMSPERMATERIAL
                        Create a new primitive per material and assign the material. Default is False
  --packageBinary PACKAGEBINARY
                        Create a biary packaged GLB file. Default is False
  --translateShaders TRANSLATESHADERS
                        Translate shaders to glTF. Default is False
  --bakeTextures BAKETEXTURES
                        Bake pattern graphs as textures. Default is False
  --bakeResolution BAKERESOLUTION
                        Bake image resolution. Default is 256
  --writeDefaultInputs WRITEDEFAULTINPUTS
                        Write default inputs on shader nodes. Default is False
```

For more detailed information about the workflow this package supports, please refer to this **[documentation](https://kwokcb.github.io/MaterialX_Learn/documents/workflow_gltf.html)**.

For API usage, refer to **[this documentation](https://kwokcb.github.io/materialxgltf/docs/html)**.

## Usage

<script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.js"></script>

<model-viewer style='background-color:rgba(0, 0, 0, 1.0); width: 48em; height: 48em' id='viewer1' ar interaction-prompt='none' camera-controls touch-action='pan-y' src='./docs/data/BoomBoxWithAxes_primMaterials.glb' shadow-intensity='0.3' alt='BoomBox With Axes Per Prim Material' poster='./docs/data/BoomBoxWithAxes_primMaterials.png'></model-viewer>

The following shows is a set of progressive examples to convert from a glTF file to MaterialX and then to a new glTF file for "shader ball" preview of
extracted materials.

Note that the sample data is included as part of the package for convenience.

The sample input file is the "BoomBox with Axes" file from the glTF https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/sitory found **[here](https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/BoomBoxWithAxes/glTF)**.

<img src="https://github.com/KhronosGroup/glTF-Sample-Assets/blob/main/Models/BoomBoxWithAxes/screenshot/screenshot_large.jpg?raw=true" width=30%>

This is converted from glTF to a MaterialX document which can be previewed / modified using an integration which supports MaterialX. Here the file is loaded into the a graph editor

<img src="https://kwokcb.github.io/materialxgltf/docs/images/BoomBox_graph.png" alt="Graph Editor Snapshot" width="100%">


The converted materials are then used to create a new glTF file using sample "shaderball" data with each material found assigned to different instances of the "shaderball"

<img src="https://raw.githubusercontent.com/kwokcb/MaterialX_Learn/main/documents/images/mtlx_to_gltf_materialviewer.png" alt="VSCode Snapshot"
width="50%">

## Interactive Example

A `Jupyter` notebook which performs the same steps is available **[here](https://kwokcb.github.io/materialxgltf/docs/examples.html)**.

This or any other notebook can be used if the user wishes to test the package in an interactive environment.

### Import the package

```python
import materialxgltf.core as core
```

### Check Available Sample Data

```python
import pkg_resources

directory_name = "data"  
files = pkg_resources.resource_listdir('materialxgltf', directory_name)
for file in files:
    print('Data file: ', file)
```

### Convert from glTF to MaterialX
```python
import pkg_resources
import MaterialX as mx

gltfFileName = pkg_resources.resource_filename('materialxgltf', 'data/BoomBoxWithAxes.gltf')
print(gltfFileName)

# Instantiate a the reader class. Read in sample  glTF file
# and output a MaterialX document
gltf2MtlxReader = core.GLTF2MtlxReader()
doc = gltf2MtlxReader.convert(gltfFileName)
if not doc:
    print('Existing due to error')
else:
    status, err = doc.validate()
    if not status:
        print('Generated MaterialX document has validation errors: ', err)
    else:
        print('Generated MaterialX document is valid')

# Write the document to a string
print('Resulting MaterialX document:\n')
result = core.Util.writeMaterialXDocString(doc)
print(result)
```

### Using glTF to MaterialX Options

```python
# Set option to write material assignments
options = core.GLTF2MtlxOptions()
options['createAssignments'] = True
gltf2MtlxReader.setOptions(options)

doc = gltf2MtlxReader.convert(gltfFileName)
if not doc:
    print('Existing due to error')
else:
    status, err = doc.validate()
    if not status:
        print('Generated MaterialX document has validation errors: ', err)
    else:
        print('Generated MaterialX document is valid')

# Write the document to a string
print('Resulting MaterialX document:\n')
result = core.Util.writeMaterialXDocString(doc)
print(result)
```

### Conversion from MaterialX to glTF

```python
materialXFileName = pkg_resources.resource_filename('materialxgltf', 'data/BoomBoxWithAxes.mtlx')
print('> Load MaterialX document: %s' % materialXFileName)

mtlx2glTFWriter = core.MTLX2GLTFWriter()
doc, libFiles = core.Util.createMaterialXDoc()
mx.readFromXmlFile(doc, materialXFileName, mx.FileSearchPath())

options = core.MTLX2GLTFOptions()
options['debugOutput'] = True
mtlx2glTFWriter.setOptions(options)
gltfString = mtlx2glTFWriter.convert(doc)
if len(gltfString) > 0:
    print('> Resulting glTF:\n')
    print(gltfString)
else:
    print('> Failed to convert MaterialX document to glTF')
```

### Embedding Geometry 

```python
gltfGeometryFile = pkg_resources.resource_filename('materialxgltf', 'data/shaderBall.gltf')
print('> Load glTF geometry file: %s' % gltfGeometryFile)

options = core.MTLX2GLTFOptions()
options['geometryFile'] = gltfGeometryFile
options['primsPerMaterial'] = False
mtlx2glTFWriter.setOptions(options)
gltfString = mtlx2glTFWriter.convert(doc)
if len(gltfString) > 0:
    print('> Resulting glTF:\n')
    print(gltfString)
else:
    print('> Failed to convert MaterialX document to glTF')
```

### Creating Primitives Per Material
```python
gltfGeometryFile = pkg_resources.resource_filename('materialxgltf', 'data/shaderBall.gltf')
print('> Load glTF geometry file: %s' % gltfGeometryFile)

options = core.MTLX2GLTFOptions()
options['geometryFile'] = gltfGeometryFile
options['primsPerMaterial'] = True
mtlx2glTFWriter.setOptions(options)
gltfString = mtlx2glTFWriter.convert(doc)
if len(gltfString) > 0:
    print('> Resulting glTF:\n')
    print(gltfString)
else:
    print('> Failed to convert MaterialX document to glTF')
```

### Packaging A Binary File

```python
gltfFileName = pkg_resources.resource_filename('materialxgltf', 'data/BoomBoxWithAxes_primMaterials.gltf')
print('> Load glTF geometry file: %s' % gltfGeometryFile)
binaryFileName = str()
binaryFileName = gltfFileName .replace('.gltf', '.glb')
print('Packaging GLB...')
try:
    saved, images, buffers = mtlx2glTFWriter.packageGLTF(gltfFileName , binaryFileName)
    print('Save GLB file:' + binaryFileName + '. Status:' + str(saved))
    for image in images:
        print('- Embedded image: %s' % image)
    for buffer in buffers:
        print('  - Embedded buffer: %s' % buffer)
    print('Packaging GLB...Done')
except Exception as err:
    print('Failed to package GLB file: %s' % err)
```

### Translate Shader and Bake Textures

All materials are assumed to use glTF PBR surface shaders.
Conversion to this shading model can be performed via MaterialX
utilities, which includes texture baking.

Please refer to the **[sample Jupyter notebook](https://kwokcb.github.io/materialxgltf/docs/examples.html)** for an example of shader
translation and baking using some convenience functions included with the package.
Note that they do not need to be used as the core MaterialX distribution provides
access to the APIs used in this package.

## Build

There are a number of build scripts in the [utiltities](https://kwokcb.github.io/materialxgltf/utiltities) folder provided for convenience
if users wish to build the repository locally:

- `build.sh` : Install package and build dependents
- `build_docs` : Build Jupyter notebooks and run Doxygen to build documentation. Note that this will install the `jupyter` package from PyPi. Users can all install development dependencies using `pip install '.[dev]'` from the root folder.
- `build_examples` : Build example content. This is WIP.
- `build_dist` : Build  distribution in a top level `dist` folder.

## Authors

- LinkedIn: <a href="https://www.linkedin.com/in/bernard-kwok/" target="_blank">Bernard Kwok</a>
- GitHub: [kwokcb](https://github.com/kwokcb)
- Email: <a href="mailto:kwokcb@gmail.com">kwokcb@gmail.com</a>
