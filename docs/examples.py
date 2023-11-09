# %% [markdown]
# ### Using The Core Library
# 
# This notebook provides a set of sample code which demonstrates the 
# workflow to convert between glTF and MaterialX.
# 
# The sample input file is the "BoomBox with Axes" file from the glTF sample repository found [here](https://github.com/KhronosGroup/glTF-Sample-Models/tree/master/2.0/BoomBoxWithAxes/glTF) is used to demonstrate glTF to MaterialX conversion.
# 
# The resulting MaterialX file after conversion is used to demonstrate conversion to glTF.
# 
# <script type='module' src='https://unpkg.com/@google/model-viewer/dist/model-viewer.js'></script>
# 
# <model-viewer style='background-color:grey;; width: 100%; height: 48em' id='viewer1' ar interaction-prompt='none' camera-controls touch-action='pan-y' src='./data/BoomBoxWithAxes_primMaterials.glb' shadow-intensity='0.3' alt='BoomBox With Axes Per Prim Material' poster='./data/BoomBoxWithAxes_primMaterials.png'></model-viewer>
# 

# %%
import materialxgltf.core as core

# %% [markdown]
# This is import not required and is only added used here to improve output display

# %%
from IPython.display import display_markdown

def displaySource(title, string, language='xml', open=True):
    text = '<details '
    text = text + (' open' if open else '') 
    text = text + '><summary><b>' + title + '</b></summary>\n\n' + '```' + language + '\n' + string + '\n```\n' + '</details>\n' 
    display_markdown(text, raw=True)

# %% [markdown]
# Packaged Sample Data
# 
# For convenience a few sample files are included as part of the Python package and are used in this notebook.

# %%
import pkg_resources

directory_name = "data"  
files = pkg_resources.resource_listdir('materialxgltf', directory_name)
result = ''
for file in files:
    result = result + file + '\n'

displaySource('Available data files', result, 'text', True)

# %% [markdown]
# ### Convert from glTF to MaterialX
# 
# The sample glTF input file is the "BoomBox with Axes" file from the glTF sample repository found [here](https://github.com/KhronosGroup/glTF-Sample-Models/tree/master/2.0/BoomBoxWithAxes/glTF).

# %%
import pkg_resources
import MaterialX as mx

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

# %% [markdown]
# ### Using glTF to MaterialX Options
# 
# The option to create material assignments is enabled and the MaterialX file is regenerated.

# %%
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

# %% [markdown]
# ### Conversion from MaterialX to glTF
# 
# This file is then converted back to glTF.

# %%
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

# %% [markdown]
# ### Embedding Geometry
# 
# To view the material on sample geometry the sample "shader ball" geometry is imported. 
# The first MaterialX material will be assigned to all of the geometric primitives.

# %%
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

# %% [markdown]
# ### Creating Primitives Per Material
# 
# This geometry is (transform) instanced for each of the MaterialX materials and then assigned that material.
# 
# In this case there are 2 materials.

# %%
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

# %% [markdown]
# ### Creating Binary Package
# 
# For the purposesd of data interop and preview the glTF file is packaged to produce a single glb file.
# 
# <img src="./images/ThreeJS_editor_boombox.png" width="100%"><br>
# <sub>Result after conversion to glTF as show in the ThreeJS editor</sub>

# %%
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

# %% [markdown]
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

# %% [markdown]
# #### Marble Example
# 
# The following assumes access to the "marble" example available from MaterialX github.
# 
# <img src="./images/MaterialXGraphEditor_boombox.png" width=100%>
# <sub>Figure: Original shader graph in MaterialX Graph Editor. The marble is a procedural shader.</sub>
# 
# The first step executes shader translation.

# %%
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


# %% [markdown]
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

# %%
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

# %% [markdown]
# After baking we perform a final pass to make these image paths relative to that folder as platform specific absolute paths are not valid for glTF.

# %%

remappedUris = core.Util.makeFilePathsRelative(doc, materialXFileName)
for uri in remappedUris:
    print('- Remapped URI: "%s" to "%s"' % (uri[0], uri[1]))

title = ' Baked document with resolved URIs: '
displaySource(title, core.Util.writeMaterialXDocString(doc), 'xml', True)

# %% [markdown]
# This final document can then be used as input for conversion to glTF:

# %%
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

# %% [markdown]
# The final result can then be viewed using a viewer such as the ThreeJS editor:
# 
# <img src="./images/ThreeJS_editor_baked_marble.png" width="100%">


