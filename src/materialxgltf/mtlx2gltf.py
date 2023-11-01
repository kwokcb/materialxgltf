#!/usr/bin/env python
'''
Utility and command line interface to convert from a MaterialX file to a glTF file 
'''
import os
import argparse

from materialxgltf.core import *

def mtlx2gltf(materialXFileName, gltfOutputFileName, options=MTLX2GLTFOptions()):
    '''
    Utility to convert a MaterialX file to glTF file
    @param materialXFileName Path to MaterialX file to convert
    @param gltfOutputFileName Path to glTF file to write
    @param options Options for conversion
    '''
    searchPath = mx.getDefaultDataSearchPath()

    mtlx2glTFWriter = MTLX2GLTFWriter()
    doc, libFiles = Util.createMaterialXDoc()
    if libFiles:
        print('- Loaded %d library files.' % len(libFiles))
    else:
        print('- No library files loaded.')
    mx.readFromXmlFile(doc, materialXFileName, searchPath)

    # Perform shader translation and baking if necessary
    if options['translateShaders']:
        translatedCount = mtlx2glTFWriter.translateShaders(doc)
        print('- Translated %d shaders.' % translatedCount)
        if options['bakeTextures']:
            materialXFileName = materialXFileName + '_baked.mtlx'
            bakeResolution = 256
            if options['bakeResolution']:
                bakeResolution = options['bakeResolution']
            mtlx2glTFWriter.bakeTextures(doc, False, bakeResolution, bakeResolution, False, 
                                        False, False, searchPath, materialXFileName)
            print('- Baked textures to: ', materialXFileName)
            doc, libFiles = Util.createMaterialXDoc()
            mx.readFromXmlFile(doc, materialXFileName, searchPath)
            remappedUris = Util.makeFilePathsRelative(doc, materialXFileName)
            for uri in remappedUris:
                print('  - Remapped URI: %s to %s' % (uri[0], uri[1]))

    mtlx2glTFWriter.setOptions(options)
    gltfString = mtlx2glTFWriter.convert(doc)
    if len(gltfString) > 0:
        print('> Write glTF to: ', gltfOutputFileName)
        f = open(gltfOutputFileName, 'w')
        f.write(gltfString)
        f.close()
    else:
        return False, mtlx2glTFWriter.getLog()

    if options['packageBinary']:
        binaryFileName = str(gltfOutputFileName)
        binaryFileName = binaryFileName.replace('.gltf', '.glb')
        print('- Packaging GLB file...')
        saved, images, buffers = mtlx2glTFWriter.packageGLTF(gltfOutputFileName, binaryFileName)
        print('- Save GLB file:' + binaryFileName + '. Status:' + str(saved))
        for image in images:
            print('  - Embedded image: %s' % image)
        for buffer in buffers:
            print('  - Embedded buffer: %s' % buffer)

    return True, ''

def main():
    '''
    Command line utility to convert a MaterialX file to a glTF file
    '''
    parser = argparse.ArgumentParser(description='Utility to convert a MaterialX file to a glTF file')
    parser.add_argument(dest='mtlxFileName', help='Path containing MaterialX file to convert.')
    parser.add_argument('--gltfFileName', dest='gltfFileName', default='', help='Name of MaterialX output file. If not specified the glTF name with "_tomtlx.mtlx" suffix will be used')
    parser.add_argument('--gltfGeomFileName', dest='gltfGeomFileName', default='', help='Name of MaterialX output file. If not specified the glTF name with "_tomtlx.mtlx" suffix will be used')
    parser.add_argument('--primsPerMaterial', dest='primsPerMaterial', type=mx.stringToBoolean, default=False, help='Create a new primitive per material and assign the material. Default is False')
    parser.add_argument('--packageBinary', dest='packageBinary', type=mx.stringToBoolean, default=False, help='Create a biary packaged GLB file. Default is False')
    parser.add_argument('--translateShaders', dest='translateShaders', type=mx.stringToBoolean, default=False, help='Translate shaders to glTF. Default is False')
    parser.add_argument('--bakeTextures', dest='bakeTextures', type=mx.stringToBoolean, default=False, help='Bake pattern graphs as textures. Default is False')
    parser.add_argument('--bakeResolution', dest='bakeResolution', type=int, default=256, help='Bake image resolution. Default is 256')

    opts = parser.parse_args()

    # Check input glTF file
    mtlxFileName = opts.mtlxFileName
    if not os.path.exists(mtlxFileName):
        print('Cannot find input file: ', mtlxFileName)
        exit(-1)    

    # Set up MTLX file name
    gltfFileName = mtlxFileName + '.gltf'
    if len(opts.gltfFileName) > 0:
        gltfFileName = opts.gltfFileName 

    # Perform conversion
    options = MTLX2GLTFOptions()
    options['primsPerMaterial'] = opts.primsPerMaterial
    options['packageBinary'] = opts.packageBinary
    options['geometryFile'] = opts.gltfGeomFileName
    options['translateShaders'] = opts.translateShaders
    options['bakeTextures'] = opts.bakeTextures
    options['bakeResolution'] = opts.bakeResolution
    converted, err = mtlx2gltf(mtlxFileName, gltfFileName, options)
    print('Converted MaterialX file %s to gltf file: %s. Status: %s.' % (mtlxFileName, gltfFileName, converted))
    if not converted:
        print('- Error: ', err)

if __name__ == "__main__":
    main()