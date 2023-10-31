# %% [markdown]
# ### Use Core Library
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
# <model-viewer style='background-color:rgba(0, 0, 0, 0.5); width: 24em; height: 24em' id='viewer1' ar interaction-prompt='none' camera-controls touch-action='pan-y' src='./data/BoomBoxWithAxes_primMaterials.glb' shadow-intensity='0.3' alt='BoomBox With Axes Per Prim Material' poster='./data/BoomBoxWithAxes_primMaterials.png'></model-viewer>
# 

# %%
import materialxgltf.core as core

# %% [markdown]
# This import not required and is only added used here to improve output display

# %%
from IPython.display import display_markdown

def displaySource(title, string, language='xml', open=True):
    text = '<details '
    text = text + (' open' if open else '') 
    text = text + '><summary>' + title + '</summary>\n\n' + '```' + language + '\n' + string + '\n```\n' + '</details>\n' 
    display_markdown(text, raw=True)

# %% [markdown]
# Package Data

# %%
import pkg_resources

directory_name = "data"  
files = pkg_resources.resource_listdir('materialxgltf', directory_name)
for file in files:
    print('Data file: ', file)


# %% [markdown]
# ### Convert from glTF to MaterialX

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
    print('Existing due to error')
else:
    status, err = doc.validate()
    if not status:
        print('- Generated MaterialX document has validation errors: ', err)
    else:
        print('- Generated MaterialX document is valid')

# Examine the document output
result = core.Util.writeMaterialXDocString(doc)
displaySource('Resulting MaterialX document', result, 'xml', False)

# %% [markdown]
# ### Using glTF to MaterialX Options

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
displaySource('Resulting MaterialX document', result, 'xml', False)

# %% [markdown]
# ### Conversion from MaterialX to glTF

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
    displaySource('Resulting glTF', gltfString, 'json', False)
else:
    print('> Failed to convert MaterialX document to glTF')

# %% [markdown]
# ### Embed Geometry
# 

# %%
gltfGeometryFile = pkg_resources.resource_filename('materialxgltf', 'data/shaderBall.gltf')
print('> Load glTF geometry file: %s' % mx.FilePath(gltfGeometryFile).getBaseName())

options = core.MTLX2GLTFOptions()
options['geometryFile'] = gltfGeometryFile
options['primsPerMaterial'] = False
mtlx2glTFWriter.setOptions(options)
gltfString = mtlx2glTFWriter.convert(doc)
if len(gltfString) > 0:
    displaySource('Resulting glTF', gltfString, 'json', False)
else:
    print('> Failed to convert MaterialX document to glTF')

# %% [markdown]
# ### Creating Primitives Per Material

# %%
gltfGeometryFile = pkg_resources.resource_filename('materialxgltf', 'data/shaderBall.gltf')
print('> Load glTF geometry file: %s' % mx.FilePath(gltfGeometryFile).getBaseName())

options = core.MTLX2GLTFOptions()
options['geometryFile'] = gltfGeometryFile
options['primsPerMaterial'] = True
mtlx2glTFWriter.setOptions(options)
gltfString = mtlx2glTFWriter.convert(doc)
if len(gltfString) > 0:
    displaySource('Resulting glTF', gltfString, 'json', False)
else:
    print('> Failed to convert MaterialX document to glTF')

# %% [markdown]
# ### Package Binary

# %%
gltfFileName = pkg_resources.resource_filename('materialxgltf', 'data/BoomBoxWithAxes_primMaterials.gltf')
gltfFileNameBase = mx.FilePath(gltfGeometryFile).getBaseName()
print('> Load glTF geometry file: %s' % gltfFileNameBase)

# Package the gltf file's dependents into a glb file
binaryFileName = str()
binaryFileName = gltfFileName .replace('.gltf', '.glb')
gltfFileNameBase = mx.FilePath(binaryFileName).getBaseName()
print('Packaging GLB...')
try:
    saved, images, buffers = mtlx2glTFWriter.packageGLTF(gltfFileName , binaryFileName)
    print('Save GLB file:' + gltfFileNameBase + '. Status:' + str(saved))
    for image in images:
        print('- Embedded image: %s' % image)
    for buffer in buffers:
        print('  - Embedded buffer: %s' % buffer)
    print('Packaging GLB...Done')
except Exception as err:
    print('Failed to package GLB file: %s' % err)


# %% [markdown]
# ### Translate Shader and Bake Textures
# 
# These  steps can be done as an independent pre-process 
# with only a dependency on the core MaterialX distribution -- thus
# does not require this package to be used.


