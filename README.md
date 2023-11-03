# materialxgltf

## Contents
- [Introduction](#Introduction)
- [Installation](#installation)
- [Usage](#usage)
- [Documentation](#documentation)

## Introduction

This package supports the bi-directional translation between MaterialX materials and glTF materials. The minimum version of MaterialX required is 1.38 8 and the target glTF version is 2.0.1.  

Below is an example of converting the "Damaged Helmet" asset (found in the [glTF Sample Model repository](https://github.com/KhronosGroup/glTF-Sample-Models/tree/master/2.0/DamagedHelmet) to MaterialX and previewing.
<img src="https://github.com/kwokcb/glTF_MaterialX/raw/main/docs/gltf_import-graphEditor2.png" width="80%">

The functionality found here is equivalent to the C++ module available in
[this repository](https://github.com/kwokcb/glTF_MaterialX). Note that additional documentation can be found on that site. 

## Installation

The minimum version of Python is assumed to be 3.9.

The package can be installed using `pip``:

```bash
pip install materialxgltf
```

or the [source repository](https://github.com/kwokcb/materialxgltf) can be cloned and the package built from the command line:

```bash
py -m build
```

This will build a distribution folder called `dist` which contains 
a zip file which can be installed using:

```bash
pip --install <name of zip>
```

### Requirements

Requires the installation of the following packages:

* `materialx` version 1.38.8 or higher: For editing MaterialX documents.
* `pygltflib` : For conversion from `glTF` to `glb` including packaging dependent geometry and image resources.


## Documentation

For more detailed information about the workflow this package supports, please refer to this [documentation](https://kwokcb.github.io/MaterialX_Learn/documents/workflow_gltf.html).

Refer to [this documentation](https://kwokcb.github.io/materialxgltf/docs/html) for API usage. 

## Usage

<script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.js">    
</script>

<model-viewer style='background-color:rgba(0, 0, 0, 1.0); width: 48em; height: 48em' id='viewer1' ar interaction-prompt='none' camera-controls touch-action='pan-y' src='./docs/data/BoomBoxWithAxes_primMaterials.glb' shadow-intensity='0.3' alt='BoomBox With Axes Per Prim Material' poster='./docs/data/BoomBoxWithAxes_primMaterials.png'></model-viewer>

The following shows is a set of progressive examples to convert from a glTF file to MaterialX and then to a new glTF file for "shader ball" preview of
extracted materials.

Note that the sample data is included as part of the package for convenience.

The sample input file is the "BoomBox with Axes" file from the glTF sample repository found [here](https://github.com/KhronosGroup/glTF-Sample-Models/tree/master/2.0/BoomBoxWithAxes/glTF).

<img src="https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/BoomBoxWithAxes/screenshot/screenshot.jpg">

This is converted from glTF to a MaterialX document which can be previewed / modified using an integration which supports MaterialX. Here the file is loaded into the "MaterialX Graph Editor" which comes with [MaterialX releases](https://github.com/AcademySoftwareFoundation/MaterialX/releases).

<img src="https://raw.githubusercontent.com/kwokcb/MaterialX_Learn/main/documents/images/gltf_to_mtlx_boombox_with_axes.png" alt="MaterialX Graph Editor Snapshot"
width="80%">

The converted materials are then used to create a new glTF file using sample "shaderball" data with each material found assigned to different instances of the "shaderball"

<img src="https://raw.githubusercontent.com/kwokcb/MaterialX_Learn/main/documents/images/mtlx_to_gltf_materialviewer.png" alt="VSCode Snapshot"
width="50%">

## Interactive Example

A `Jupyter` notebook which performs the same steps is available [here](https://kwokcb.github.io/docs/examples.html). This or any other notebook can be used if the user wishes to test the package in an interactive environment.

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

Please refer to the sample Jupyter notebook for an example of shader
translation and baking using some convenience functions included with the package.
Note that they do not need to be used as the core MaterialX distribution provides
access to the APIs used in this package.

## Author

- LinkedIn: <a href="https://www.linkedin.com/in/bernard-kwok/" target="_blank">Bernard Kwok</a>
- GitHub: [kwokcb](https://github.com/kwokcb)
- Email: <a href="mailto:kwokcb@gmail.com">kwokcb@gmail.com</a>


