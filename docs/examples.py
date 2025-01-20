#!/usr/bin/env python
# coding: utf-8

# <script type='module' src='https://unpkg.com/@google/model-viewer/dist/model-viewer.js'></script>
# 
# ### Using The Core Library
# 
# This notebook provides a set of sample code which demonstrates the workflow to convert between glTF and MaterialX.
# 
# The sample input file is the "BoomBox with Axes" file from the glTF sample repository found [here](https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models//BoomBoxWithAxes/glTF) is used to demonstrate glTF to MaterialX conversion. The resulting MaterialX file after conversion is used to demonstrate conversion to glTF.
# 
# | | |
# | :--: | :--: |
# | <model-viewer style='background-color:grey;; width: 24em; height: 24em' id='viewer1' ar interaction-prompt='none' camera-controls touch-action='pan-y' src='./data/BoomBoxWithAxes_primMaterials.glb' shadow-intensity='0.3' alt='BoomBox With Axes Per Prim Material' poster='./data/BoomBoxWithAxes_primMaterials.png'></model-viewer> | <model-viewer style='background-color:grey;; width: 24em; height: 24em' id='viewer1' ar interaction-prompt='none' camera-controls touch-action='pan-y' src='./data/BoomBoxWithAxes.mtlx_sphere.glb' shadow-intensity='0.3' alt='BoomBox With Axes Per Prim Material' poster=''></model-viewer> |
# 
# The following are some examples from conversion of Substance3D materials to glTF
# | | |
# | :--: | :--: |
# | <model-viewer style='background-color:grey; width: 24em; height: 24em' id='viewer1' ar interaction-prompt='none' camera-controls touch-action='pan-y' src='./data/Substance3D/parquet_clothes.mtlx.glb' shadow-intensity='0.3' alt='Parquet on Cube' poster=''></model-viewer> | <model-viewer style='background-color:grey; width: 24em; height: 24em' id='viewer1' ar interaction-prompt='none' camera-controls touch-action='pan-y' src='./data/Substance3D/parquet_clothes.mtlx_moebius.glb' shadow-intensity='0.3' alt='Parquet on Cube' poster=''></model-viewer> | 
# | <model-viewer style='background-color:grey; width: 24em; height: 24em' id='viewer1' ar interaction-prompt='none' camera-controls touch-action='pan-y' src='./data/Substance3D/parquet_clothes.mtlx_shaderball.glb' shadow-intensity='0.3' alt='Parquet on Cube' poster=''></model-viewer> | <model-viewer style='background-color:grey; width: 24em; height: 24em' id='viewer1' ar interaction-prompt='none' camera-controls touch-action='pan-y' src='./data/Substance3D/parquet_clothes.mtlx_sphere.glb' shadow-intensity='0.3' alt='Parquet on Cube' poster=''></model-viewer> |

# In[1]:


import materialxgltf
import materialxgltf.core as core


# This is import not required and is only added used here to improve output display

# In[2]:


from IPython.display import display_markdown

def displaySource(title, string, language='xml', open=True):
    text = '<details '
    text = text + (' open' if open else '') 
    text = text + '><summary><b>' + title + '</b></summary>\n\n' + '```' + language + '\n' + string + '\n```\n' + '</details>\n' 
    display_markdown(text, raw=True)


# Packaged Sample Data
# 
# For convenience a few sample files are included as part of the Python package and are used in this notebook.

# In[3]:


import pkg_resources
import os

directory_name = "data"  
files = pkg_resources.resource_listdir('materialxgltf', directory_name)
result = ''
for file in files:
    if file == 'shaderball.gltf' or file.find('baked') != -1:
        continue
    file_extension = os.path.splitext(file)[1]
    if file_extension in ['.mtlx', '.gltf']:
        result = result + file + '\n'

displaySource('Available data files', result, 'text', True)


# ### Convert from glTF to MaterialX
# 
# The sample glTF input file is the "BoomBox with Axes" file from the glTF sample repository [here](https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models//BoomBoxWithAxes/glTF).

# In[4]:


import pkg_resources
import MaterialX as mx

print(f'Using ( MaterialX version: {mx.getVersionString()} materialxgltf version: {materialxgltf.__version__} )\n')

gltfFileName = pkg_resources.resource_filename('materialxgltf', 'data/BoomBoxWithAxes.gltf')
print('Converting: %s' % mx.FilePath(gltfFileName).getBaseName())

# Instantiate a the reader class. Read in sample  glTF file
# and output a MaterialX document
gltf2MtlxReader = core.GLTF2MtlxReader()
doc = gltf2MtlxReader.convert(gltfFileName)
if not doc:
    print('Exiting due to error')
