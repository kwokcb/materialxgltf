# Install package
echo "Install package..."
python -m pip install --upgrade pip
pip install . --quiet

@echo "Build Package Examples"
pushd .
cd src/materialxgltf/data 
# Build boombox MTLX from glTF
materialxgltf gltf2Mtlx.py BoomBoxWithAxes.gltf --mtlxFileName BoomBoxWithAxes.mtlx
# Build boombox glb from MTLX
materialxgltf mtlx2gltf BoomBoxWithAxes.mtlx --gltfGeomFileName shaderball.gltf --primsPerMaterial True  --packageBinary True
# Build MTLX w/ glTF to glb
materialxgltf mtlx2gltf  --gltfGeomFileName shaderball.gltf --primsPerMaterial True --packageBinary True gltf_test_nondefault_pbr.mtlx
# BUild MTLX w/ std surface -> translation -> bake -> glb
materialxgltf mtlx2gltf  --gltfGeomFileName shaderball.gltf --primsPerMaterial True --packageBinary True standard_surface_marble_solid.mtlx --translateShaders True --bakeTextures True
popd

