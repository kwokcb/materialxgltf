echo "Convert from glTF to MTLX: GLTF Sample Assets Examples"
pushd .
cd docs/data/RTS_GLTF
python -m materialxgltf gltf2mtlx DamagedHelmet.gltf
python -m materialxgltf gltf2mtlx GlamVelvetSofa.gltf
python -m materialxgltf gltf2mtlx MaterialsVariantsShoe.gltf
python -m materialxgltf gltf2mtlx SciFiHelmet.gltf
python -m materialxgltf gltf2mtlx AnisotropyBarnLamp.gltf
# Add reference renderings
python ../../../utilities/test_render.py DamagedHelmet.gltf_converted.mtlx -m DamagedHelmet.gltf
python ../../../utilities/test_render.py GlamVelvetSofa.gltf_converted.mtlx -m GlamVelvetSofa.gltf
python ../../../utilities/test_render.py MaterialsVariantsShoe.gltf_converted.mtlx -m MaterialsVariantsShoe.gltf
python ../../../utilities/test_render.py SciFiHelmet.gltf_converted.mtlx -m SciFiHelmet.gltf
python ../../../utilities/test_render.py AnisotropyBarnLamp.gltf_converted.mtlx -m AnisotropyBarnLamp.gltf
popd