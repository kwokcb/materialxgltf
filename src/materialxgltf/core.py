# core.py

'''
@file 
This module contains the core definitions and utilities for MaterialX glTF conversion.
'''

# MaterialX support
import MaterialX as mx
import MaterialX.PyMaterialXGenShader as mx_gen_shader
from MaterialX import PyMaterialXRender as mx_render
from MaterialX import PyMaterialXRenderGlsl as mx_render_glsl
from sys import platform
if platform == 'darwin':
    from MaterialX import PyMaterialXRenderMsl as mx_render_msl

# JSON / glTF support
import json
from pygltflib import GLTF2, BufferFormat
from pygltflib.utils import ImageFormat

# Utilities
import os, re, copy, math

from materialxgltf.globals import *

#########################################################################################
# Basic I/O Utilities 
#########################################################################################
class Util:

    @staticmethod
    def createMaterialXDoc() -> (mx.Document, list):
        '''
        @brief Utility to create a MaterialX document with the default libraries loaded.
        @return The created MaterialX document and the list of loaded library filenames.
        '''
        doc = mx.createDocument()
        stdlib = mx.createDocument()
        libFiles = []
        searchPath = mx.getDefaultDataSearchPath()
        libFiles = mx.loadLibraries(mx.getDefaultDataLibraryFolders(), searchPath, stdlib)
        doc.importLibrary(stdlib)

        return doc, libFiles

    @staticmethod
    def skipLibraryElement(elem) -> bool:
        '''
        @brief Utility to skip library elements when iterating over elements in a document.
        @return True if the element is not in a library, otherwise False.
        '''
        return not elem.hasSourceUri()

    @staticmethod
    def writeMaterialXDoc(doc, filename, predicate=skipLibraryElement):
        '''
        @brief Utility to write a MaterialX document to a file.
        @param doc The MaterialX document to write.
        @param filename The name of the file to write to.
        @param predicate A predicate function to determine if an element should be written. Default is to skip library elements.
        '''
        writeOptions = mx.XmlWriteOptions()
        writeOptions.writeXIncludeEnable = False
        writeOptions.elementPredicate = predicate

        if filename:
            mx.writeToXmlFile(doc, filename, writeOptions)
    
    @staticmethod
    def writeMaterialXDocString(doc, predicate=skipLibraryElement):
        '''
        @brief Utility to write a MaterialX document to string.
        @param doc The MaterialX document to write.
        @param predicate A predicate function to determine if an element should be written. Default is to skip library elements.
        @return The XML string representation of the MaterialX document.
        '''
        writeOptions = mx.XmlWriteOptions()
        writeOptions.writeXIncludeEnable = False
        writeOptions.elementPredicate = predicate

        result =  mx.writeToXmlString(doc, writeOptions)
        return result
    
    @staticmethod
    def makeFilePathsRelative(doc, docPath) -> list:
        '''
        @brief Utility to make file paths relative to a document path
        @param doc The MaterialX document to update.
        @param docPath The path to make file paths relapy -tive to.
        @return List of tuples of unresolved and resolved file paths.
        '''
        result = []

        for elem in doc.traverseTree():
                valueElem = None
                if elem.isA(mx.ValueElement):
                    valueElem = elem
                if not valueElem or valueElem.getType() != mx.FILENAME_TYPE_STRING:
                    continue

                unresolvedValue = mx.FilePath(valueElem.getValueString())
                if unresolvedValue.isEmpty():
                    continue

                elementResolver = valueElem.createStringResolver()
                if unresolvedValue.isAbsolute():
                    elementResolver.setFilePrefix('')
                resolvedValue = valueElem.getResolvedValueString(elementResolver)
                resolvedValue = mx.FilePath(resolvedValue).getBaseName()
                valueElem.setValueString(resolvedValue)

                if unresolvedValue != resolvedValue:
                    result.append([unresolvedValue.asString(mx.FormatPosix), resolvedValue])

        return result  

#########################################################################################
# gLTF to MaterialX Conversion classes
#########################################################################################
class GLTF2MtlxOptions(dict):
    '''
    @brief Class to hold options for glTF to MaterialX conversion.
    Available options:
        - 'addAllInputs' : Add all inputs from the node definition. Default is False. 
        - 'createAssignments' : Create MaterialX assignments for each glTF primitive. Default is False.
        - 'debugOutput' : Print debug output. Default is False.
    '''
    def __init__(self, *args, **kwargs):
        '''
        @brief Constructor
        '''
        super().__init__(*args, **kwargs)

        self['createAssignments'] = False
        self['addAllInputs'] = False
        self['debugOutput'] = True