else:
    status, err = doc.validate()
    if not status:
        print('- Generated MaterialX document has validation errors: ', err)
    else:
        print('- Generated MaterialX document is valid')

# Examine the document output
result = core.Util.writeMaterialXDocString(doc)
displaySource('Resulting MaterialX document', result, 'xml', True)


# ### Using glTF to MaterialX Options
# 
# The option to create material assignments is enabled and the MaterialX file is regenerated.

# In[5]:


# Set option to write material assignments
options = core.GLTF2MtlxOptions()
options['createAssignments'] = True
gltf2MtlxReader.setOptions(options)

print('Converting with Look: %s' % mx.FilePath(gltfFileName).getBaseName())
doc = gltf2MtlxReader.convert(gltfFileName)
if not doc:
    print('Existing due to error')
else:
    status, err = doc.validate()
    if not status:
        print('Generated MaterialX document has validation errors: ', err)
    else:
        print('Generated MaterialX document is valid')

# Display the resulting document
result = core.Util.writeMaterialXDocString(doc)
displaySource('Resulting MaterialX document', result, 'xml', True)


# ### Conversion from MaterialX to glTF
# 
# This file is then converted back to glTF.

# In[6]:


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
    displaySource('Resulting glTF', gltfString, 'json', True)
else:
    print('> Failed to convert MaterialX document to glTF')


# ### Embedding Geometry
# 
# To view the material on sample geometry the sample "shader ball" geometry is imported. 
# The first MaterialX material will be assigned to all of the geometric primitives.

# In[7]:


gltfGeometryFile = pkg_resources.resource_filename('materialxgltf', 'data/shaderBall.gltf')
print('> Load glTF geometry file: %s' % mx.FilePath(gltfGeometryFile).getBaseName())

options = core.MTLX2GLTFOptions()
# Set the geometry file to use
options['geometryFile'] = gltfGeometryFile
mtlx2glTFWriter.setOptions(options)

# Perform the conversion
gltfString = mtlx2glTFWriter.convert(doc)
if len(gltfString) > 0:
    displaySource('Resulting glTF', gltfString, 'json', False)
else:
    print('> Failed to convert MaterialX document to glTF')


# ### Creating Primitives Per Material
# 
# This geometry is (transform) instanced for each of the MaterialX materials and then assigned that material.
# 
# In this case there are 2 materials.

# In[8]:


gltfGeometryFile = pkg_resources.resource_filename('materialxgltf', 'data/shaderBall.gltf')
print('> Load glTF geometry file: %s' % gltfGeometryFile)

options = core.MTLX2GLTFOptions()
options['geometryFile'] = gltfGeometryFile

# Set to create an transform instance for each material and assign the material
options['primsPerMaterial'] = True

mtlx2glTFWriter.setOptions(options)
gltfString = mtlx2glTFWriter.convert(doc)
if len(gltfString) > 0:
    displaySource('Resulting glTF', gltfString, 'json', False)
else:
    print('> Failed to convert MaterialX document to glTF')


# ### Creating Binary Package
# 
# For the purposesd of data interop and preview the glTF file is packaged to produce a single glb file.
# 
# <img src="./images/ThreeJS_editor_boombox.png" width="100%"><br>
# <sub>Result after conversion to glTF as show in the ThreeJS editor</sub>

# In[9]:


# Load in sample gltf file
gltfFileName = pkg_resources.resource_filename('materialxgltf', 'data/BoomBoxWithAxes_primMaterials.gltf')
gltfFileNameBase = mx.FilePath(gltfGeometryFile).getBaseName()

log = 'Packaging GLB...\n'
log = log + '- Load glTF geometry file: %s' % gltfFileNameBase + '\n'

# Package the gltf file's dependents into a glb file
binaryFileName = str()
binaryFileName = gltfFileName .replace('.gltf', '.glb')
gltfFileNameBase = mx.FilePath(binaryFileName).getBaseName()
try:
    saved, images, buffers = mtlx2glTFWriter.packageGLTF(gltfFileName , binaryFileName)
    log = log + '- Save GLB file:' + gltfFileNameBase + '. Status: ' + str(saved)
    log = log + '\n'
    for image in images:
        log = log + '  - Embedded image: %s' % image + '\n'
    for buffer in buffers:
        log = log + '  - Embedded buffer: %s' % buffer + '\n'
    log = log + 'Packaging completed.\n'
except Exception as err:
    log = log + '- Failed to package GLB file: %s' % err + '\n'

