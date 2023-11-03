## Gallery

<script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.js">    
</script>

### MaterialX to glTF

The following are some examples of conversions from MaterialX to glTF. The input files are from the `resources` folder of the ASWF MaterialX Repository found [here](https://github.com/AcademySoftwareFoundation/MaterialX/tree/main/resources/Materials/Examples). the glTF and Autodesk
Standard Surface example scenes are converted. For the latter shader translation and texture baking are performed. All results are packaged into
individual glTF binary files (glb). 

These files can be previewed in any integration which accepts `glb` files as input such as the [ThreeJS editor](https://threejs.org/editor/), and the [Babylon viewer](https://sandbox.babylonjs.com/). For this page the [model-viewer](https://modelviewer.dev/) package is used.


### glTF to MaterialX

<model-viewer style='background-color:rgba(0, 0, 0, 1.0); width: 24em; height: 24em' id='viewer1' ar interaction-prompt='none' camera-controls touch-action='pan-y' src='https://kwokcb.github.io//docs/data/BoomBoxWithAxes_primMaterials.glb' shadow-intensity='0.3' alt='BoomBox With Axes Per Prim Material' poster='https://kwokcb.github.io/docs/data/BoomBoxWithAxes_primMaterials.png'></model-viewer>