class GLTF2MtlxReader:
    '''
    Class to read glTF and convert to MaterialX.    
    '''
    # Log string
    _log = ''
    # Conversion options
    _options = GLTF2MtlxOptions()    

    def clearLog(self):
        '''
        @brief Clear the log string.
        '''
        self._log = ''

    def getLog(self):
        '''
        @brief Return the log string.
        @return The log string.
        '''
        return self._log
    
    def log(self, string):
        '''
        @brief Add a string to the log.
        @param string The string to add to the log.
        '''
        self._log += string + '\n'

    def setOptions(self, options):
        '''
        @brief Set the options for the reader.
        @param options The options to set.
        '''
        self._options = options

    def getOptions(self) -> GLTF2MtlxOptions:
        '''
        @brief Get the options for the reader.
        @return The options.
        '''
        return self._options

    def addMtlxImage(self, materials, nodeName, fileName, nodeCategory, nodeDefId, nodeType, colorspace='') -> mx.Node:
        '''
        Create a MaterialX image lookup.
        @param materials MaterialX document to add the image node to.
        @param nodeName Name of the image node.
        @param fileName File name of the image.
        @param nodeCategory Category of the image node.
        @param nodeDefId Node definition id of the image node.
        @param nodeType Type of the image node.
        @param colorspace Color space of the image node. Default is empty string.
        @return The created image node.        
        '''
        nodeName = materials.createValidChildName(nodeName)
        imageNode = materials.addNode(nodeCategory, nodeName, nodeType)
        if imageNode:
            if not imageNode.getNodeDef():
                self.log('Failed to create image node. Category,name,type: %s %s %s' % (nodeCategory, nodeName, nodeType))
                return imageNode

            if len(nodeDefId):
                imageNode.setAttribute(mx.InterfaceElement.NODE_DEF_ATTRIBUTE, nodeDefId)
                    
            fileInput = imageNode.addInputFromNodeDef(mx.Implementation.FILE_ATTRIBUTE)
            if fileInput:
                fileInput.setValue(fileName, mx.FILENAME_TYPE_STRING)                    

                if len(colorspace):
                    colorspaceattr = MTLX_COLOR_SPACE_ATTRIBUTE 
                    fileInput.setAttribute(colorspaceattr, colorspace)
            else:
                self.log('-- failed to create file input for name: %s' % fileName)

        return imageNode

    def addMTLXTexCoordNode(self, image, uvindex) -> mx.Node:
        '''
        @brief Create a MaterialX texture coordinate lookup
        @param image The image node to connect the texture coordinate node to.
        @param uvindex The uv index to use for the texture coordinate lookup.
        @return The created texture coordinate node.
        '''
        parent = image.getParent()
        if not parent.isA(mx.GraphElement):
            return None

        texcoordNode = None
        if parent:

            texcoordName = parent.createValidChildName('texcoord')
            texcoordNode = parent.addNode('texcoord', texcoordName, 'vector2')

            if texcoordNode:

                uvIndexInput = texcoordNode.addInputFromNodeDef('index')
                if uvIndexInput:
                    uvIndexInput.setValue(uvindex)

                # Connect to image node
                texcoordInput = image.addInputFromNodeDef('texcoord')
                if texcoordInput:
                    texcoordInput.setAttribute(MTLX_NODE_NAME_ATTRIBUTE, texcoordNode.getName())
        
        return texcoordNode

    def getGLTFTextureUri(self, texture, images) -> str:
        '''
        @brief Get the uri of a glTF texture.
        @param texture The glTF texture.
        @param images The set of glTF images.
        @return The uri of the texture.
        '''
        uri = ''
        if texture and 'source' in texture:
            source = texture['source']
            if source < len(images):
                image = images[source]

                if 'uri' in image:
                    uri = image['uri']
        return uri

    def readGLTFImageProperties(self, imageNode, gltfTexture, gltfSamplers):
        '''
        @brief Convert gltF to MaterialX image properties
        @param imageNode The MaterialX image node to set properties on.
        @param gltfTexture The glTF texture to read properties from.
        @param gltfSamplers The set of glTF samplers to examine properties from.
        '''
        texcoord = gltfTexture['texCoord'] if 'texCoord' in gltfTexture else None

        extensions = gltfTexture['extensions'] if 'extensions' in gltfTexture else None
        transformExtension = extensions['KHR_texture_transform'] if extensions and 'KHR_texture_transform' in extensions else None
        if transformExtension:
            rotation = transformExtension['rotation'] if 'rotation' in transformExtension else None
            if rotation:
                input = imageNode.addInputFromNodeDef('rotate')
                if input:
                    # Note: Rotation in glTF and MaterialX are opposite directions
                    # Direction is handled in the MaterialX implementation
                    input.setValueString (str(rotation * TO_DEGREE))
            offset = transformExtension['offset'] if 'offset' in transformExtension else None
            if offset:
                input = imageNode.addInputFromNodeDef('offset')
                if input:
                    input.setValueString ( str(offset).removeprefix('[').removesuffix(']'))
            scale = transformExtension['scale'] if 'scale' in transformExtension else None
            if scale:
                input = imageNode.addInputFromNodeDef('scale')
                if input:
                    input.setValueString (str(scale).removeprefix('[').removesuffix(']') )

            # Override texcoord if found in extension
            texcoordt = transformExtension['texCoord'] if 'texCoord' in transformExtension else None
            if texcoordt:
                texcoord = texcoordt

        # Add texcoord node if specified
        if texcoord:
            self.addMTLXTexCoordNode(imageNode, texcoord)    

        # Read sampler info
        samplerIndex = gltfTexture['sampler'] if 'sampler' in gltfTexture else None
        if samplerIndex != None and samplerIndex >= 0:
            sampler =  gltfSamplers[samplerIndex] if samplerIndex < len(gltfSamplers) else None        

            filterMap = {}
            filterMap[9728] = "closest"
            filterMap[9729] = "linear"
            filterMap[9984] = "cubic"
            filterMap[9985] = "closest"
            filterMap[9986] = "linear"
            filterMap[9987] = "cubic"

            # Filter. There is only one filter type so set based on the max filter if found, otherwise 
            # min filter if found
            magFilter = sampler['magFilter'] if 'magFilter' in sampler else None
            if magFilter:
                input = imageNode.addInputFromNodeDef('filtertype')
                if input:
                    filterString = filterMap[magFilter]
                    input.setValueString (filterString)
            minFilter = sampler['minFilter'] if 'minFilter' in sampler else None
            if minFilter:
                input = imageNode.addInputFromNodeDef('filtertype')
                if input:
                    filterString = filterMap[minFilter]
                    input.setValueString (filterString)

            wrapMap = {}
            wrapMap[33071] = "clamp"
            wrapMap[33648] = "mirror"
            wrapMap[10497] = "periodic"
            wrapS = sampler['wrapS'] if 'wrapS' in sampler else None
            if wrapS:
                input = imageNode.addInputFromNodeDef('uaddressmode')
                if input:
                    input.setValueString (wrapMap[wrapS])
                else:
                    self.log('Failed to add uaddressmode input')                
            wrapT = sampler['wrapT'] if 'wrapT' in sampler else None
            if wrapT:
                input = imageNode.addInputFromNodeDef('vaddressmode')
                if input:
                    input.setValueString (wrapMap[wrapT])
                else:
                    self.log('*** failed to add vaddressmode input')


    def readInput(self, materials, texture, values, imageNodeName, nodeCategory, nodeType, nodeDefId,
                shaderNode, inputNames, gltf_textures, gltf_images, gltf_samplers) -> mx.Node:
        '''
        @brief Read glTF material input and set input values or add upstream connected nodes
        @param materials MaterialX document to update
        @param texture The glTF texture to read properties from.
        @param values The values to set on the shader node inputs.
        @param imageNodeName The name of the image node to create if mapped
        @param nodeCategory The category of the image node to create if mapped
        @param nodeType The type of the image node to create if mapped
        @param nodeDefId The node definition id of the image node to create if mapped
        @param shaderNode The shader node to update inputs on.
        @param inputNames The names of the inputs to update on the shader node.
        @param gltf_textures The set of glTF textures to examine
        @param gltf_images The set of glTF images to examine
        @param gltf_samplers The set of glTF samplers to examine
        @return The created image node if mapped, otherwise None.
        '''
        imageNode = None

        # Create and set mapped input
        if texture:
            textureIndex = texture['index']
            texture = gltf_textures[textureIndex] if textureIndex < len(gltf_textures) else None
            uri = self.getGLTFTextureUri(texture, gltf_images)    
            imageNodeName = materials.createValidChildName(imageNodeName)
            imageNode = self.addMtlxImage(materials, imageNodeName, uri, nodeCategory, nodeDefId,                                   
                                        nodeType, EMPTY_STRING)
            if imageNode:
                self.readGLTFImageProperties(imageNode, texture, gltf_samplers)

                for inputName in inputNames:
                    input = shaderNode.addInputFromNodeDef(inputName)
                    if input:
                        input.setAttribute(MTLX_NODE_NAME_ATTRIBUTE, imageNode.getName())
                        input.removeAttribute(MTLX_VALUE_ATTRIBUTE)

        # Create and set unmapped input
        if not imageNode:        
            if len(values) > 0 and (len(values) == len(inputNames)):
                for i in range(0, len(values)):
                    inputName = inputNames[i]
                    value = values[i]
                    input = shaderNode.addInputFromNodeDef(inputName)
                    if input:
                        input.setValue(float(value))

        return imageNode

    def readColorInput(self, materials, colorTexture, color, imageNodeName, nodeCategory, nodeType, nodeDefId,
                        shaderNode, colorInputName, alphaInputName, 
                        gltf_textures, gltf_images, gltf_samplers, colorspace=MTLX_DEFAULT_COLORSPACE):
        '''     
        @brief Read glTF material color input and set input values or add upstream connected nodes
        @param materials MaterialX document to update
        @param colorTexture The glTF texture to read properties from.
        @param color The color to set on the shader node inputs if unmapped
        @param imageNodeName The name of the image node to create if mapped
        @param nodeCategory The category of the image node to create if mapped
        @param nodeType The type of the image node to create if mapped
        @param nodeDefId The node definition id of the image node to create if mapped
        @param shaderNode The shader node to update inputs on.
        @param colorInputName The name of the color input to update on the shader node.
        @param alphaInputName The name of the alpha input to update on the shader node.
        @param gltf_textures The set of glTF textures to examine
        @param gltf_images The set of glTF images to examine
        @param gltf_samplers The set of glTF samplers to examine
        @param colorspace The colorspace to set on the image node if mapped. Default is assumed to be srgb_texture.
        to match glTF convention.
        '''
            
        assignedColorTexture = False 
        assignedAlphaTexture = False 

        # Check to see if all inputs shoudl be added
        addAllInputs = self._options['addAllInputs']
        if addAllInputs:
            shaderNode.addInputsFromNodeDef()
            shaderNode.removeChild('tangent')
            shaderNode.removeChild('normal')
            shaderNode.removeChild('clearcoat_normal')
            shaderNode.removeChild('attenuation_distance')

        # Try to assign a texture (image node)
        if colorTexture:
            # Get the index of the texture
            textureIndex = colorTexture['index']
            texture = gltf_textures[textureIndex] if textureIndex < len(gltf_textures) else None
            uri = self.getGLTFTextureUri(texture, gltf_images)    
            imageNodeName = materials.createValidChildName(imageNodeName)
            imageNode = self.addMtlxImage(materials, imageNodeName, uri, nodeCategory, nodeDefId, nodeType, colorspace)

            if imageNode:
                self.readGLTFImageProperties(imageNode, colorTexture, gltf_samplers)

                newTextureName = imageNode.getName()

                # Connect texture to color input on shader
                if len(colorInputName):
                    colorInput = shaderNode.addInputFromNodeDef(colorInputName)
                    if not colorInput:
                        self.log('Failed to add color input:' + colorInputName)
                    else:
                        colorInput.setAttribute(MTLX_NODE_NAME_ATTRIBUTE, newTextureName)
                        colorInput.setOutputString('outcolor')
                        colorInput.removeAttribute(MTLX_VALUE_ATTRIBUTE)
                    assignedColorTexture = True

                # Connect texture to alpha input on shader
                if len(alphaInputName):            
                    alphaInput = shaderNode.addInputFromNodeDef(alphaInputName)
                    if not alphaInput:
                        self.log('Failed to add alpha input:' + alphaInputName)
                    else:
                        alphaInput.setAttribute(MTLX_NODE_NAME_ATTRIBUTE, newTextureName)
                        alphaInput.setOutputString('outa')
                        alphaInput.removeAttribute(MTLX_VALUE_ATTRIBUTE)

                    assignedAlphaTexture = True

        # Assign constant color / alpha if no texture is assigned
        if color:
            if not assignedColorTexture and len(colorInputName):
                colorInput = shaderNode.addInputFromNodeDef(colorInputName)
                if not colorInput:
                    nd = shaderNode.getNodeDef()
                    self.log('Failed to add color input: %s' % colorInputName)
                else:
                    colorInput.setValue(mx.Color3(color[0], color[1], color[2]))
                    if len(colorspace):
                        colorspaceattr = MTLX_COLOR_SPACE_ATTRIBUTE 
                        colorInput.setAttribute(colorspaceattr, colorspace)
            if not assignedAlphaTexture and len(alphaInputName):            
                alphaInput = shaderNode.addInputFromNodeDef(alphaInputName)
                if not alphaInput:
                    self.log('Failed to add alpha input: %s' % alphaInputName)
                else:
                    # Force this to be interepret as float vs integer
                    alphaInput.setValue(float(color[3]))

    def glTF2MaterialX(self, doc, gltfDoc) -> bool:
        '''
        @brief Convert glTF document to a MaterialX document.
        @param doc The MaterialX document to update.
        @param gltfDoc The glTF document to read from.
        @return True if successful, otherwise False.
        '''

        materials = gltfDoc['materials'] if 'materials' in gltfDoc else [] 
        textures = gltfDoc['textures'] if 'textures' in gltfDoc else [] 
        images = gltfDoc['images'] if 'images' in gltfDoc else []
        samplers = gltfDoc['samplers'] if 'samplers' in gltfDoc else []

        if not materials or len(materials) == 0:
            self.log('No materials found to convert')
            return False

        # Remapper from glTF to MaterialX for alpha mode
        alphaModeMap = {}
        alphaModeMap['OPAQUE'] = 0
        alphaModeMap['MASK'] = 1
        alphaModeMap['BLEND'] = 2

        for material in materials:

            # Generate shader and material names
            shaderName = MTLX_DEFAULT_SHADER_NAME
            materialName = MTLX_DEFAULT_MATERIAL_NAME    
            if 'name' in material:
                gltfMaterialName = material['name']
                materialName = MTLX_MATERIAL_PREFIX + gltfMaterialName
                shaderName = MTLX_SHADER_PREFIX + gltfMaterialName
                shaderName = gltfMaterialName
            shaderName = doc.createValidChildName(shaderName)
            materialName = doc.createValidChildName(materialName)
            # Overwrite name in glTF with generated name
            material['name'] = materialName

            # Create shader. Check if unlit shader is needed
            use_unlit = True if 'unlit' in material else False
            if 'extensions' in material:
                mat_extensions = material['extensions']
                if 'KHR_materials_unlit' in mat_extensions:
                    use_unlit = True

            shaderCategory = MTLX_UNLIT_CATEGORY_STRING if use_unlit else MTLX_GLTF_PBR_CATEGORY
            nodedefString = 'ND_surface_unlit' if use_unlit else 'ND_gltf_pbr_surfaceshader'
            comment = doc.addChildOfCategory('comment')
            comment.setDocString(' Generated shader: ' + shaderName + ' ')         
            shaderNode = doc.addNode(shaderCategory, shaderName, mx.SURFACE_SHADER_TYPE_STRING)
            shaderNode.setAttribute(mx.InterfaceElement.NODE_DEF_ATTRIBUTE, nodedefString)

            addInputsFromNodeDef = self._options['addAllInputs']
            if addInputsFromNodeDef:
                shaderNode.addInputsFromNodeDef()
            shaderNode.removeChild('tangent')
            shaderNode.removeChild('normal')

            # Create a surface material for the shader node
            comment = doc.addChildOfCategory('comment')
            comment.setDocString(' Generated material: ' + materialName + ' ')         
            materialNode = doc.addNode(mx.SURFACE_MATERIAL_NODE_STRING, materialName, mx.MATERIAL_TYPE_STRING)
            shaderInput = materialNode.addInput(mx.SURFACE_SHADER_TYPE_STRING, mx.SURFACE_SHADER_TYPE_STRING)
            shaderInput.setAttribute(MTLX_NODE_NAME_ATTRIBUTE, shaderNode.getName())

            if self._options['debugOutput']:
                print('- Convert gLTF material to MateriaLX: %s' % materialName)

            # Check for separate occlusion - TODO
            haveSeparateOcclusion = False

            # ----------------------------
            # Read in pbrMetallicRoughness
            # ----------------------------
            if 'pbrMetallicRoughness' in material:
                pbrMetallicRoughness = material['pbrMetallicRoughness']

                # Parse base color factor
                # -----------------------
                baseColorTexture = None
                if 'baseColorTexture' in pbrMetallicRoughness:
                    baseColorTexture = pbrMetallicRoughness['baseColorTexture']
                baseColorFactor = None
                if 'baseColorFactor' in pbrMetallicRoughness:
                    baseColorFactor = pbrMetallicRoughness['baseColorFactor']
                if baseColorTexture or baseColorFactor:
                    colorInputName = 'base_color'
                    alphaInputName = 'alpha'
                    if use_unlit:
                        colorInputName = 'emission_color'
                        alphaInputName = 'opacity'
                    imagename = 'image_' + colorInputName
                    self.readColorInput(doc, baseColorTexture, baseColorFactor, imagename, 
                                MTLX_GLTF_COLOR_IMAGE, MULTI_OUTPUT_TYPE_STRING, 
                                    '', shaderNode, colorInputName, alphaInputName, 
                                    textures, images, samplers, MTLX_DEFAULT_COLORSPACE)

                # Parse metallic factor
                # ---------------------
                if 'metallicFactor' in pbrMetallicRoughness:
                    metallicFactor = pbrMetallicRoughness['metallicFactor']
                    metallicFactor = str(metallicFactor)
                    metallicInput = shaderNode.addInputFromNodeDef('metallic')
                    metallicInput.setValueString(metallicFactor)
            
                # Parse roughness factor
                # ---------------------
                if 'roughnessFactor' in pbrMetallicRoughness:
                    roughnessFactor = pbrMetallicRoughness['roughnessFactor']
                    roughnessFactor = str(roughnessFactor)
                    roughnessInput = shaderNode.addInputFromNodeDef('roughness')
                    roughnessInput.setValueString(roughnessFactor)

                # Parse texture for metalic, roughness, and occlusion (if not specified separately)
                # ---------------------------------------------------------------------

                # Check for occlusion/metallic/roughness texture
                texture = None
                if 'metallicRoughnessTexture' in pbrMetallicRoughness:
                    texture = pbrMetallicRoughness['metallicRoughnessTexture']
                if texture:
                    imageNode = self.readInput(doc, texture, [], 'image_orm', MTLX_GLTF_IMAGE, MTLX_VEC3_STRING, '',
                                        shaderNode,  ['metallic', 'roughness', 'occlusion'], textures, images, samplers)
                    self.readGLTFImageProperties(imageNode, texture, samplers)

                    # Route individual channels on ORM image to the appropriate inputs on the shader
                    indexName = [ 'x', 'y', 'z' ]
                    outputName = [ 'outx', 'outy', 'outz' ]
                    metallicInput = shaderNode.addInputFromNodeDef('metallic')
                    roughnessInput = shaderNode.addInputFromNodeDef('roughness')
                    occlusionInput = None if haveSeparateOcclusion else shaderNode.addInputFromNodeDef('occlusion')
                    inputs = [ occlusionInput, roughnessInput, metallicInput ]
                    addSeparateNode = False # TODO: This options is not supported on write parsing yet.
                    addExtractNode = True
                    separateNode = None
                    if addSeparateNode:
                        # Add a separate node to route the channels
                        separateNodeName = doc.createValidChildName('separate_orm')
                        separateNode = doc.addNode('separate3', separateNodeName, 'multioutput')      
                        seperateInput = separateNode.addInputFromNodeDef('in')
                        seperateInput.setType('vector3')
                        seperateInput.setAttribute(MTLX_NODE_NAME_ATTRIBUTE, imageNode.getName())                  
                    for i in range(0,3): 
                        input = inputs[i]
                        if input:
                            input.setType('float') #mx.FLOAT_STRING
                            if addExtractNode:
                                extractNodeName = doc.createValidChildName('extract_orm')
                                extractNode = doc.addNode('extract', extractNodeName, 'float')
                                extractNode.addInputsFromNodeDef()
                                extractNodeInput = extractNode.getInput('in')
                                extractNodeInput.setType('vector3')    
                                extractNodeInput.removeAttribute('value')
                                extractNodeInput.setAttribute(MTLX_NODE_NAME_ATTRIBUTE, imageNode.getName())                                
                                extractNodeInput = extractNode.getInput('index')
                                extractNodeInput.setValue(i)

                                input.setAttribute(MTLX_NODE_NAME_ATTRIBUTE, extractNode.getName())
                            elif separateNode:
                                input.setAttribute(MTLX_NODE_NAME_ATTRIBUTE, separateNode.getName())
                                input.setOutputString(outputName[i])

            # Parse normal input
            # ------------------
            if 'normalTexture' in material:
                normalTexture = material['normalTexture']      
                self.readInput(doc, normalTexture, [], 'image_normal', MTLX_GLTF_NORMALMAP_IMAGE, MTLX_VEC3_STRING, '',
                        shaderNode, ['normal'], textures, images, samplers)

            # Parse occlusion input
            # ---------------------
            occlusionTexture = None
            if 'occlusionTexture' in material:
                occlusionTexture = material['occlusionTexture']
                self.readInput(doc, occlusionTexture, [], 'image_occlusion', MTLX_GLTF_IMAGE, 'float', '',
                        shaderNode, ['occlusion'], textures, images, samplers)

            # Parse emissive inputs
            # ----------------------
            emissiveTexture = None
            if 'emissiveTexture' in material:
                emissiveTexture = material['emissiveTexture']
            emissiveFactor = [0.0, 0.0, 0.0]
            if 'emissiveFactor' in material:
                emissiveFactor = material['emissiveFactor']
            self.readColorInput(doc, emissiveTexture, emissiveFactor, 'image_emissive',
                            MTLX_GLTF_COLOR_IMAGE, MULTI_OUTPUT_TYPE_STRING, 
                            '', shaderNode, 'emissive', '', textures, images, samplers, MTLX_DEFAULT_COLORSPACE)       
        
            # Parse and remap alpha mode
            # --------------------------
            if 'alphaMode' in material:
                alphaModeString = material['alphaMode']
                alphaMode = 0 
                if alphaModeString in alphaModeMap:
                    alphaMode = alphaModeMap[alphaModeString]
                if alphaMode != 0:
                    alphaModeInput = shaderNode.addInputFromNodeDef('alpha_mode')
                    alphaModeInput.setValue(alphaMode)

            # Parse alpha cutoff 
            # ------------------
            if 'alphaCutoff' in material:
                alphaCutOff = material['alphaCutoff']
                if alphaCutOff != 0.5:
                    alphaCutOffInput = shaderNode.addInputFromNodeDef('alpha_cutoff')
                    alphaCutOffInput.setValue(float(alphaCutOff))

            # Parse extensions
            # --------------------------------
            if 'extensions' in material:
                extensions = material['extensions']

                # Parse untextured ior extension
                # ------------------------------
                if 'KHR_materials_ior' in extensions:
                    iorExtension = extensions['KHR_materials_ior']
                    if  'ior' in iorExtension:
                        ior = iorExtension['ior']
                        iorInput = shaderNode.addInputFromNodeDef('ior')
                        iorInput.setValue(float(ior))

                # Parse specular and specular color extension
                if 'KHR_materials_specular' in extensions:
                    specularExtension = extensions['KHR_materials_specular']
                    specularColorFactor = None
                    if 'specularColorFactor' in specularExtension:
                        specularColorFactor = specularExtension['specularColorFactor']
                    specularColorTexture = None
                    if 'specularColorTexture' in specularExtension:
                        specularColorTexture = specularExtension['specularColorTexture']
                    if specularColorFactor or specularColorTexture:
                        self.readColorInput(doc, specularColorTexture, specularColorFactor, 'image_specularcolor',
                                MTLX_GLTF_COLOR_IMAGE, MULTI_OUTPUT_TYPE_STRING, 
                                '', shaderNode, 'specular_color', '', textures, images, MTLX_DEFAULT_COLORSPACE)

                    specularTexture = specularFactor = None
                    if 'specularFactor' in specularExtension:
                        specularFactor = specularExtension['specularFactor']
                    if 'specularTexture' in specularExtension:
                        specularTexture = specularExtension['specularTexture']
                    if specularFactor or specularTexture:
                        self.readInput(doc, specularTexture, [specularFactor], 'image_specular', MTLX_GLTF_IMAGE,
                                'float', '', shaderNode, ['specular'], textures, images, samplers)

                # Parse transmission extension        
                if 'KHR_materials_transmission' in extensions:
                    transmissionExtension = extensions['KHR_materials_transmission']
                    if 'transmissionFactor' in transmissionExtension:
                        transmissionFactor = transmissionExtension['transmissionFactor']
                        transmissionInput = shaderNode.addInputFromNodeDef('transmission')
                        transmissionInput.setValue(float(transmissionFactor)) 

                # Parse iridescence extension - TODO
                if 'KHR_materials_iridescence' in extensions:
                    iridescenceExtension = extensions['KHR_materials_iridescence']
                    if iridescenceExtension:

                        # Parse unmapped or mapped iridescence
                        iridescenceFactor = iridescenceTexture = None
                        if 'iridescenceFactor' in iridescenceExtension:
                            iridescenceFactor = iridescenceExtension['iridescenceFactor']
                        if 'iridescenceTexture' in iridescenceExtension:
                            iridescenceTexture = iridescenceExtension['iridescenceTexture']
                        if iridescenceFactor or iridescenceTexture:
                            self.readInput(doc, iridescenceTexture, [iridescenceFactor], 'image_iridescence', MTLX_GLTF_IMAGE,
                                    'float', '', shaderNode, ['iridescence'], textures, images, samplers)
                        
                        # Parse mapped or unmapped iridescence IOR
                        if 'iridescenceIor' in iridescenceExtension:
                            iridescenceIor = iridescenceExtension['iridescenceIor']
                            self.readInput(doc, None, [iridescenceIor], '', '',
                                    'float', '', shaderNode, ['iridescence_ior'], textures, images, samplers)
                        
                        # Parse iridescence texture
                        iridescenceThicknessMinimum = iridescenceExtension['iridescenceThicknessMinimum'] if 'iridescenceThicknessMinimum' in iridescenceExtension else None
                        iridescenceThicknessMaximum = iridescenceExtension['iridescenceThicknessMaximum'] if 'iridescenceThicknessMaximum' in iridescenceExtension else None
                        iridescenceThicknessTexture = iridescenceExtension['iridescenceThicknessTexture'] if 'iridescenceThicknessTexture' in iridescenceExtension else None
                        if iridescenceThicknessMinimum or iridescenceThicknessMaximum or iridescenceThicknessTexture:
                            floatInput = shaderNode.addInputFromNodeDef("iridescence_thickness")
                            if floatInput:
                                uri = ''
                                if iridescenceThicknessTexture:
                                    textureIndex = iridescenceThicknessTexture['index']
                                    texture = textures[textureIndex] if textureIndex < len(textures) else None
                                    uri = self.getGLTFTextureUri(texture, images)  
                                
                                    imageNodeName = doc.createValidChildName("image_iridescence_thickness")                            
                                    newTexture = self.addMtlxImage(doc, imageNodeName, uri, 'gltf_iridescence_thickness', '', 'float', '')
                                    if newTexture:
                                        floatInput.setAttribute(MTLX_NODE_NAME_ATTRIBUTE, newTexture.getName())
                                        floatInput.removeAttribute('value')

                                        if iridescenceThicknessMinimum:
                                            minInput = newTexture.addInputFromNodeDef("thicknessMin")
                                            if minInput:
                                                minInput.setValue(float(iridescenceThicknessMinimum))
                                        if iridescenceThicknessMaximum:
                                            maxInput = newTexture.addInputFromNodeDef("thicknessMax")
                                            if maxInput:
                                                maxInput.setValue(float(iridescenceThicknessMaximum))

                if 'KHR_materials_emissive_strength' in extensions:
                    emissiveStrengthExtension = extensions['KHR_materials_emissive_strength']
                    if 'emissiveStrength' in emissiveStrengthExtension:
                        emissiveStrength = emissiveStrengthExtension['emissiveStrength']                                        
                        self.readInput(doc, None, [emissiveStrength], '', '', '', '',
                                shaderNode, ['emissive_strength'], textures, images, samplers)

                # Parse volume Inputs:
                if 'KHR_materials_volume' in extensions:
                    volumeExtension = extensions['KHR_materials_volume']

                    # Textured or untexture thickness
                    thicknessFactor = thicknessTexture = None
                    if 'thicknessFactor' in volumeExtension:
                        thicknessFactor = volumeExtension['thicknessFactor']  
                    if 'thicknessTexture' in volumeExtension:
                        thicknessTexture = volumeExtension['thicknessTexture']
                    if thicknessFactor or thicknessTexture:                    
                        self.readInput(doc, thicknessTexture, [thicknessFactor], 'image_thickness', MTLX_GLTF_IMAGE, 'float', '',
                                shaderNode, ['thickness'], textures, images, samplers)

                    # Untextured attenuation color
                    if 'attenuationColor' in volumeExtension:
                        attenuationColor = volumeExtension['attenuationColor']
                        attenuationInput = shaderNode.addInputFromNodeDef('attenuation_color')
                        attenuationInput.setValue(mx.Color3(attenuationColor[0], attenuationColor[1], attenuationColor[2]))

                    # Untextured attenuation distance
                    if 'attenuationDistance' in volumeExtension:
                        attenuationDistance = volumeExtension['attenuationDistance']
                        attenuationDistance = str(attenuationDistance)
                        attenuationInput = shaderNode.addInputFromNodeDef('attenuation_distance')
                        attenuationInput.setValueString(attenuationDistance)

                # Parse clearcoat
                if 'KHR_materials_clearcoat' in extensions:
                    clearcoat = extensions['KHR_materials_clearcoat']

                    clearcoatFactor = clearcoatTexture = None
                    if 'clearcoatFactor' in clearcoat:
                        clearcoatFactor = clearcoat['clearcoatFactor']
                    if 'clearcoatTexture' in clearcoat:
                        clearcoatTexture = clearcoat['clearcoatTexture']
                    if clearcoatFactor or clearcoatTexture:
                        self.readInput(doc, clearcoatTexture, [clearcoatFactor], 'image_clearcoat', 
                                MTLX_GLTF_IMAGE, 'float', '', shaderNode, ['clearcoat'], 
                                textures, images, samplers)
                        
                    clearcoatRoughnessFactor = clearcoatRoughnessTexture = None
                    if 'clearcoatRoughnessFactor' in clearcoat:
                        clearcoatRoughnessFactor = clearcoat['clearcoatRoughnessFactor']
                    if 'clearcoatRoughnessTexture' in clearcoat:
                        clearcoatRoughnessTexture = clearcoat['clearcoatRoughnessTexture']
                    if clearcoatRoughnessFactor or clearcoatRoughnessTexture:
                        self.readInput(doc, clearcoatRoughnessTexture, [clearcoatRoughnessFactor], 
                                'image_clearcoat_roughness', 
                                MTLX_GLTF_IMAGE, 'float', '', shaderNode, ['clearcoat_roughness'], 
                                textures, images, samplers)
                        
                    if 'clearcoatNormalTexture' in clearcoat:
                        clearcoatNormalTexture = clearcoat['clearcoatNormalTexture']
                        self.readInput(doc, clearcoatNormalTexture, [None], 'image_clearcoat_normal', 
                                MTLX_GLTF_NORMALMAP_IMAGE, MTLX_VEC3_STRING, '',
                                shaderNode, ['clearcoat_normal'], textures, images, samplers)
                        
                # Parse sheen
                if 'KHR_materials_sheen' in extensions:
                    sheen = extensions['KHR_materials_sheen']

                    sheenColorFactor = sheenColorTexture = None
                    if 'sheenColorFactor' in sheen:
                        sheenColorFactor = sheen['sheenColorFactor']
                    if 'sheenColorTexture' in sheen:
                        sheenColorTexture = sheen['sheenColorTexture']
                    if sheenColorFactor or sheenColorTexture:
                        self.readColorInput(doc, sheenColorTexture, sheenColorFactor, 'image_sheen',
                                MTLX_GLTF_COLOR_IMAGE, MULTI_OUTPUT_TYPE_STRING, 
                                '', shaderNode, 'sheen_color', '', textures, images, MTLX_DEFAULT_COLORSPACE)
                        
                    sheenRoughnessFactor = sheenRoughnessTexture = None
                    if 'sheenRoughnessFactor' in sheen:
                        sheenRoughnessFactor = sheen['sheenRoughnessFactor']  
                    if 'sheenRoughnessTexture' in sheen:
                        sheenRoughnessTexture = sheen['sheenRoughnessTexture']
                    if sheenRoughnessFactor or sheenRoughnessTexture:                    
                        self.readInput(doc, sheenRoughnessTexture, [sheenRoughnessFactor], 'image_sheen_roughness', MTLX_GLTF_IMAGE, 'float', '',
                                shaderNode, ['sheen_roughness'], textures, images, samplers)

        return True

    def computeMeshMaterials(self, materialMeshList, materialCPVList, cnode, path, nodeCount, meshCount, meshes, nodes, materials):
        '''
        @brief Recursively computes mesh to material assignments.
        @param materialMeshList The dictionary of material to mesh assignments to update.
        @param materialCPVList The list of materials that require CPV.
        @param cnode The current node to examine.
        @param path The current string path to the node. If a node, mesh has no name then a default name is used. Primtives are named by index.
        @param nodeCount The current node count.
        @param meshCount The current mesh count.
        @param meshes The set of meshes to examine.
        @param nodes The set of nodes to examine.
        @param materials The set of materials to examine.
        '''
        
        # Push node name on to path
        prevPath = path
        cnodeName = ''
        if 'name' in cnode:
            cnodeName = cnode['name']
        else:    
            cnodeName =  GLTF_DEFAULT_NODE_PREFIX + str(nodeCount)
            nodeCount = nodeCount + 1
        path = path + '/' + ( mx.createValidName(cnodeName) )

        # Check if this node is associated with a mesh
        if 'mesh' in cnode:
            meshIndex = cnode['mesh']
            cmesh = meshes[meshIndex]
            if cmesh:

                # Append mesh name on to path
                meshName = ''
                if 'name' in cmesh:
                    meshName = cmesh['name']
                else:
                    meshName = self.GLTF_DEFAULT_MESH_PREFIX + str(meshCount)
                    meshCount = meshCount + 1
                path = path + '/' + mx.createValidName(meshName)

                if 'primitives' in cmesh:
                    primitives = cmesh['primitives']

                    # Check for material CPV attribute
                    requiresCPV = False
                    primitiveIndex = 0
                    for primitive in primitives:

                        material = None
                        if 'material' in primitive:
                            materialIndex = primitive['material']   
                            material = materials[materialIndex]

                        # Add reference to mesh (by name) to material
                        if material:
                            materialName = material['name']

                            if materialName not in materialMeshList:
                                materialMeshList[materialName] = []
                            if len(primitives) == 1:
                                materialMeshList[materialName].append(path)
                                #materialMeshList[materialName].append(path + '/' + GLTF_DEFAULT_PRIMITIVE_PREFIX + str(primitiveIndex))
                            else:
                                materialMeshList[materialName].append(path + '/' + GLTF_DEFAULT_PRIMITIVE_PREFIX + str(primitiveIndex))

                            if 'attributes' in primitive:
                                attributes = primitive['attributes']
                                if 'COLOR' in attributes:
                                    if self._options['debugOutput']:
                                        print('CPV attribute found')
                                    requiresCPV = True
                                    break
                            if requiresCPV:
                                materialCPVList.append(materialName)
                        
                        primitiveIndex = primitiveIndex + 1

        if 'children' in cnode:
            children = cnode['children']
            for childIndex in children:
                child = nodes[childIndex]
                self.computeMeshMaterials(materialMeshList, materialCPVList, child, path, nodeCount, meshCount, meshes, nodes, materials)

        # Pop path name
        path = prevPath

    def buildMaterialAssociations(self, gltfDoc) -> dict:
        '''
        @brief Build a dictionary of material assignments.
        @param gltfDoc The glTF document to read from.
        @return A dictionary of material assignments if successful, otherwise None.
        '''
        materials = gltfDoc['materials'] if 'materials' in gltfDoc else [] 
        meshes = gltfDoc['meshes'] if 'meshes' in gltfDoc else []
        
        if not materials or not meshes:
            return None
    
        meshNameTemplate = "mesh"
        meshCount = 0
        materialAssignments = {}
        for mesh in meshes:
            if 'primitives' in mesh:
                meshName = mesh['name'] if 'name' in mesh else meshNameTemplate + str(meshCount) 
                primitives = mesh['primitives']
                primitiveCount = 0
                for primitive in primitives:
                    if 'material' in primitive:
                        materialIndex = primitive['material']
                        if materialIndex < len(materials):
                            material = materials[materialIndex]                        
                            if 'name' in material:
                                materialName = material['name']
                                primitiveName = GLTF_DEFAULT_PRIMITIVE_PREFIX + str(primitiveCount)
                                if materialName not in materialAssignments:
                                    materialAssignments[materialName] = []
                                if len(primitives) == 1:
                                    materialAssignments[materialName].append(meshName)
                                else:                            
                                    materialAssignments[materialName].append(meshName + '/' + primitiveName)
                    primitiveCount += 1
            meshCount += 1        

        return materialAssignments

    def convert(self, gltfFileName) -> mx.Document:
        '''
        @brief Convert a glTF file to a MaterialX document.
        @param gltfFileName The glTF file to convert.
        @return A MaterialX document if successful, otherwise None.
        '''

        if not os.path.exists(gltfFileName):
            if self._options['debugOutput']:
                print('File not found:', gltfFileName)
            self.log('File not found:' + gltfFileName)
            return None

        gltfJson = None

        self.log('Read glTF file:' + gltfFileName)
        gltfFile = open(gltfFileName, 'r')
        gltfJson = None
        if gltfFile:
            gltfJson = json.load(gltfFile)
            gltfString = json.dumps(gltfJson, indent=2)
            self.log('GLTF JSON' + gltfString)
        if gltfJson:
            doc, libFiles = Util.createMaterialXDoc()
            self.glTF2MaterialX(doc, gltfJson)

            # Create a look and assign materials if found
            # TODO: Handle variants
            #assignments = buildMaterialAssociations(gltfJson)
            if False: #assignments:
                look = doc.addLook('look')
                for assignMaterial in assignments:
                    matassign = look.addMaterialAssign(MTLX_MATERIAL_PREFIX + assignMaterial)
                    matassign.setMaterial(MTLX_MATERIAL_PREFIX + assignMaterial)
                    matassign.setGeom(','.join(assignments[assignMaterial]))

            assignments = {}
            materialCPVList = {}
            meshes = gltfJson['meshes'] if 'meshes' in gltfJson else []
            nodes = gltfJson['nodes'] if 'nodes' in gltfJson else []
            scenes = gltfJson['scenes'] if 'scenes' in gltfJson else []
            if meshes and nodes and scenes:
                for scene in gltfJson['scenes']:
                    self.log('Scan scene for materials: ' + str(scene))
                    nodeCount = 0
                    meshCount = 0
                    path = ''
                    for nodeIndex in scene['nodes']:
                        node = nodes[nodeIndex]
                        self.computeMeshMaterials(assignments, materialCPVList, node, path, nodeCount, meshCount, meshes, nodes, gltfJson['materials'])

            # Add a CPV node if any assigned geometry has a color stream.
            for materialName in materialCPVList:
                materialNode = doc.getNode(materialName)
                shaderInput = materialNode.getInput('surfaceshader') if materialNode else None
                shaderNode = shaderInput.getConnectedNode() if shaderInput else None
                baseColorInput = shaderNode.getInput('base_color') if shaderNode else None
                baseColorNode = baseColorInput.getConnectedNode() if baseColorInput else None
                if baseColorNode:
                    geomcolorInput = baseColorNode.addInputFromNodeDef('geomcolor')
                    if geomcolorInput:
                        geomcolor = doc.addNode('geomcolor', EMPTY_STRING, 'color4')
                        geomcolorInput.setNodeName(geomcolor.getName())

            # Create a look and material assignments
            if self._options['createAssignments'] and len(assignments) > 0:
                comment = doc.addChildOfCategory('comment')
                comment.setDocString(' Generated material assignments ')
                look = doc.addLook('look')
                for assignMaterial in assignments:
                    matassign = look.addMaterialAssign(assignMaterial)
                    matassign.setMaterial(assignMaterial)
                    matassign.setGeom(','.join(assignments[assignMaterial]))

            return doc
        
