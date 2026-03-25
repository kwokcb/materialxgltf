#!/usr/bin/env python
'''
Utility and command line interface to convert from a glTF file to a MaterialX file 
'''
import os
import argparse

from core import *

def gltf2Mtlx(gltf_file, mtlx_file, options=GLTF2MtlxOptions(), zip=False):
    '''
    @brief Utility to convert a glTF file to MaterialX file

    @param gltfFileName Path to glTF file to convert
    @param mtlxFileName Path to MaterialX file to write
    @param options Options for conversion
    @param zip Write document to zip with image references vs just the document.    
    '''
    status = True
    err = ''

    gltf2MtlxReader = GLTF2MtlxReader()
    gltf2MtlxReader.setOptions(options)
    doc = gltf2MtlxReader.convert(gltf_file)
    if not doc:
        status = False
        err = 'Error converting glTF file to MaterialX file'
    else:
        status, err = doc.validate()
        if not status:
            print('Validation error(s): ', err)

        if options['zip']:
            image_references = gltf2MtlxReader.getImageReferences()
            zip_path = mtlx_file.replace('.mtlx', '.zip')
            Util.writeMaterialXZip(doc, mtlx_file, zip_path, image_references)
            print('Saved gltf file: %s to MaterialX zip file: %s. Status: %s.' % (gltf_file, zip_path, status))
        else:
            Util.writeMaterialXDoc(doc, mtlx_file)
            print('Saved gltf file: %s to MaterialX file: %s. Status: %s.' % (gltf_file, mtlx_file, status))

    return status, err

def main():
    '''
    @brief Command line interface to convert from a glTF file to a MaterialX file
    '''
    parser = argparse.ArgumentParser(description='Utility to convert a glTF file to MaterialX file')
    parser.add_argument(dest='gltfFileName', help='Path containing glTF file to convert.')
    parser.add_argument('-fn', '--mtlxFileName', dest='mtlxFileName', default='', help='Name of MaterialX output file. If not specified the glTF name with "_converted.mtlx" suffix will be used')
    parser.add_argument('-ca', '--createAssignments', dest='createAssignments', type=mx.stringToBoolean, default=True, help='Create material assignments. Default is True')
    parser.add_argument('-ai','--addAllInputs', dest='addAllInputs', type=mx.stringToBoolean, default=False, help='Add all definition inputs to MaterialX shader nodes. Default is False')
    parser.add_argument('-ax', '--assignXform', dest='assignXform', type=mx.stringToBoolean, default=False, help='Assign to transforms vs shapes. Default is False'   )
    parser.add_argument('-z', '--zip', dest='zip', type=mx.stringToBoolean, default=False, help='Write a zip file containing the MaterialX file and all referenced texture files. Default is False')

    opts = parser.parse_args()

    # Check input glTF file
    gltfFileName = opts.gltfFileName
    if not os.path.exists(gltfFileName):
        print('Cannot find input file: ', gltfFileName)
        exit(-1)    

    # Set up MTLX file name
    mtlx_path = gltfFileName + '_converted.mtlx'
    if opts.mtlxFileName:
        mtlx_path = opts.mtlxFileName 

    # Perform conversion
    options = GLTF2MtlxOptions()
    options['createAssignments'] = opts.createAssignments    
    options['addAllInputs'] = opts.addAllInputs
    options['assignXform'] = opts.assignXform
    options['zip'] = opts.zip
    converted, err = gltf2Mtlx(gltfFileName, mtlx_path, options)

if __name__ == "__main__":
    main()
