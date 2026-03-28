pushd .
cd docs/data/RTS
echo "Convert from MTLX to glTF: MaterialX Standard Surface Examples..."
for file in $(find . -type f -name "*.mtlx"); do
    filename=$(basename "$file")
    if [[ "$filename" == standard_* && "$filename" != *baked* ]]; then    
        gltf_filename="${filename}.gltf" 
        baked_filename="${file}_baked.mtlx"
        echo "Convert: $filename --> $gltf_filename"
        python -m materialxgltf mtlx2gltf --bakeResolution 512 --primsPerMaterial 1 --packageBinary 1 --gltfGeomFileName ../Geometry/shaderball.gltf $file --translateShaders True --bakeTextures True --gltfFileName ./$gltf_filename
        rm $baked_filename
        rm ./$gltf_filename
    fi
done
popd