##########################################################################################################################
# MaterialX to glTF conversion classes
##########################################################################################################################

class MTLX2GLTFOptions(dict):
    '''
    @brief Class to hold options for MaterialX to glTF conversion.

    Available options:
        - 'translateShaders' : Translate MaterialX shaders to glTF PBR shader. Default is False.   
        - 'bakeTextures' : Bake pattern graphs in MaterialX. Default is False.
        - 'bakeResolution' : Baked texture resolution if 'bakeTextures' is enabled. Default is 256.
        - 'packageBinary' : Package binary data in glTF. Default is False.
        - 'geometryFile' : Path to geometry file to use for glTF. Default is ''.
        - 'primsPerMaterial' : Create a new primitive per material in the MaterialX file and assign the material. Default is False.
        - 'searchPath' : Search path for files. Default is empty.
        - 'writeDefaultInputs' : Emit inputs even if they have default values. Default is False.
        - 'debugOutput' : Print debug output. Default is True.
    '''
    def __init__(self, *args, **kwargs):
        '''
        @brief Constructor.
        '''
        super().__init__(*args, **kwargs)

        self['translateShaders'] = False
        self['bakeTextures'] = False
        self['bakeResolution'] = 256
        self['packageBinary'] = False
        self['geometryFile'] = ''  
        self['primsPerMaterial'] = True     
        self['debugOutput'] = True
        self['createProceduralTextures'] = False
        self['searchPath'] = mx.FileSearchPath()
        self['writeDefaultInputs'] = False

