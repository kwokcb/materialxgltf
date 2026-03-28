echo "Convert from MTLX to glTF: GPUOpen Example"
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
