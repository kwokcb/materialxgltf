echo "Convert from glTF to MTLX: GLTF Sample Assets Examples"
pushd .
cd docs/data/RTS_GLTF
python -m materialxgltf gltf2mtlx DamagedHelmet.gltf
python -m materialxgltf gltf2mtlx GlamVelvetSofa.gltf
python -m materialxgltf gltf2mtlx MaterialsVariantsShoe.gltf
python -m materialxgltf gltf2mtlx SciFiHelmet.gltf
python -m materialxgltf gltf2mtlx AnisotropyBarnLamp.gltf
python -m materialxgltf gltf2mtlx ChronographWatch.gltf
python -m materialxgltf gltf2mtlx DiffuseTransmissionTeacup.gltf
python -m materialxgltf gltf2mtlx FlightHelmet.gltf
python -m materialxgltf gltf2mtlx GlassHurricaneCandleHolder.gltf
python -m materialxgltf gltf2mtlx USDShaderBallForGltf.gltf
# Add reference renderings
python ../../../utilities/test_render.py DamagedHelmet.gltf_converted.mtlx -m DamagedHelmet.gltf
python ../../../utilities/test_render.py GlamVelvetSofa.gltf_converted.mtlx -m GlamVelvetSofa.gltf
python ../../../utilities/test_render.py MaterialsVariantsShoe.gltf_converted.mtlx -m MaterialsVariantsShoe.gltf
python ../../../utilities/test_render.py SciFiHelmet.gltf_converted.mtlx -m SciFiHelmet.gltf
python ../../../utilities/test_render.py AnisotropyBarnLamp.gltf_converted.mtlx -m AnisotropyBarnLamp.gltf
python ../../../utilities/test_render.py ChronographWatch.gltf_converted.mtlx -m ChronographWatch.gltf
python ../../../utilities/test_render.py DiffuseTransmissionTeacup.gltf_converted.mtlx -m DiffuseTransmissionTeacup.gltf
python ../../../utilities/test_render.py FlightHelmet.gltf_converted.mtlx -m FlightHelmet.gltf
python ../../../utilities/test_render.py GlassHurricaneCandleHolder.gltf_converted.mtlx -m GlassHurricaneCandleHolder.gltf
python ../../../utilities/test_render.py USDShaderBallForGltf.gltf_converted.mtlx -m USDShaderBallForGltf.gltf
popd
cd docs/data/RTS
python -m materialxgltf gltf2mtlx ./scale_factors.gltf
python -m materialxgltf mtlx2gltf ./scale_factors.gltf_converted.mtlx   