class MTLX2GLTFWriter:
    '''
    @brief Class to read in a MaterialX document and write to a glTF document.
    '''

    # Log string
    _log = ''
    # Options
    _options = MTLX2GLTFOptions()
        
    def clearLog(self):
        '''
        @brief Clear the log.
        '''
        self._log = ''

    def getLog(self):
        '''
        @brief Get the log.
        '''
        return self._log
    
    def log(self, string):
        '''
        @brief Log a string.
        '''
        self._log += string + '\n'

    def setOptions(self, options):
        '''
        @brief Set options.
        @param options: The options to set.
        '''
        self._options = options

    def getOptions(self) -> MTLX2GLTFOptions:
        '''
        @brief Get the options for the reader.
        @return The options.
        '''
        return self._options

    def initialize_gtlf_texture(self, texture, name, uri, images) -> None:
        '''
        @brief Initialize a new gltF image entry and texture entry which references
        the image entry.

        @param texture: The glTF texture entry to initialize.
        @param name: The name of the texture entry.
        @param uri: The URI of the image entry.
        @param images: The list of images to append the new image entry to.
        '''
        image = {}
        image['name'] = name
        uriPath = mx.FilePath(uri)
        image['uri'] = uriPath.asString(mx.FormatPosix)
        images.append(image)

        texture['name'] = name
        texture['source'] = len(images) - 1

    def getShaderNodes(self, graphElement):
        '''
        @brief Find all surface shaders in a GraphElement.
        @param graphElement: The GraphElement to search for surface shaders.
        '''
        shaderNodes = set()
        for material in graphElement.getMaterialNodes():
            for shader in mx.getShaderNodes(material):
                shaderNodes.add(shader.getNamePath())
        for shader in graphElement.getNodes():
            if shader.getType() == 'surfaceshader':
                shaderNodes.add(shader.getNamePath())
        return shaderNodes


    def getRenderableGraphs(self, doc, graphElement):
        '''
        @brief Find all renderable graphs in a GraphElement.
        @param doc: The MaterialX document.
        @param graphElement: The GraphElement to search for renderable graphs.
        '''
        ngnamepaths = set()
        graphs = []
        shaderNodes = self.getShaderNodes(graphElement)
        for shaderPath in shaderNodes:
            shader = doc.getDescendant(shaderPath)
            for input in shader.getInputs():
                ngString = input.getNodeGraphString()
                if ngString and ngString not in ngnamepaths:
                    graphs.append(graphElement.getNodeGraph(ngString))
                    ngnamepaths.add(ngString)
        return graphs

    def copyGraphInterfaces(self, dest, ng, removeInternals):
        '''
        @brief Copy the interface of a nodegraph to a new nodegraph under a specified parent `dest`.
        @param dest: The parent nodegraph to copy the interface to.
        @param ng: The nodegraph to copy the interface from.
        @param removeInternals: Whether to remove internal nodes from the interface.
        '''
        copyMethod = 'add_remove'
        ng1 = dest.addNodeGraph(ng.getName())
        ng1.copyContentFrom(ng)
        removeInternals = False
        if removeInternals:
            for child in ng1.getChildren():
                if child.isA(mx.Input) or child.isA(mx.Output):
                    for attr in ['nodegraph', MTLX_NODE_NAME_ATTRIBUTE, 'defaultinput']:
                        child.removeAttribute(attr)
                    continue
                ng1.removeChild(child.getName())

    # Convert MaterialX element to JSON
    def elementToJSON(self, elem, jsonParent):
        '''
        @brief Convert an MaterialX XML element to JSON.
        Will recursively traverse the parent/child Element hierarchy.

        @param elem: The MaterialX element to convert.
        @param jsonParent: The parent JSON element to add the converted element to.
        '''
        if (elem.getSourceUri() != ''):
            return
        
        # Create a new JSON element for the MaterialX element
        jsonElem = {}

        # Add attributes
        for attrName in elem.getAttributeNames():
            jsonElem[attrName] = elem.getAttribute(attrName)

        # Add children
        for child in elem.getChildren():
            jsonElem = self.elementToJSON(child, jsonElem)
        
        # Add element to parent
        jsonParent[elem.getCategory() + self.JSON_CATEGORY_NAME_SEPARATOR + elem.getName()] = jsonElem
        return jsonParent

    # Convert MaterialX document to JSON
    def documentToJSON(self, doc):
        '''
        @brief Convert an MaterialX XML document to JSON
        @param doc: The MaterialX document to convert.
        '''
        root = {}
        root['materialx'] = {}

        for attrName in doc.getAttributeNames():
            root[attrName] =  doc.getAttribute(attrName)

        for elem in doc.getChildren():
            self.elementToJSON(elem, root[self.MATERIALX_DOCUMENT_ROOT])

        return root

    def stringToScalar(self, value, type) -> None:
        '''
        @brief Convert a string to a scalar value.
        @param value: The string value to convert.
        @param type: The type of the value.
        '''
        returnvalue = value

        if type in ['integer', 'matrix33', 'matrix44', 'vector2', 'vector3', 'vector3', 'float', 'color3', 'color4']:
            splitvalue = value.split(',')
            if len(splitvalue) > 1: 
                returnvalue = [float(x) for x in splitvalue]
            else:
                if type == 'integer':
                    returnvalue = int(value)
                else:
                    returnvalue = float(value)

        return returnvalue

    def graphToJson(self, graph, json, materials, textures, images, samplers):
        '''
        @brief Convert a MaterialX graph to JSON.
        @param graph: The MaterialX graph to convert.
        @param json: The JSON object to add the converted graph to.
        @param materials: The list of materials to append the new material to.
        @param textures: The list of textures to append new textures to.
        @param images: The list of images to append new images to.
        @param samplers: The list of samplers to append new samplers to.
        '''

        debug = False

        skipAttr = ['uiname', 'xpos', 'ypos' ] # etc
        procDict = dict()

        graphOutputs = []    
        procs = None
        extensions = None
        if 'extensions' not in json:
            extensions = json['extensions'] = {}
        extensions = json['extensions']
        khr_procedurals = None
        if 'KHR_procedurals' not in extensions:
            extensions['KHR_procedurals'] = {}
        khr_procedurals = extensions['KHR_procedurals']
        if 'procedurals' not in khr_procedurals:
            khr_procedurals['procedurals'] = []
        procs = khr_procedurals['procedurals']

        for node in graph.getNodes():
            jsonNode = {}
            jsonNode['name'] = node.getNamePath()
            procs.append(jsonNode)
            procDict[node.getNamePath()] = len(procs) - 1

        for input in graph.getInputs():
            jsonNode = {}
            jsonNode['name'] = input.getNamePath()
            jsonNode['nodetype'] = input.getCategory()
            if input.getValue() != None:
                
                # If it's a file name then create a texture
                inputType = input.getAttribute(mx.TypedElement.TYPE_ATTRIBUTE)
                jsonNode['type'] = inputType
                if  inputType == mx.FILENAME_TYPE_STRING:
                    texture = {}
                    filename = input.getValueString()                
                    self.initialize_gtlf_texture(texture, input.getNamePath(), filename, images)
                    textures.append(texture)
                    self.writeImageProperties(texture, samplers, node)
                    jsonNode['texture'] = len(textures) -1
                # Otherwise just set the value
                else:
                    value = input.getValueString()
                    value = self.stringToScalar(value, inputType)
                    jsonNode['value'] = value
            procs.append(jsonNode)
            procDict[jsonNode['name']] = len(procs) - 1

        for output in graph.getOutputs():
            jsonNode = {}
            jsonNode['name'] = output.getNamePath()
            procs.append(jsonNode)
            graphOutputs.append(jsonNode['name'])
            procDict[jsonNode['name']] = len(procs) - 1

        for output in graph.getOutputs():
            jsonNode = None
            index = procDict[output.getNamePath()]
            jsonNode = procs[index]
            jsonNode['nodetype'] = output.getCategory()

            outputString = connection = output.getAttribute('output')
            if len(connection) == 0:
                connection = output.getAttribute('interfacename')
            if len(connection) == 0:
                connection = output.getAttribute(MTLX_NODE_NAME_ATTRIBUTE)
            connectionNode = graph.getChild(connection)
            if connectionNode:
                #if self._options['debugOutput']:
                #    jsonNode['proceduralName'] = connectionNode.getNamePath()
                jsonNode['procedural'] = procDict[connectionNode.getNamePath()]
                if len(outputString) > 0:
                    jsonNode['output'] = outputString

            #procs.append(jsonNode)
            #graphOutputs.append(jsonNode['name'])
            #procDict[jsonNode['name']] = len(procs) - 1

        for node in graph.getNodes():
            jsonNode = None
            index = procDict[node.getNamePath()]
            jsonNode = procs[index]
            jsonNode['nodetype'] = node.getCategory()
            nodedef = node.getNodeDef()
            if debug and nodedef and len(nodedef.getNodeGroup()):
                jsonNode['nodegroup'] = nodedef.getNodeGroup() 
            for attrName in node.getAttributeNames():
                if attrName not in skipAttr:
                    jsonNode[attrName] = node.getAttribute(attrName)

            inputs = []
            for input in node.getInputs():

                inputItem = {}
                inputItem['name'] = input.getName()

                if input.getValue() != None:
                    # If it's a file name then create a texture
                    inputType = input.getAttribute(mx.TypedElement.TYPE_ATTRIBUTE)
                    inputItem['type'] = inputType
                    if  inputType == mx.FILENAME_TYPE_STRING:
                        texture = {}
                        filename = input.getValueString()                
                        self.initialize_gtlf_texture(texture, input.getNamePath(), filename, images)
                        textures.append(texture)
                        inputItem['texture'] = len(textures) -1
                        self.writeImageProperties(texture, samplers, node)
                    # Otherwise just set the value
                    else:
                        inputType = input.getAttribute(mx.TypedElement.TYPE_ATTRIBUTE)
                        value  = input.getValueString()
                        value = self.stringToScalar(value, inputType)    
                        inputItem['value'] = value                                       
                else:
                    connection = input.getAttribute('interfacename')
                    if len(connection) == 0:
                        connection = input.getAttribute(MTLX_NODE_NAME_ATTRIBUTE)
                    connectionNode = graph.getChild(connection)
                    if connectionNode:
                        inputType = input.getAttribute(mx.TypedElement.TYPE_ATTRIBUTE)
                        inputItem['type'] = inputType
                        if debug:
                            inputItem['proceduralName'] = connectionNode.getNamePath()
                        inputItem['procedural'] = procDict[connectionNode.getNamePath()]
                        outputString = input.getAttribute('output')
                        if len(outputString) > 0:
                            inputItem['output'] = outputString

                inputs.append(inputItem)

            if len(inputs) > 0:
                jsonNode['inputs'] = inputs

            #procs.append(jsonNode)
        
        addGraph = False
        if addGraph:
            jsonNode = {}
            jsonNode['name'] = graph.getNamePath()
            jsonNode['nodetype'] = 'graph'
            if False:
                inputs = {}
                for input in graph.getInputs():
                    if input.getValue() != None:
                        inputs[input.getName()] = input.getValueString()
                    else:
                        connection = input.getAttribute('output')
                        if len(connection) == 0:
                            connection = input.getAttribute('interfacename')
                        if len(connection) == 0:
                            connection = input.getAttribute('node')
                        #connectionNode = graph.getChild(connection)
                        #if connectionNode:
                        if len(connection) > 0:
                            inputs[input.getName()] = connection
                if len(inputs) > 0:
                    jsonGraph['inputs'] = inputs
        
                procs.append(jsonNode)
                procDict[jsonNode['name']] = len(procs) - 1 

        return graphOutputs, procDict

    def translateShader(self, shader, destCategory) -> bool:
        '''
        @brief Translate a MaterialX shader to a different category.
        @param shader: The MaterialX shader to translate.
        @param destCategory: The shader category to translate to.
        @return True if the shader was translated successfully, otherwise False.        
        '''

        shaderTranslator = mx_gen_shader.ShaderTranslator.create()
        try:
            if shader.getCategory() == destCategory:
                return True, ''
            shaderTranslator.translateShader(shader, MTLX_GLTF_PBR_CATEGORY)
        except mx.Exception as err:
            return False, err
        except LookupError as err:
            return False, err
        
        return True, ''

    def bakeTextures(self, doc, hdr, width, height, useGlslBackend, average, writeDocumentPerMaterial, outputFilename) -> None:
        '''
        @brief Bake all textures in a MaterialX document.
        @param doc: The MaterialX document to bake textures from.
        @param hdr: Whether to bake textures as HDR.
        @param width: The width of the baked textures.
        @param height: The height of the baked textures.
        @param useGlslBackend: Whether to use the GLSL backend for baking.
        @param average: Whether to average the baked textures.
        @param writeDocumentPerMaterial: Whether to write a separate MaterialX document per material.
        @param outputFilename: The output filename to write the baked document to.
        '''
        baseType = mx_render.BaseType.FLOAT if hdr else mx_render.BaseType.UINT8    
        
        if platform == 'darwin' and not useGlslBackend:
            baker = mx_render_msl.TextureBaker.create(width, height, baseType)
        else:
            baker = mx_render_glsl.TextureBaker.create(width, height, baseType)
        
        if not baker:
            return False
        
        if average:
            baker.setAverageImages(True)
        baker.writeDocumentPerMaterial(writeDocumentPerMaterial)
        baker.bakeAllMaterials(doc, self._options['searchPath'], outputFilename)  
        
        return True      
   
    def buildPrimPaths(self, primPaths, cnode, path, nodeCount, meshCount, meshes, nodes):
        '''
        @brief Recurse through a node hierarcht to build a dictionary of paths to primitives.
        @param primPaths: The dictionary of primitive paths to build.
        @param cnode: The current node to examine.
        @param path: The parent path to the node.
        @param nodeCount: The current node count.
        @param meshCount: The current mesh count.
        @param meshes: The list of meshes to examine.
        @param nodes: The list of nodes to examine.
        '''
        
        # Push node name on to path
        prevPath = path
        cnodeName = ''
        if 'name' in cnode:
            cnodeName = cnode['name']
        else:    
            cnodeName =  self.GLTF_DEFAULT_NODE_PREFIX + str(nodeCount)
            nodeCount = nodeCount + 1
        path = path + '/' + ( mx.createValidName(cnodeName) )

        # Check if this node is associated with a mesh
        if 'mesh' in cnode:
            meshIndex = cnode['mesh']
            cmesh = meshes[meshIndex]
            if cmesh:

                # Append mesh name on to path
                meshName = ''
                if 'name' in cmesh:
                    meshName = cmesh['name']
                else:
                    meshName = self.GLTF_DEFAULT_MESH_PREFIX + str(meshCount)
                    meshCount = meshCount + 1
                path = path + '/' + mx.createValidName(meshName)

                if 'primitives' in cmesh:
                    primitives = cmesh['primitives']

                    # Check for material CPV attribute
                    primitiveIndex = 0
                    for primitive in primitives:

                        primpath = path
                        if len(primitives) > 1:
                            primpath = + '/' + self.GLTF_DEFAULT_PRIMITIVE_PREFIX + str(primitiveIndex)
                        primPaths[primpath] = primitive
                        
                        primitiveIndex = primitiveIndex + 1

        if 'children' in cnode:
            children = cnode['children']
            for childIndex in children:
                child = nodes[childIndex]
                self.buildPrimPaths(primPaths, child, path, nodeCount, meshCount, meshes, nodes)

        # Pop path name
        path = prevPath    

    def createPrimsForMaterials(self, gltfJson, rowCount=10) -> None:
        '''
        @brief Create new meshes and nodes for each material in a glTF document.
        @param gltfJson: The glTF document to create new meshes and nodes for.
        @param rowCount: The number of meshes per row to create.
        @return None
        '''
        if not 'materials' in gltfJson:
            return
        nodes = None
        if 'nodes' in gltfJson:
            nodes = gltfJson['nodes']
        if not nodes:
            return
        if 'scenes' in gltfJson:
            scenes = gltfJson['scenes']
        if not scenes:
            return

        materials = gltfJson['materials']
        materialCount = len(materials)
        if  materialCount == 1:
            return
        
        if 'meshes' in gltfJson:
            meshes = gltfJson['meshes']

        MESH_POSTFIX = '_material_'
        translationX = 2.5
        translationY = 0

        meshCopies = []
        meshIndex = len(meshes) - 1 
        nodeCopies = []
        for materialId in range(1, materialCount):
            for mesh in meshes:
                if 'primitives' in mesh:
                    meshCopy = copy.deepcopy(mesh)
                    primitivesCopy = meshCopy['primitives']
                    for primitiveCopy in primitivesCopy:
                        # Overwrite the material for each prim
                        primitiveCopy['material'] = materialId
                    
                    meshCopy['name'] = mesh['name'] + MESH_POSTFIX + str(materialId)
                    meshCopies.append(meshCopy)
                    meshIndex = meshIndex + 1

                    newNode = {}
                    newNode['name'] = meshCopy['name']
                    newNode['mesh'] = meshIndex
                    newNode['translation'] = [translationX, translationY, 0]
                    nodeCopies.append(newNode)

            materialId = materialId + 1
            translationX = translationX + 2.5
            if materialId % rowCount == 0:
                translationX = 0
                translationY = translationY + 2.5

        meshes.extend(meshCopies)
        nodeCount = len(nodes)
        nodes.extend(nodeCopies)  
        scenenodes = scenes[0]['nodes']
        for i in range(nodeCount, len(nodes)):
            scenenodes.append(i)                

    def assignMaterial(self, doc, gltfJson) -> None:
        '''
        @brief Assign materials to meshes based on MaterialX looks (material assginments).
        The assignment is performed based on matching the MaterialX geometry paths to the glTF mesh primitive paths.
        @param doc: The MaterialX document containing looks.
        @param gltfJson: The glTF document to assign materials to.
        '''

        gltfmaterials = gltfJson['materials']
        if len(gltfmaterials) == 0:
            self.log('No materials in gltfJson')
            return

        meshes = gltfJson['meshes'] if 'meshes' in gltfJson else None
        if not meshes:
            self.log('No meshes in gltfJson')
            return
        nodes = gltfJson['nodes'] if 'nodes' in gltfJson else None
        if not nodes:
            self.log('No nodes in gltfJson')
            return
        scenes = gltfJson['scenes'] if 'scenes' in gltfJson else None
        if not scenes:
            self.log('No scenes in gltfJson')
            return

        primPaths = {}
        for scene in gltfJson['scenes']:
            nodeCount = 0
            meshCount = 0
            path = ''
            for nodeIndex in scene['nodes']:
                node = nodes[nodeIndex]
                self.buildPrimPaths(primPaths, node, path, nodeCount, meshCount, meshes, nodes)
        if not primPaths:
            return
        
        # Build a dictionary of material name to material array index
        materialIndexes = {}
        for index in range(len(gltfmaterials)):
            gltfmaterial = gltfmaterials[index]
            if 'name' in gltfmaterial:
                matName = MTLX_MATERIAL_PREFIX + gltfmaterial['name']
                materialIndexes[matName] = index

        # Scan through assignments in looks in order
        # if the materialname matches a meshhes' material name, then assign the material index to the mesh
        for look in doc.getLooks():
            materialAssigns = look.getMaterialAssigns()        
            for materialAssign in materialAssigns:
                materialName = materialAssign.getMaterial()
                if materialName in materialIndexes:
                    materialIndex = materialIndexes[materialName]
                    geomString = materialAssign.getGeom()
                    geomlist = geomString.split(',')

                    # Scan geometry list with primitive paths
                    for geomlistitem in geomlist:
                        if geomlistitem in primPaths:
                            prim = primPaths[geomlistitem]
                            if prim: 
                                self.log('assign material: ' + materialName + ' to mesh path: ' + geomlistitem)
                                prim['material'] = materialIndex
                                break
                else:
                    self.log('Cannot find material: ' + materialName + 'in scene materials' + materialIndexes)


    def writeImageProperties(self, texture, samplers, imageNode) -> None:
        '''
        @brief Write image properties of a MaterialX gltF image node to a glTF texture and sampler entry.
        @param texture: The glTF texture entry to write to.
        @param samplers: The list of samplers to append new samplers to.
        @param imageNode: The MaterialX glTF image node to examine.
        '''
        TO_RADIAN = 3.1415926535 / 180.0

        # Handle uvset index
        uvindex = None
        texcoordInput = imageNode.getInput('texcoord')
        if texcoordInput:
            texcoordNode = texcoordInput.getConnectedNode()
            if texcoordNode:
                uvindexInput = texcoordNode.getInput('index')
                if uvindexInput:
                    value = uvindexInput.getValue()
                    if value:
                        uvindex = value

        if uvindex:
            texture['texCoord'] = uvindex

        # Handle transform extension
        # See: https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Khronos/KHR_texture_transform/README.md
        
        offsetInputValue = None
        offsetInput = imageNode.getInput('offset')
        if offsetInput:
            offsetInputValue = offsetInput.getValue()
        
        rotationInputValue = None
        rotationInput = imageNode.getInput('rotate')
        if rotationInput:
            rotationInputValue = rotationInput.getValue()

        scaleInputValue = None
        scaleInput = imageNode.getInput('scale')
        if scaleInput:
            scaleInputValue = scaleInput.getValue()

        if uvindex or offsetInputValue or rotationInputValue or scaleInputValue:

            if not 'extensions' in texture:
                texture['extensions'] = {}
            extensions = texture['extensions']    
            transformExtension = extensions['KHR_texture_transform'] = {}

            if offsetInputValue:
                transformExtension['offset'] = [offsetInputValue[0], offsetInputValue[1]]
            if rotationInputValue:
                val = float(rotationInputValue)
                # Note: Rotation in glTF is in radians and degrees in MaterialX
                transformExtension['rotation'] = val * TO_RADIAN
            if scaleInputValue:
                transformExtension['scale'] = [scaleInputValue[0], scaleInputValue[1]]
            if uvindex:
                transformExtension['texCoord'] = uvindex

        # Handle sampler.
        # Based on: https://github.com/KhronosGroup/glTF/blob/main/specification/2.0/schema/sampler.schema.json
        uaddressInput = imageNode.addInputFromNodeDef('uaddressmode')
        uaddressInputValue = uaddressInput.getValue() if uaddressInput else None
        vaddressInput = imageNode.addInputFromNodeDef('vaddressmode')
        vaddressInputValue = vaddressInput.getValue() if vaddressInput else None
        filterInput = imageNode.addInputFromNodeDef('filtertype')
        filterInputValue = filterInput.getValue() if filterInput else None

        sampler = {}
        if uaddressInputValue or vaddressInputValue or filterInputValue:

            wrapMap = {}
            wrapMap['clamp'] = 33071
            wrapMap['mirror'] = 33648
            wrapMap['periodic'] = 10497

            if uaddressInputValue and uaddressInputValue in wrapMap:
                sampler['wrapS'] = wrapMap[uaddressInputValue]
            else:
                sampler['wrapS'] = 10497
            if vaddressInputValue and vaddressInputValue in wrapMap:
                sampler['wrapT'] = wrapMap[vaddressInputValue]
            else:
                sampler['wrapT'] = 10497

            filterMap = {}
            filterMap['closest'] = 9728
            filterMap['linear'] = 9986
            filterMap['cubic'] = 9729
            if filterInputValue and filterInputValue in filterMap:
                sampler['magFilter'] = 9729 # No real value so make this fixed.
                sampler['minFilter'] = filterMap[filterInputValue]

            # Add sampler to samplers list if an existing sampler with the same 
            # parameters does not exist. Otherwise append a new one. 
            # Set the 'sampler' index on the texture. 
            reuseSampler = False
            for i in range(len(samplers)):
                if sampler == samplers[i]:
                    texture['sampler'] = i
                    reuseSampler = True
                    break
            if not reuseSampler:
                samplers.append(sampler)
                texture['sampler'] = len(samplers) - 1

    def writeFloatInput(self, pbrNode, inputName, gltfTextureName, gltfValueName, material, textures, images, samplers, remapper=None):
        '''
        @brief Write a float input from a MaterialX pbr node to a glTF material entry.
        @param pbrNode: The MaterialX pbr node to examine.
        @param inputName: The name of the input on the pbr node
        @param gltfTextureName: The name of the texture entry to write to.
        @param gltfValueName: The name of the value entry to write
        @param material: The glTF material entry to write to.
        @param textures: The list of textures to append new textures to.
        @param images: The list of images to append new images to.
        @param samplers: The list of samplers to append new samplers to.
        @param remapper: A optional remapping map to remap MaterialX values to glTF values
        '''
        filename = EMPTY_STRING

        imageNode = pbrNode.getConnectedNode(inputName)
        if imageNode:
            fileInput = imageNode.getInput(mx.Implementation.FILE_ATTRIBUTE)
            filename = ''
            if fileInput and fileInput.getAttribute(mx.TypedElement.TYPE_ATTRIBUTE) == mx.FILENAME_TYPE_STRING:
                filename = fileInput.getResolvedValueString()
            if len(filename) == 0:
                imageNode = None

        if imageNode:
            texture = {}
            self.initialize_gtlf_texture(texture, imageNode.getNamePath(), filename, images)
            textures.append(texture)

            material[gltfTextureName]  = {}
            material[gltfTextureName]['index'] = len(textures) - 1

            self.writeImageProperties(texture, samplers, imageNode)

        else:
            value = pbrNode.getInputValue(inputName)
            if value != None:
                nodedef = pbrNode.getNodeDef()
                # Don't write default values, unless specified
                writeDefaultInputs= self._options['writeDefaultInputs']
                if nodedef and (writeDefaultInputs or nodedef.getInputValue(inputName) != value):
                    if remapper:
                        if value in remapper:
                            material[gltfValueName] = remapper[value]
                    else:
                        material[gltfValueName] = value
                #else:
                #    print('INFO: skip writing default value for:', inputName, value)
            #else:
            #    print('WARNING: Did not write value for:', inputName )

    def writeColor3Input(self, pbrNode, inputName, gltfTextureName, gltfValueName, material, textures, images, samplers):
        '''
        @brief Write a color3 input from a MaterialX pbr node to a glTF material entry.
        @param pbrNode: The MaterialX pbr node to examine.
        @param inputName: The name of the input on the pbr node
        @param gltfTextureName: The name of the texture entry to write to.
        @param gltfValueName: The name of the value entry to write
        @param material: The glTF material entry to write to.
        @param textures: The list of textures to append new textures to.
        @param images: The list of images to append new images to.
        @param samplers: The list of samplers to append new samplers to.
        '''

        filename = EMPTY_STRING

        imageNode = pbrNode.getConnectedNode(inputName)
        if imageNode:
            fileInput = imageNode.getInput(mx.Implementation.FILE_ATTRIBUTE)
            filename = ''
            if fileInput and fileInput.getAttribute(mx.TypedElement.TYPE_ATTRIBUTE) == mx.FILENAME_TYPE_STRING:
                filename = fileInput.getResolvedValueString()
            if len(filename) == 0:
                imageNode = None

        if imageNode:
            texture = {}
            self.initialize_gtlf_texture(texture, imageNode.getNamePath(), filename, images)
            textures.append(texture)

            material[gltfTextureName]  = {}
            material[gltfTextureName]['index'] = len(textures) - 1

            material[gltfValueName] = [1.0, 1.0, 1.0]

            self.writeImageProperties(texture, samplers, imageNode)
        else:
            value = pbrNode.getInputValue(inputName)
            if value:
                nodedef = pbrNode.getNodeDef()
                # Don't write default values
                writeDefaultInputs= self._options['writeDefaultInputs']
                if nodedef and (writeDefaultInputs or nodedef.getInputValue(inputName) != value):
                    material[gltfValueName] = [ value[0], value[1], value[2] ]


    def writeCopyright(self, doc, gltfJson):
        '''
        @brief Write a glTF document copyright information.
        @param doc: The MaterialX document to examine.
        @param gltfJson: The glTF document to write to.
        '''
        asset = None
        if 'asset' in gltfJson:
            asset = gltfJson['asset']
        else:
            asset = gltfJson['asset'] = {}
        asset['copyright'] = 'Copyright 2022-2024: Bernard Kwok.'
        asset['generator'] = 'MaterialX ' + doc.getVersionString() + ' to glTF 2.0 generator. https://github.com/kwokcb/materialxgltf'
        asset['version'] = '2.0'

    def materialX2glTF(self, doc, gltfJson, resetMaterials):
        '''
        @brief Convert a MaterialX document to glTF.
        @param doc: The MaterialX document to convert.
        @param gltfJson: The glTF document to write to.
        @param resetMaterials: Whether to clear any existing glTF materials.
        '''        
        pbrNodes = {}
        unlitNodes = {}

        addInputsFromNodeDef = self._options['writeDefaultInputs']

        for material in doc.getMaterialNodes():
            shaderNodes = mx.getShaderNodes(material)
            for shaderNode in shaderNodes:
                category = shaderNode.getCategory()
                path = shaderNode.getNamePath()
                if category == MTLX_GLTF_PBR_CATEGORY and path not in pbrNodes:
                    if addInputsFromNodeDef:
                        hasNormal = shaderNode.getInput('normal')
                        hasTangent = shaderNode.getInput('tangent')
                        shaderNode.addInputsFromNodeDef()
                        if not hasNormal:
                            shaderNode.removeChild('tangent')
                        if not hasTangent:
                            shaderNode.removeChild('normal')
                    pbrNodes[path] = shaderNode
                elif category == MTLX_UNLIT_CATEGORY_STRING and path not in unlitNodes:
                    if addInputsFromNodeDef:
                        hasNormal = shaderNode.getInput('normal')
                        hasTangent = shaderNode.getInput('tangent')
                        shaderNode.addInputsFromNodeDef()
                        if not hasNormal:
                            shaderNode.removeChild('tangent')
                        if not hasTangent:
                            shaderNode.removeChild('normal')                        
                    unlitNodes[path] = shaderNode

        materials_count = len(pbrNodes) + len(unlitNodes)
        if materials_count == 0:
            return

        self.writeCopyright(doc, gltfJson)
        materials = None
        if 'materials' in gltfJson and not resetMaterials:
            materials = gltfJson['materials']
        else:
            materials = gltfJson['materials'] = list()

        textures = None
        if 'textures' in gltfJson:
            textures = gltfJson['textures'] 
        else:
            textures = gltfJson['textures'] = list()

        images = None
        if 'images' in gltfJson:
            images = gltfJson['images'] 
        else:
            images = gltfJson['images'] = list()

        samplers = None
        if 'samplers' in gltfJson:
            samplers = gltfJson['samplers']
        else:
            samplers = gltfJson['samplers'] = list()

        # Get 'extensions used' element to fill in if extensions are used
        extensionsUsed = None
        if not 'extensionsUsed' in gltfJson:
            gltfJson['extensionsUsed'] = []
        extensionsUsed = gltfJson['extensionsUsed']

        # Write materials
        #
        COLOR_SEMANTIC = 'color'
        
        for name in unlitNodes:
            material = {}

            unlitExtension = 'KHR_materials_unlit'
            if not unlitExtension in extensionsUsed:
                extensionsUsed.append(unlitExtension)
            mat_extensions = material['extensions'] = {}
            mat_extensions[unlitExtension] = {}
            
            unlitNode = unlitNodes[name]
            material['name'] = name
            roughness = material['pbrMetallicRoughness'] = {}

            base_color_set = False
            base_color = [ 1.0, 1.0, 1.0, 1.0 ]

            imageNode = unlitNode.getConnectedNode('emission_color')
            filename = ''
            if imageNode:                         
                fileInput = imageNode.getInput(mx.Implementation.FILE_ATTRIBUTE)
                if fileInput and fileInput.getAttribute(mx.TypedElement.TYPE_ATTRIBUTE) == mx.FILENAME_TYPE_STRING:
                    filename = fileInput.getResolvedValueString() 
                                        
            if len(filename) == 0:
                imageNode = None

            if imageNode:
                texture = {}
                self.initialize_gtlf_texture(texture, imageNode.getNamePath(), filename, images)
                textures.append(texture)

                roughness['baseColorTexture'] = {}
                roughness['baseColorTexture']['index'] = len(textures) - 1

                self.writeImageProperties(texture, samplers, imageNode)

                # Pull off color from gltf_colorImage node
                color = unlitNode.getInputValue('emission_color')
                if color:
                    base_color[0] = color[0]
                    base_color[1] = color[1]
                    base_color[2] = color[2]
                    base_color_set = True
            
            else:
                color = unlitNode.getInputValue('emission_color')
                if color:
                    base_color[0] = color[0]
                    base_color[1] = color[1]
                    base_color[2] = color[2]
                    base_color_set = True

                value = unlitNode.getInputValue('opacity')
                if value:
                    base_color[3] = value
                    base_color_set = True

            if base_color_set:
                roughness['baseColorFactor'] = base_color        

            if base_color_set:
                roughness['baseColorFactor'] = base_color

            materials.append(material)

        for name in pbrNodes:
            material = {}
            
            # Setup extensions list
            extensions = None
            if not 'extensions' in material:
                material['extensions'] = {}
            extensions = material['extensions']
                
            pbrNode = pbrNodes[name]
            if self._options['debugOutput']:
                print('- Convert MaterialX node to glTF:', pbrNode.getNamePath())

            # Set material name
            material['name'] = name

            # Handle PBR metallic roughness
            # -----------------------------
            roughness = material['pbrMetallicRoughness'] = {}

            #  Handle base color
            base_color = [ 1.0, 1.0, 1.0, 1.0 ]
            base_color_set = False

            filename = ''
            imageNode = pbrNode.getConnectedNode('base_color')
            imageGraph = None
            if self._options['createProceduralTextures']:
                if imageNode:
                    if imageNode.getParent().isA(mx.NodeGraph):
                        imageGraph = imageNode.getParent()

            if imageGraph:
                if self._options['debugOutput']:
                    print('- Generate KHR procedurals for graph: ' + imageGraph.getName())
                self.log('- Generate KHR procedurals for graph: ' + imageGraph.getName())
                #dest = mx.createDocument()
                #removeInternals = False
                #copyGraphInterfaces(dest, imageGraph, removeInternals)

                extensionName = 'KHR_procedurals'
                if  extensionName not in extensionsUsed:
                    extensionsUsed.append(extensionName)             
                #if extensionName not in extensions:                          
                #    extensions[extensionName] = {}
                #outputExtension = extensions[extensionName]                

                #jsonGraph = documentToJSON(imageGraph)
                graphOutputs, procDict = self.graphToJson(imageGraph, gltfJson, materials, textures, images, samplers)
                outputs = imageGraph.getOutputs()
                if len(outputs) > 0:
                    connectionName = outputs[0].getNamePath()
                    inputBaseColor = pbrNode.getInput('base_color')
                    outputSpecifier = inputBaseColor.getAttribute('output')
                    if len(outputSpecifier) > 0:            
                        connectionName = imageGraph.getNamePath() + '/' + outputSpecifier

                    # Add extension to texture entry
                    baseColorEntry = roughness['baseColorTexture'] = {}
                    baseColorEntry['index'] = 0 # Q: What should this be ?
                    if 'extensions' not in baseColorEntry:
                        baseColorEntry['extensions'] = {}
                    extensions = baseColorEntry['extensions']
                    if extensionName not in extensions:                          
                        extensions[extensionName] = {}
                    procExtensions = extensions[extensionName]                
                    procExtensions['index'] = procDict[connectionName]

            else:            
                if imageNode:                         
                    fileInput = imageNode.getInput(mx.Implementation.FILE_ATTRIBUTE)
                    if fileInput and fileInput.getAttribute(mx.TypedElement.TYPE_ATTRIBUTE) == mx.FILENAME_TYPE_STRING:
                        filename = fileInput.getResolvedValueString() 
                                        
                if len(filename) == 0:
                    imageNode = None

                if imageNode:
                    texture = {}
                    self.initialize_gtlf_texture(texture, imageNode.getNamePath(), filename, images)
                    textures.append(texture)

                    roughness['baseColorTexture'] = {}
                    roughness['baseColorTexture']['index'] = len(textures) - 1

                    self.writeImageProperties(texture, samplers, imageNode)

                    # Pull off color from gltf_colorImage node
                    color = pbrNode.getInputValue('base_color')
                    if color:
                        base_color[0] = color[0]
                        base_color[1] = color[1]
                        base_color[2] = color[2]
                        base_color_set = True
                
                else:
                    color = pbrNode.getInputValue('base_color')
                    if color:
                        base_color[0] = color[0]
                        base_color[1] = color[1]
                        base_color[2] = color[2]
                        base_color_set = True

                    value = pbrNode.getInputValue('alpha')
                    if value:
                        base_color[3] = value
                        base_color_set = True

                if base_color_set:
                    roughness['baseColorFactor'] = base_color 
            
            # Handle metallic, roughness, occlusion
            # Handle partially mapped or when different channels map to different images
            # by merging into a single ORM image. Note that we save as BGR 24-bit fixed images
            # thus we scan by that order which results in an MRO image being written to disk.
            #roughness['metallicRoughnessTexture'] = {}
            metallicFactor = pbrNode.getInputValue('metallic')
            #if metallicFactor:
            #    roughness['metallicFactor'] = metallicFactor
            #    print('------------------------ set metallic', roughness['metallicFactor'],
            #          ' node:', pbrNode.getNamePath())
            #roughnessFactor = pbrNode.getInputValue('roughness')
            #if roughnessFactor:        
            #    roughness['roughnessFactor'] = roughnessFactor
            extractInputs = [ 'metallic', 'roughness', 'occlusion' ]
            filenames = [ EMPTY_STRING, EMPTY_STRING, EMPTY_STRING ]
            imageNamePaths = [ EMPTY_STRING, EMPTY_STRING, EMPTY_STRING ]
            roughnessInputs = [ 'metallicFactor', 'roughnessFactor', '' ]

            IN_STRING = 'in'
            ormNode= None
            imageNode = None
            extractCategory = 'extract'
            for e in range(0, 3):
                inputName = extractInputs[e]
                pbrInput = pbrNode.getInput(inputName)
                if pbrInput:
                    # Read past any extract node
                    connectedNode = pbrNode.getConnectedNode(inputName)
                    if connectedNode:
                        if connectedNode.getCategory() == extractCategory:
                            imageNode = connectedNode.getConnectedNode(IN_STRING)
                        else:
                            imageNode = connectedNode

                    if imageNode:
                        fileInput = imageNode.getInput(mx.Implementation.FILE_ATTRIBUTE)                    
                        filename = EMPTY_STRING
                        if fileInput and fileInput.getAttribute(mx.TypedElement.TYPE_ATTRIBUTE) == mx.FILENAME_TYPE_STRING:
                            filename = fileInput.getResolvedValueString()  
                        filenames[e] = filename
                        imageNamePaths[e] = imageNode.getNamePath()

                    # Write out constant factors. If there is an image node
                    # then ignore any value stored as the image takes precedence.
                    if len(roughnessInputs[e]):
                        value = pbrInput.getValue()
                        if value != None:
                            roughness[roughnessInputs[e]] = value
                        #else:
                        #    roughness[roughnessInputs[e]] = 1.0

                # Set to default 1.0
                #else:
                #    if len(roughnessInputs[e]):
                #        roughnessInputs[e] = 1.0

            # Determine how many images to export and if merging is required
            metallicFilename = mx.FilePath(filenames[0])
            roughnessFilename = mx.FilePath(filenames[1])
            occlusionFilename = mx.FilePath(filenames[2])
            metallicFilename = self._options['searchPath'].find(metallicFilename)
            roughnessFilename = self._options['searchPath'].find(roughnessFilename)
            occlusionFilename = self._options['searchPath'].find(occlusionFilename)            

            # if metallic and roughness match but occlusion differs, Then export 2 textures if found
            if metallicFilename == roughnessFilename:
                if roughnessFilename == occlusionFilename:
                    # All 3 are the same:
                    if not roughnessFilename.isEmpty():
                        print('- Append single ORM texture', roughnessFilename.asString())
                        texture = {}
                        self.initialize_gtlf_texture(texture, imageNamePaths[0], roughnessFilename.asString(mx.FormatPosix), images)
                        self.writeImageProperties(texture, samplers, imageNode)
                        textures.append(texture)

                        roughness['metallicRoughnessTexture']  = {}
                        roughness['metallicRoughnessTexture']['index'] = len(textures) - 1
                else:
                    # Metallic and roughness are the same
                    if not metallicFilename.isEmpty():
                        print('- Append single metallic-roughness texture', metallicFilename.asString())
                        texture = {}
                        self.initialize_gtlf_texture(texture, imageNamePaths[0], metallicFilename.asString(mx.FormatPosix), images)
                        self.writeImageProperties(texture, samplers, imageNode)
                        textures.append(texture)

                        roughness['metallicRoughnessTexture']  = {}
                        roughness['metallicRoughnessTexture']['index'] = len(textures) - 1                    

                    # Append separate occlusion texture
                    if not occlusionFilename.isEmpty():
                        print('- Append single occlusion texture', metallicFilename.asString())
                        texture = {}
                        self.initialize_gtlf_texture(texture, imageNamePaths[2], occlusionFilename.asString(mx.FormatPosix), images)
                        self.writeImageProperties(texture, samplers, imageNode)
                        textures.append(texture)

                        material['occlusionTexture']  = {}
                        material['occlusionTexture']['index'] = len(textures) - 1                    

            # Metallic and roughness do no match and one or both are images. Merge as necessary
            elif not metallicFilename.isEmpty() or not (roughnessFilename).isEmpty():
                loader = mx_render.StbImageLoader.create()
                handler = mx_render.ImageHandler.create(loader)
                handler.setSearchPath(self._options['searchPath'])
                if handler:
                    ormFilename = roughnessFilename if metallicFilename.isEmpty() else metallicFilename

                imageWidth = 0
                imageHeight = 0

                roughnessImage = handler.acquireImage(roughnessFilename) if not roughnessFilename.isEmpty() else None
                if roughnessImage:
                    imageWidth = max(roughnessImage.getWidth(), imageWidth)
                    imageHeight = max(roughnessImage.getHeight(), imageHeight)

                metallicImage = handler.acquireImage(metallicFilename) if not metallicFilename.isEmpty() else None
                if metallicImage:
                    imageWidth = max(metallicImage.getWidth(), imageWidth)
                    imageHeight = max(metallicImage.getHeight(), imageHeight)

                outputImage = None
                if (imageWidth * imageHeight) != 0:
                    color = mx.Color4(0.0)
                    outputImage = mx_render.createUniformImage(imageWidth, imageHeight, 
                                                               3, mx_render.BaseType.UINT8, color)

                    uniformRoughnessColor = 1.0
                    if 'roughnessFactor' in roughness:
                        uniformRoughnessColor = roughness['roughnessFactor']
                    if roughnessImage:
                        roughness['roughnessFactor'] = 1.0

                    uniformMetallicColor = 1.0
                    if 'metallicFactor' in roughness:
                        uniformMetallicColor = roughness['metallicFactor']
                    if metallicImage:
                        roughness['metallicFactor'] = 1.0

                    for y in range(0, imageHeight):
                        for x in range(0, imageWidth):
                            finalColor = outputImage.getTexelColor(x, y)
                            finalColor[1] = roughnessImage.getTexelColor(x, y)[0] if roughnessImage else uniformRoughnessColor
                            finalColor[2] = metallicImage.getTexelColor(x, y)[0] if metallicImage else uniformMetallicColor
                            outputImage.setTexelColor(x, y, finalColor)

                    ormFilename.removeExtension()
                    ormfilePath = ormFilename.asString(mx.FormatPosix) + '_combined.png'
                    flipImage = False
                    saved = loader.saveImage(ormfilePath, outputImage, flipImage)

                    uri = mx.FilePath(ormfilePath).getBaseName()
                    print('- Merged metallic-roughness to single texture:', uri, 'Saved: ', saved)
                    texture = {}
                    self.initialize_gtlf_texture(texture,  imageNode.getNamePath(), uri, images)
                    self.writeImageProperties(texture, samplers, imageNode)
                    textures.append(texture)

                    roughness['metallicRoughnessTexture']  = {}
                    roughness['metallicRoughnessTexture']['index'] = len(textures) - 1         

            # Handle normal
            filename = EMPTY_STRING
            imageNode = pbrNode.getConnectedNode('normal')
            if imageNode:
                # Read past normalmap node
                if imageNode.getCategory() == 'normalmap':
                    imageNode = imageNode.getConnectedNode(IN_STRING)
                if imageNode:
                    fileInput = imageNode.getInput(mx.Implementation.FILE_ATTRIBUTE)
                    filename = EMPTY_STRING
                    if fileInput and fileInput.getAttribute(mx.TypedElement.TYPE_ATTRIBUTE) == mx.FILENAME_TYPE_STRING:
                        filename = fileInput.getResolvedValueString()
                    if len(filename) == 0:
                        imageNode = None
            if imageNode:
                texture = {}
                self.initialize_gtlf_texture(texture, imageNode.getNamePath(), filename, images)
                textures.append(texture)

                material['normalTexture']  = {}
                material['normalTexture']['index'] = len(textures) - 1       
                    
                self.writeImageProperties(texture, samplers, imageNode)

            # Handle transmission extension
            outputExtension = {}
            self.writeFloatInput(pbrNode, 'transmission',
                            'transmissionTexture', 'transmissionFactor', outputExtension, textures, images, samplers)
            if len(outputExtension) > 0:
                extensionName = 'KHR_materials_transmission'
                extensions[extensionName] = outputExtension
                if  extensionName not in extensionsUsed:
                    extensionsUsed.append(extensionName)            

            # Handle specular color and specular extension
            imageNode = pbrNode.getConnectedNode('specular_color')
            imageGraph = None
            if imageNode:
                if imageNode.getParent().isA(mx.NodeGraph):
                    imageGraph = imageNode.getParent()

            # Procedural extension. WIP
            if imageGraph:
                extensionName = 'KHR_procedurals'
                if  extensionName not in extensionsUsed:
                    extensionsUsed.append(extensionName)   
                if extensionName not in extensions:                          
                    extensions[extensionName] = {}
                outputExtension = extensions[extensionName]                

                graphOutputs, procDict = self.graphToJson(imageGraph, gltfJson, materials, textures, images, samplers)
                outputs = imageGraph.getOutputs()
                if len(outputs) > 0:
                    connectionName = outputs[0].getNamePath()
                    inputBaseColor = pbrNode.getInput('specular_color')
                    outputSpecifier = inputBaseColor.getAttribute('output')
                    if len(outputSpecifier) > 0:            
                        connectionName = imageGraph.getNamePath() + '/' + outputSpecifier
                    outputExtension['specularColorTexture'] = procDict[connectionName]

            else: 
                outputExtension = {}
                self.writeColor3Input(pbrNode, 'specular_color', 
                                'specularColorTexture', 'specularColorFactor', outputExtension, textures, images, samplers)
                self.writeFloatInput(pbrNode, 'specular', 
                                'specularTexture', 'specularFactor', outputExtension, textures, images, samplers)
                if len(outputExtension) > 0: 
                    extensionName = 'KHR_materials_specular'
                    if  extensionName not in extensionsUsed:
                        extensionsUsed.append(extensionName)             
                    extensions[extensionName] = outputExtension

            # Handle emission
            self.writeColor3Input(pbrNode, 'emissive', 
                            'emissiveTexture', 'emissiveFactor', material, textures, images, samplers)

            # Handle emissive strength extension
            outputExtension = {}
            self.writeFloatInput(pbrNode, 'emissive_strength', 
                            '', 'emissiveStrength', outputExtension, textures, images, samplers) 
            if len(outputExtension) > 0: 
                extensionName = 'KHR_materials_emissive_strength'
                if  extensionName not in extensionsUsed:
                    extensionsUsed.append(extensionName)             
                extensions[extensionName] = outputExtension

            # Handle ior extension
            outputExtension = {}
            self.writeFloatInput(pbrNode, 'ior', 
                            '', 'ior', outputExtension, textures, images, samplers) 
            if len(outputExtension) > 0: 
                extensionName = 'KHR_materials_ior'        
                if  extensionName not in extensionsUsed:
                    extensionsUsed.append(extensionName)             
                extensions[extensionName] = outputExtension

            # Handle sheen color
            outputExtension = {}
            self.writeColor3Input(pbrNode, 'sheen_color', 
                            'sheenColorTexture', 'sheenColorFactor', outputExtension, textures, images, samplers)
            self.writeFloatInput(pbrNode, 'sheen_roughness', 
                            'sheenRoughnessTexture', 'sheenRoughnessFactor', outputExtension, textures, images, samplers) 
            if len(outputExtension) > 0: 
                extensionName = 'KHR_materials_sheen'        
                if  extensionName not in extensionsUsed:
                    extensionsUsed.append(extensionName)             
                extensions[extensionName] = outputExtension

            # Handle clearcloat
            outputExtension = {}
            self.writeFloatInput(pbrNode, 'clearcoat', 
                            'clearcoatTexture', 'clearcoatFactor', outputExtension, textures, images, samplers) 
            self.writeFloatInput(pbrNode, 'clearcoat_roughness', 
                            'clearcoatRoughnessTexture', 'clearcoatRoughnessFactor', outputExtension, textures, images, samplers) 
            if len(outputExtension) > 0: 
                extensionName = 'KHR_materials_clearcoat'        
                if  extensionName not in extensionsUsed:
                    extensionsUsed.append(extensionName)             
                extensions[extensionName] = outputExtension

            # Handle KHR_materials_volume extension
            # - Parse thickness
            outputExtension = {}           
            thicknessInput = pbrNode.getInput('thickness')
            if thicknessInput:

                thicknessNode = thicknessInput.getConnectedNode()
                thicknessFileName = EMPTY_STRING
                if thicknessNode:
                    fileInput = thicknessNode.getInput(mx.Implementation.FILE_ATTRIBUTE)
                    if fileInput and fileInput.getAttribute(mx.TypedElement.TYPE_ATTRIBUTE) == mx.FILENAME_TYPE_STRING:
                        thicknessFileName = fileInput.getResolvedValueString()

                if len(thicknessFileName) > 0:
                    texture = {}
                    self.initialize_gtlf_texture(texture, thicknessNode.getNamePath(), thicknessFileName, images)
                    textures.append(texture)

                    outputExtension['thicknessTexture']  = {}
                    outputExtension['thicknessTexture']['index'] = len(textures) - 1     
                else:
                    thicknessValue = thicknessInput.getValue() 
                    if thicknessValue:
                        outputExtension['thicknessFactor'] = thicknessValue

            # Parse attenuation and attenuation distance
            attenuationInput = pbrNode.getInput('attenuation_color')
            if attenuationInput:
                attenuationValue = attenuationInput.getValue() 
                if attenuationValue:
                    inputType = attenuationInput.getAttribute(mx.TypedElement.TYPE_ATTRIBUTE)
                    outputExtension['attenuationColor'] = self.stringToScalar(attenuationInput.getValueString(), inputType)
            attenuationInput = pbrNode.getInput('attenuation_distance')
            if attenuationInput:
                attenuationValue = attenuationInput.getValue() 
                if attenuationValue:
                    outputExtension['attenuationDistance'] = attenuationValue

            if len(outputExtension) > 0: 
                extensionName = 'KHR_materials_volume'        
                if  extensionName not in extensionsUsed:
                    extensionsUsed.append(extensionName)             
                extensions[extensionName] = outputExtension

            # Handle clearcoat normal
            filename = EMPTY_STRING
            imageNode = pbrNode.getConnectedNode('clearcoat_normal')
            if imageNode:
                # Read past normalmap node
                if imageNode.getCategory() == 'normalmap':
                    imageNode = imageNode.getConnectedNode(IN_STRING)
                if imageNode:
                    fileInput = imageNode.getInput(mx.Implementation.FILE_ATTRIBUTE)
                    filename = EMPTY_STRING
                    if fileInput and fileInput.getAttribute(mx.TypedElement.TYPE_ATTRIBUTE) == mx.FILENAME_TYPE_STRING:
                        filename = fileInput.getResolvedValueString() 
                    if filename == EMPTY_STRING:
                        imageNode = None
                if imageNode:
                    texture = {}
                    self.initialize_gtlf_texture(texture, imageNode.getNamePath(), filename, images)
                    self.writeImageProperties(texture, samplers, imageNode)
                    textures.append(texture)

                    outputExtension['clearcoatNormalTexture']  = {}
                    outputExtension['clearcoatNormalTexture']['index'] = len(textures) - 1       
                
            # Handle alphA mode, cutoff
            alphModeInput = pbrNode.getInput('alpha_mode')
            if alphModeInput:
                value = alphModeInput.getValue()

                alphaModeMap = {}
                alphaModeMap[0] = 'OPAQUE'
                alphaModeMap[1] = 'MASK'
                alphaModeMap[2] = 'BLEND'
                self.writeFloatInput(pbrNode, 'alpha_mode', '', 'alphaMode', material, textures, images, samplers, alphaModeMap)
                if value == 'MASK':
                    self.writeFloatInput(pbrNode, 'alpha_cutoff', '', 'alphaCutoff', material, textures, images, samplers)


            # Handle iridescence
            outputExtension = {}
            self.writeFloatInput(pbrNode, 'iridescence',
                            'iridescenceTexture', 'iridescenceFactor', outputExtension, textures, images, samplers)
            self.writeFloatInput(pbrNode, 'iridescence_ior',
                            'iridescenceTexture', 'iridescenceIor', outputExtension, textures, images, samplers)
            if len(outputExtension) > 0: 
                extensionName = 'KHR_materials_iridescence'
                if  extensionName not in extensionsUsed:
                    extensionsUsed.append(extensionName)             
                extensions[extensionName] = outputExtension
                
            # Scan for upstream <gltf_iridescence_thickness> node.
            # Note: This is the agreed upon upstream node to create to map
            # to gltf_pbr as part of the core implementation. It basically
            # represents this structure: 
            # https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Khronos/KHR_materials_iridescence/README.md
            thicknessInput = pbrNode.getInput('iridescence_thickness')
            if thicknessInput:

                thicknessNode = thicknessInput.getConnectedNode()
                thicknessFileName = mx.FilePath()
                if thicknessNode:
                    fileInput = thicknessNode.getInput(mx.Implementation.FILE_ATTRIBUTE)
                    thicknessFileName = EMPTY_STRING
                    if fileInput and fileInput.getAttribute(mx.TypedElement.TYPE_ATTRIBUTE) == mx.FILENAME_TYPE_STRING:
                        thicknessFileName = fileInput.getResolvedValueString()

                        texture = {}
                        self.initialize_gtlf_texture(texture, thicknessNode.getNamePath(), thicknessFileName, images)
                        textures.append(texture)

                        outputExtension['iridescenceThicknessTexture']  = {}
                        outputExtension['iridescenceThicknessTexture']['index'] = len(textures) - 1     

                        thickessInput = thicknessNode.getInput('thicknessMin')
                        thicknessValue = thickessInput.getValue() if thickessInput else None
                        if thicknessValue:
                            outputExtension['iridescenceThicknessMinimum'] = thicknessValue
                        thickessInput = thicknessNode.getInput('thicknessMax')
                        thicknessValue = thickessInput.getValue() if thickessInput else None
                        if thicknessValue:
                            outputExtension['iridescenceThicknessMaximum'] = thicknessValue

            if len(material['extensions']) == 0:
                del material['extensions']

            materials.append(material)

        # Remove any empty items to avoid validation errors
        if len(gltfJson['extensionsUsed']) == 0:
            del gltfJson['extensionsUsed']
        if len(gltfJson['samplers']) == 0:
            del gltfJson['samplers']
        if len(gltfJson['images']) == 0:
            del gltfJson['images']
        if len(gltfJson['textures']) == 0:
            del gltfJson['textures']

    def packageGLTF(self, inputFile, outputFile):
        '''
        @brief Package gltf file into a glb file
        @param inputFile gltf file to package
        @param outputFile Packaged glb file
        @return status, image list, buffer list.
        '''
        images = []
        buffers = []

        # Load the gltf file
        gltfb = GLTF2() 
        gltf = gltfb.load(inputFile)
        if not gltf:
            return False, images 

        # Embed images
        if len(gltf.images):
            for im in gltf.images:
                searchPath = self._options['searchPath']
                path = searchPath.find(im.uri)
                path = searchPath.find(im.uri)
                if path:
                    im.uri = path.asString(mx.FormatPosix)                    
                    self.log('- Remapped buffer URI to: ' + im.uri) 
                images.append(im.uri)
            gltf.convert_images(ImageFormat.DATAURI)

        # Embed buffer references.
        # If the input file is not in the same folder as the current working directory,
        # then modify the buffer uri to be an absolute path.
        if len(gltf.buffers):
            absinputFile = os.path.abspath(inputFile)
            parentFolder = os.path.dirname(absinputFile)
            for buf in gltf.buffers:
                searchPath = self._options['searchPath']
                path = searchPath.find(buf.uri)
                if path:
                    buf.uri = path.asString(mx.FormatPosix)                    
                    self.log('- Remapped buffer URI to: ' + buf.uri) 
                buffers.append(buf.uri)
        gltfb.convert_buffers(BufferFormat.BINARYBLOB)            

        saved = gltf.save(outputFile)
        return saved, images, buffers

    def translateShaders(self, doc):
        '''
        @brief Translate shaders to gltf pbr 
        @param doc MaterialX document to examine
        @return Number of shaders translated
        '''
        shadersTranslated = 0
        if not doc:
            return shadersTranslated

        materialNodes = doc.getMaterialNodes()
        for material in materialNodes:
            shaderNodes = mx.getShaderNodes(material)
            for shaderNode in shaderNodes:
                category = shaderNode.getCategory()
                path = shaderNode.getNamePath()
                if category != MTLX_GLTF_PBR_CATEGORY and category != MTLX_UNLIT_CATEGORY_STRING:
                    status, error = self.translateShader(shaderNode, MTLX_GLTF_PBR_CATEGORY)
                    if not status:
                        self.log('Failed to translate shader:' + shaderNode.getNamePath() + 
                            ' of type ' + shaderNode.getCategory())
                        # + '\nError: ' + error.error)
                    else:
                        shadersTranslated = shadersTranslated + 1
        
        return shadersTranslated

    def convert(self, doc):
        '''
        @brief Convert MaterialX document to glTF
        @param doc MaterialX document to convert
        @return glTF JSON string
        '''
        # Resulting glTF JSON string        
        gltfJson = {}

        # Check for glTF geometry file inclusion
        gltfGeometryFile = self._options['geometryFile']
        if len(gltfGeometryFile):
            print('- glTF geometry file:' + gltfGeometryFile)
            if os.path.exists(gltfGeometryFile):
                gltfFile = open(gltfGeometryFile, 'r')
                if gltfFile:
                    gltfJson = json.load(gltfFile)
                if self._options['debugOutput']:
                    print('- Embedding glTF geometry file:' + gltfGeometryFile)
                self.log('- Embedding glTF geometry file:' + gltfGeometryFile)

                # If no materials, add a default material
                for mesh in gltfJson['meshes']:
                    for primitive in mesh['primitives']:
                        if 'material' not in primitive:
                            primitive['material'] = 0
            else:
                if self._options['debugOutput']:
                    print('- glTF geometry file not found:' + gltfGeometryFile)
                self.log('- glTF geometry file not found:' + gltfGeometryFile)

        # Clear and convert materials
        resetMaterials = True
        self.materialX2glTF(doc, gltfJson, resetMaterials)
        
        # If geometry specified, create new primitives for each material
        materialCount = len(gltfJson['materials']) if 'materials' in gltfJson else 0
        if self._options['primsPerMaterial'] and (materialCount > 0):
            if self._options['debugOutput']:
                print('- Generating a new primitive for each of %d materials' % materialCount)
            # Compute sqrt of materialCount
            rowCount = int(math.sqrt(materialCount))
            self.createPrimsForMaterials(gltfJson, rowCount)

        # Get resulting glTF JSON string
        gltfString = json.dumps(gltfJson, indent=2)
        self.log('- Output glTF with new MaterialX materials' + str(gltfString))

        return gltfString
    