displaySource('Packaging Log', log, 'text', True)


# ### Translate Shader and Bake Textures
# 
# Shader translation and and baking generally are paired together as
# shader translation inserts an additional MaterialX "translation" node graph
# which needs to be "baked" out to get direct mappings from the upstream pattern
# graphs to the target shading model. 
# 
# The built in baking for MaterialX is used. This baking:
# - Requires a GPU which can render GLSL or Metal (for Mac platforms).
# - Always writes new files and images to disk.
# - Can may halt or not run *inside a Jupyter notebook* due to it's usage of GPU rendering.
# 
# These steps can be performed as an independent pre-process 
# with only a dependency on the core MaterialX distribution -- thus
# does not require this package to be used.

# #### Marble Example
# 
# The following assumes access to the "marble" example available from MaterialX github.
# 
# <img src="./images/MaterialXGraphEditor_boombox.png" width=100%>
# <sub>Figure: Original shader graph in MaterialX Graph Editor. The marble is a procedural shader.</sub>
# 
# The first step executes shader translation.

# In[10]:


# Set search path to defaut so that MaterialX libraries can be found
searchPath = mx.getDefaultDataSearchPath()

# Translate shaders
materialXFileName = pkg_resources.resource_filename('materialxgltf', 'data/standard_surface_marble_solid.mtlx')
materialXFileNameBase = mx.FilePath(materialXFileName).getBaseName()
print('> Load MaterialX file: %s' % materialXFileNameBase)

mtlx2glTFWriter = core.MTLX2GLTFWriter()
doc, libFiles = core.Util.createMaterialXDoc()
mx.readFromXmlFile(doc, materialXFileName, mx.FileSearchPath())

 # Perform shader translation and baking if necessary
translatedCount = mtlx2glTFWriter.translateShaders(doc)
title = ' Translated ' + str(translatedCount) + ' shader(s).'
displaySource(title, core.Util.writeMaterialXDocString(doc), 'xml', True)


# This is followed by texture baking to obtain this result:
# 
# | MaterialX Graph Editor | Baked Image(s) |
# | :--: | :--: |
# | <img src="./images/MaterialXGraphEditor_boombox_baked.png"> | <img src="./images/Marble_3D_gltf_pbr_base_color.png"> |
# 
# <em><sub>Figure: Baked shader graph in MaterialX Graph Editor (lef). Baked images (right)</sub></em>
# 
# Baking itself will write out a new MaterialX document and a set of baked images. 
# 
# There are two issues to be aware of when using baking:
# 
# - Baking requires that the shader implementation code be accessible as it's either using `GLSL`` or `Metal`` code generation (at time of writing). Thus the appropriate search paths must be set to find the shader code. Additionally any file image references must be resolved taking into any document file name paths qualifiers (such as `fileprefix` and tokens.
# 
# - Baking embeds baked image file name references with **absolute paths**. This is not a problem for the MaterialX document itself, but is a problem for the glTF file which is being generated. To handle this all absolute paths are converted to relative paths, given the assumption that baking will write the files into the same folder location as the baked MaterialX document.

# In[11]:


import os

materialXFileName = materialXFileName + '_baked.mtlx'
bakeResolution = 256

# Set the search options properly to ensure the MaterialX definition library can be found
# as well as set search paths for filename resolving.
options = core.MTLX2GLTFOptions()
searchPath = mx.getDefaultDataSearchPath()
if not mx.FilePath(materialXFileName).isAbsolute():
    materialXFileName = os.path.abspath(materialXFileName)
searchPath.append(mx.FilePath(materialXFileName).getParentPath())
searchPath.append(mx.FilePath.getCurrentPath())
options['searchPath'] = searchPath
mtlx2glTFWriter.setOptions(options)

# Perform baking
mtlx2glTFWriter.bakeTextures(doc, False, bakeResolution, bakeResolution, False, 
                            False, False, materialXFileName)
doc, libFiles = core.Util.createMaterialXDoc()
mx.readFromXmlFile(doc, materialXFileName, searchPath)
title = ' Baked document: '
displaySource(title, core.Util.writeMaterialXDocString(doc), 'xml', True)


# After baking we perform a final pass to make these image paths relative to that folder as platform specific absolute paths are not valid for glTF.

# In[12]:


remappedUris = core.Util.makeFilePathsRelative(doc, materialXFileName)
for uri in remappedUris:
    print('- Remapped URI: "%s" to "%s"' % (uri[0], uri[1]))

title = ' Baked document with resolved URIs: '
displaySource(title, core.Util.writeMaterialXDocString(doc), 'xml', True)


