# Build Examples
pushd .
cd docs/data/Physical
python -m materialxgltf mtlx2gltf --packageBinary 1 --gltfGeomFileName ../Geometry/test_sphere.gltf ./Aluminum.mtlx --translateShaders True --bakeTextures True
python -m materialxgltf mtlx2gltf --packageBinary 1 --gltfGeomFileName ../Geometry/test_sphere.gltf ./Sapphire.mtlx --translateShaders True --bakeTextures True
python -m materialxgltf mtlx2gltf --packageBinary 1 --gltfGeomFileName ../Geometry/test_sphere.gltf ./Tire.mtlx --translateShaders True --bakeTextures True
python -m materialxgltf mtlx2gltf --packageBinary 1 --gltfGeomFileName ../Geometry/test_sphere.gltf ./Whiteboard.mtlx --translateShaders True --bakeTextures True
popd
pushd .
cd docs/data/Substance3D
python -m materialxgltf mtlx2gltf --packageBinary 1 --gltfGeomFileName ../Geometry/test_cube.gltf parquet_clothes.mtlx
python -m materialxgltf mtlx2gltf --packageBinary 1 --gltfGeomFileName ../Geometry/test_sphere.gltf parquet_clothes.mtlx --gltfFileName parquet_clothes.mtlx_sphere.gltf
rm parquet_clothes.mtlx_sphere.gltf
popd
pushd .
cd docs/data/QuiltiX
python -m materialxgltf mtlx2gltf --packageBinary 1 --gltfGeomFileName ../Geometry/test_sphere.gltf Black_Upholstery.mtlx_baked.mtlx
python -m materialxgltf mtlx2gltf --packageBinary 1 --gltfGeomFileName ../Geometry/test_sphere.gltf .//Copper_Old.gltf_baked.mtlx
python -m materialxgltf mtlx2gltf --packageBinary 1 --gltfGeomFileName ../Geometry/test_sphere.gltf .//Motley_Patchwork_Rug.mtlx
popd