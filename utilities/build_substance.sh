@echo "Convert from MTLX to glTF : Substance3D Example"
pushd .
cd docs/data/Substance3D
python -m materialxgltf mtlx2gltf --packageBinary 1 --gltfGeomFileName ../Geometry/test_cube.gltf parquet_clothes.mtlx
python -m materialxgltf mtlx2gltf --packageBinary 1 --gltfGeomFileName ../Geometry/test_sphere.gltf parquet_clothes.mtlx --gltfFileName parquet_clothes.mtlx_sphere.gltf
rm parquet_clothes.mtlx_sphere.gltf
# Add reference renderings
python ../../../utilities/test_render.py parquet_clothes.mtlx
popd
