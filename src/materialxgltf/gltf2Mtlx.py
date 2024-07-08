#!/usr/bin/env python
'''
Utility and command line interface to convert from a glTF file to a MaterialX file 
'''
import os
import argparse

#import MaterialX as mx
#from materialxgltf.core import *
from core import *

def gltf2Mtlx(gltfFileName, mtlxFileName, options=GLTF2MtlxOptions()):
    '''
    @brief Utility to convert a glTF file to MaterialX file

    @param gltfFileName Path to glTF file to convert
    @param mtlxFileName Path to MaterialX file to write
    @param options Options for conversion
    '''
    status = True
    err = ''

    gltf2MtlxReader = GLTF2MtlxReader()
    gltf2MtlxReader.setOptions(options)
    doc = gltf2MtlxReader.convert(gltfFileName)
    if not doc:
        status = False
        err = 'Error converting glTF file to MaterialX file'
    else:
        status, err = doc.validate()
        if not status:
            print('Validation error: ', err)
        #print(mx.writeToXmlString(doc))
        Util.writeMaterialXDoc(doc, mtlxFileName)

    return status, err

def main():
    '''
    @brief Command line interface to convert from a glTF file to a MaterialX file
    '''
    parser = argparse.ArgumentParser(description='Utility to convert a glTF file to MaterialX file')
    parser.add_argument(dest='gltfFileName', help='Path containing glTF file to convert.')
    parser.add_argument('--mtlxFileName', dest='mtlxFileName', default='', help='Name of MaterialX output file. If not specified the glTF name with "_tomtlx.mtlx" suffix will be used')
    parser.add_argument('--createAssignments', dest='createAssignments', type=mx.stringToBoolean, default=True, help='Create material assignments. Default is True')
    parser.add_argument('--addAllInputs', dest='addAllInputs', type=mx.stringToBoolean, default=False, help='Add all definition inputs to MaterialX shader nodes. Default is False')

    opts = parser.parse_args()

    # Check input glTF file
    gltfFileName = opts.gltfFileName
    if not os.path.exists(gltfFileName):
        print('Cannot find input file: ', gltfFileName)
        exit(-1)    

    # Set up MTLX file name
    mtlxFilePath = gltfFileName + '_converted.mtlx'
    if opts.mtlxFileName:
        mtlxFilePath = opts.mtlxFileName 

    # Perform conversion
    options = GLTF2MtlxOptions()
    options['createAssignments'] = opts.createAssignments    
    options['addAllInputs'] = opts.addAllInputs
    converted, err = gltf2Mtlx(gltfFileName, mtlxFilePath, options)
    print('Converted glTF file %s to MaterialX file: %s. Status: %s.' % (gltfFileName, mtlxFilePath, converted))
    if not converted:
        print('- Error: ', err)

if __name__ == "__main__":
    main()
