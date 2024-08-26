# MaterialXglTF

This is the home page for the `materialxgltf` Python package which provides bi-directional data model conversion between MaterialX and glTF materials.

The package can be downloaded fro PyPi **[here](https://pypi.org/project/materialxgltf)**

### Documentation

* **Python Package**: Details about how to use this package can be found **[here](https://kwokcb.github.io/materialxgltf/README.html)**
* **API Documentation**): Python interface documentation can be found **[here](https://kwokcb.github.io/materialxgltf/docs/html/index.html)**
* **Jupyter Notebook**: An example is shown here **[here](https://kwokcb.github.io/materialxgltf/docs/examples.html)**. The notebook file can be found in the source repository.

#### Sample Integrations

A working version of a plug-in for QuiltiX can be found <a href="https://github.com/kwokcb/QuiltiX/tree/materialxgltf/sample_plugins/materialxgltf">here </a>

Below is a example of loading in the "Damaged Helmet" model from the <a href="https://github.com/KhronosGroup/glTF-Sample-Models/tree/main/2.0/DamagedHelmet">Khronos glTF sample models</a> repository and converting it to a MaterialX file using the QuiltiX plugin. The textures
are currently too dark due to lack of color management in the version of OpenUSD used.

| QuiltiX Plug-in| MaterialX View |
| :-- | :--: |
| <img src="https://github.com/kwokcb/QuiltiX/blob/materialxgltf/sample_plugins/materialxgltf/images/DamagedHelmet_Example.png?raw=true" width=100%> | <img src="https://github.com/kwokcb/QuiltiX/blob/materialxgltf/sample_plugins/materialxgltf/images/DamagedHelmet_Example_MXView.png?raw=true" width=100%> |

<sub>Note that the MaterialX versions must match between QuiltiX and the MaterialXglTF package. The current development version is 1.38.9. Either the appropriate branch of 
the GitHub repository needs to be built locally or the matching version of the package needs to be installed from the PyPi repository.</sub>

#### Material Examples

A gallery of example conversions can be found **[here](https://kwokcb.github.io/materialxgltf/docs/gallery.html)**

These examples can be loaded into different viewers to see the results. The following table shows the results of loading the Open Chess Set MaterialX file which has been converted to used the glTF PBR shading model, baked, and then converted to a glTF binary (GLB). ( Asset is authored by Moeen Sayed and Mujtaba Sayed, and was contributed to the MaterialX project by Side Effects. )

| Babylon Viewer | ThreeJS Editor |
| :-- | :--: |
| <img src="https://kwokcb.github.io/materialxgltf/docs/images/bablyon_chessset.png"> | <img src="https://kwokcb.github.io/materialxgltf/docs/images/ThreeJS_editor_chessset.png"> |






