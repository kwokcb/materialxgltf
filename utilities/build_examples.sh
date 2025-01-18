# Build Examples
@echo "Convert PhysicallyBased MaterialX to glTF"
pushd .
cd docs/data/Physical
python -m materialxgltf mtlx2gltf --packageBinary 1 --gltfGeomFileName ../Geometry/test_sphere.gltf ./Aluminum.mtlx --translateShaders True --bakeTextures True
python -m materialxgltf mtlx2gltf --packageBinary 1 --gltfGeomFileName ../Geometry/test_sphere.gltf ./Sapphire.mtlx --translateShaders True --bakeTextures True
python -m materialxgltf mtlx2gltf --packageBinary 1 --gltfGeomFileName ../Geometry/test_sphere.gltf ./Tire.mtlx --translateShaders True --bakeTextures True
python -m materialxgltf mtlx2gltf --packageBinary 1 --gltfGeomFileName ../Geometry/test_sphere.gltf ./Whiteboard.mtlx --translateShaders True --bakeTextures True
# Add reference renderings
python ../../../utilities/test_render.py Aluminum.mtlx
python ../../../utilities/test_render.py Sapphire.mtlx
python ../../../utilities/test_render.py Tire.mtlx
python ../../../utilities/test_render.py Whiteboard.mtlx
popd

@echo "Convert Substance3D Example to glTF"
pushd .
cd docs/data/Substance3D
python -m materialxgltf mtlx2gltf --packageBinary 1 --gltfGeomFileName ../Geometry/test_cube.gltf parquet_clothes.mtlx
python -m materialxgltf mtlx2gltf --packageBinary 1 --gltfGeomFileName ../Geometry/test_sphere.gltf parquet_clothes.mtlx --gltfFileName parquet_clothes.mtlx_sphere.gltf
rm parquet_clothes.mtlx_sphere.gltf
# Add reference renderings
python ../../../utilities/test_render.py parquet_clothes.mtlx
popd

echo "Convert from MTLX to glTF: QuiltiX"
pushd .
cd docs/data/QuiltiX
python -m materialxgltf mtlx2gltf --packageBinary 1 --gltfGeomFileName ../Geometry/test_sphere.gltf Black_Upholstery.mtlx_baked.mtlx
python -m materialxgltf mtlx2gltf --packageBinary 1 --gltfGeomFileName ../Geometry/test_sphere.gltf ./Copper_Old.gltf_baked.mtlx
python -m materialxgltf mtlx2gltf --packageBinary 1 --gltfGeomFileName ../Geometry/test_sphere.gltf ./Motley_Patchwork_Rug.mtlx
# Add reference renderings
python ../../../utilities/test_render.py Black_Upholstery.mtlx_baked.mtlx 
python ../../../utilities/test_render.py Copper_Old.gltf_baked.mtlx
python ../../../utilities/test_render.py Motley_Patchwork_Rug.mtlx
popd

echo "Convert from glTF to MTLX: GLTF Examples"
pushd .
cd docs/data/RTS_GLTF
python -m materialxgltf gltf2mtlx DamagedHelmet.gltf
python -m materialxgltf gltf2mtlx GlamVelvetSofa.gltf
python -m materialxgltf gltf2mtlx MaterialsVariantsShoe.gltf
python -m materialxgltf gltf2mtlx SciFiHelmet.gltf
# Add reference renderings
python ../../../utilities/test_render.py DamagedHelmet.gltf_converted.mtlx -m DamagedHelmet.gltf
python ../../../utilities/test_render.py GlamVelvetSofa.gltf_converted.mtlx -m GlamVelvetSofa.gltf
python ../../../utilities/test_render.py MaterialsVariantsShoe.gltf_converted.mtlx -m MaterialsVariantsShoe.gltf
python ../../../utilities/test_render.py SciFiHelmet.gltf_converted.mtlx -m SciFiHelmet.gltf
popd
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
