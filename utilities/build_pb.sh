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