# This final document can then be used as input for conversion to glTF:

# In[13]:


# Create a convert and convert write only materials to a glTF file
mtlx2glTFWriter = core.MTLX2GLTFWriter()
options = core.MTLX2GLTFOptions()
options['debugOutput'] = True
mtlx2glTFWriter.setOptions(options)
gltfString = mtlx2glTFWriter.convert(doc)
if len(gltfString) > 0:
    displaySource('Translate and Baked Result to glTF', gltfString, 'json', True)
else:
    print('> Failed to convert MaterialX document to glTF')


# The final result can then be viewed using a viewer such as the ThreeJS editor:
# 
# <img src="./images/ThreeJS_editor_baked_marble.png" width="100%">

# Translation and baking are useful to just convert shading models. Below is a snapshot of a few materials which were downloaded from
#  the [Physical Based Site](https://physicallybased.info/) which is maintained by Anton Palmqvist. The materials were converted from MaterialX with the preview using the ThreeJS editor:
# 
#  <img src="./images/PhysicallyBasedExamples.png" width=100%>
#  <sub>Figure: From left to right: "Aluminum", "Sapphire", "Whiteboard", and "Tire" examples</sub>

# ## Convenience Functions and Command Line Tools
# 
# The following are convenience functions and command line tools which are provided as part of this package.
# 
# - The file `mtlx2gltf.py`` contains a command line tool that uses a utility function `mtlx2gltf` to convert from MaterialX to glTF.
# Various command line options are mapped to conversion options (`MTLX2GLTFOptions`).
# ```bash
# usage: mtlx2gltf.py [-h] [--gltfFileName GLTFFILENAME] [--gltfGeomFileName GLTFGEOMFILENAME] [--primsPerMaterial PRIMSPERMATERIAL]
#                     [--packageBinary PACKAGEBINARY] [--translateShaders TRANSLATESHADERS] [--bakeTextures BAKETEXTURES]
#                     [--bakeResolution BAKERESOLUTION]
#                     mtlxFileName
# 
# Utility to convert a MaterialX file to a glTF file
# 
# positional arguments:
#   mtlxFileName          Path containing MaterialX file to convert.
# 
# options:
#   -h, --help            show this help message and exit
#   --gltfFileName GLTFFILENAME
#                         Name of MaterialX output file. If not specified the glTF name with "_tomtlx.mtlx" suffix will be used
#   --gltfGeomFileName GLTFGEOMFILENAME
#                         Name of MaterialX output file. If not specified the glTF name with "_tomtlx.mtlx" suffix will be used
#   --primsPerMaterial PRIMSPERMATERIAL
#                         Create a new primitive per material and assign the material. Default is False
#   --packageBinary PACKAGEBINARY
#                         Create a biary packaged GLB file. Default is False
#   --translateShaders TRANSLATESHADERS
#                         Translate shaders to glTF. Default is False
#   --bakeTextures BAKETEXTURES
#                         Bake pattern graphs as textures. Default is False
#   --bakeResolution BAKERESOLUTION
#                         Bake image resolution. Default is 256
# ```                        
# - The file gltf2mtlx.py contains a command line tool that uses a utility function to convert from glTF to MaterialX.
# Various command line options are mapped to conversion options (`GLTF2MTLXOptions`).
# ```bash
# usage: gltf2mtlx.py [-h] [--mtlxFileName MTLXFILENAME] [--createAssignments CREATEASSIGNMENTS] gltfFileName
# 
# Utility to convert a glTF file to MaterialX file
# 
# positional arguments:
#   gltfFileName          Path containing glTF file to convert.
# 
# options:
#   -h, --help            show this help message and exit
#   --mtlxFileName MTLXFILENAME
#                         Name of MaterialX output file. If not specified the glTF name with "_tomtlx.mtlx" suffix will be used
#   --createAssignments CREATEASSIGNMENTS
#                         Create material assignments. Default is True
# ```
# ### Image and Geometry Pathing
# 
# glTF does not allow for any pathing to be specified on resources such as image and geometry uris. As such the proper pathing must be set before packaging to glb files. This is handled during the packaing process which uses the `pygltflib` Python package.
# 
# By default `mtlx2gltf`adds search paths (mx.FileSearchPath) to attempt to find the absoluate location of the uri resources, sets the uri and hen performs binary packing. Thus it is possible for instance to specify embedding geometry which is not in the same folder as the root glTF file.
# 
# The examples at the beginning of this document show an example Adobe Substance 3D material which was exported and mapped to a MaterialX material. Then it was converted to glTF with different geometry paths.
# 
