# globals.py

'''
@file 
Package globals
'''
TO_DEGREE = 180.0 / 3.1415926535

#  Default MaterialX names for conversion to MaterialX
MTLX_DEFAULT_MATERIAL_NAME = 'MAT_0'
MTLX_MATERIAL_PREFIX = 'MAT_'
MTLX_DEFAULT_SHADER_NAME = 'SHD_0'
MTLX_SHADER_PREFIX = 'SHD_'
# Default GLTF names for conversion to/from MaterialX
GLTF_DEFAULT_NODE_PREFIX = 'NODE_'
GLTF_DEFAULT_MESH_PREFIX = 'MESH_'
# As primitives have not named, use the index as the name if more than one primitives child
GLTF_DEFAULT_PRIMITIVE_PREFIX = 'PRIMITIVE_'

# MaterialX strings
#SURFACE_SHADER_TYPE_STRING = 'surfaceshader'
MTLX_GLTF_PBR_CATEGORY = 'gltf_pbr'
MTLX_UNLIT_CATEGORY_STRING = 'surface_unlit'
MULTI_OUTPUT_TYPE_STRING = 'multioutput'
MTLX_GLTF_IMAGE = 'gltf_image'
MTLX_GLTF_COLOR_IMAGE = 'gltf_colorimage'
MTLX_GLTF_NORMALMAP_IMAGE = 'gltf_normalmap'
MTLX_DEFAULT_COLORSPACE = 'srgb_texture'
# mx.PortElement.NODE_NAME_ATTRIBUTE is not exposed
MTLX_INTERFACEINPUT_NAME_ATTRIBUTE = 'interfacename'
MTLX_NODE_NAME_ATTRIBUTE = 'nodename'
MTLX_NODEGRAPH_NAME_ATTRIBUTE = 'nodegraph'
MTLX_COLOR_SPACE_ATTRIBUTE = 'colorspace' # mx.Element.COLOR_SPACE_ATTRIBUTE is not exposed
MTLX_VEC3_STRING = 'vector3'
EMPTY_STRING = ''
MTLX_VALUE_ATTRIBUTE = 'value' # mx.AttributeDef.MTLX_VALUE_ATTRIBUTE is not exposed

# We use a colon to separate the category and name of an element in the JSON hierarchy
JSON_CATEGORY_NAME_SEPARATOR = ':'
# The root of the JSON hierarchy
MATERIALX_DOCUMENT_ROOT = 'materialx'

