# <img src="./svg-to-img.svg" width=20 height=20> Pyscape

Pyscape is a python library that uses inkscape/skia and pillow to make working with SVG files easier. Pillow is quite a popular and easy to use python image library, but there unfortunately doesn't exist an easy way to utilize it with SVG's. Pyscape is an (albeit limited) attempt to make that process a little easier. Pyscape uses [inkscape](https://inkscape.org/) or [skia](https://skia.org/) to render an svg, and returning a PIL Image instance. There are no temporary files, instead rendering the image to stdout and feeding that to PIL. 

## Usage

Load svg file as SVG instance
```py
from pyscape import SVG

svg = SVG('path/to/svg/file.svg')
```

Create PIL.Image instance from the svg
```py
from pyscape import SVG

svg = SVG('path/to/svg/file.svg')
img = svg.im()
```

You can specify the dpi of the rendered image or the size in pixels.

```py
from pyscape import SVG

svg = SVG('path/to/svg/file.svg')
img = svg.im(dpi=32) # img has DPI of 32
img = svg.im(size=100) # img resolution of width 100px and proportional height
img = svg.im(size=(100,150)) # img resolution of (100px, 150px)
```

You can also create multiple images of varying resolutions at once.
```py
from pyscape import SVG

svg = SVG('path/to/svg/file.svg')
images = svg.im(dpi=[32, 48, 96], size=[(1200, 1400), 120, (80, 50)]) 
```

By default, when create multiple images, the highest specified resolution is rendered, with all others downscaled from it. The downscaling filter used
can be specified, with the filters being defined by [pillow](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Resampling). If the filter
is set to `rerender` then each image is rendered individual at the specified resolution (this will be slower).

```py
from pyscape import SVG

svg = SVG('path/to/svg/file.svg')
images = svg.im(dpi=[32, 48, 96], size=[(1200, 1400), 120, (80, 50)], filter='nearest') # faster
images = svg.im(dpi=[32, 48, 96], size=[(1200, 1400), 120, (80, 50)], filter='rerender') # slower 
```

You can also directly export the svg's to any supported [pillow image format](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html).
```py
from pyscape import SVG

svg = SVG('path/to/svg/file.svg')
# creates file ./path/to/svg/file.png
img = svg.export(format="png")
```

All arguments that are used by `SVG::im` can also be called with `SVG::export`. You can specify which formats using the `format` argument, and the output file name/location using the `stem` argument. Specifying multiple DPI's and sizes will create multiple exports named based off their resolution.

```py
from pyscape import SVG

svg = SVG('path/to/svg/file.svg')

# creates two files: 
#   ./out/file.png 
#   ./out/file.jpeg
img = svg.export(stem='out/file', format=['png','jpeg'], dpi=48)

# creates four files: 
#   ./out/file2_100_80.png
#   ./out/file2_200_150.png
#   ./out/file2_100_80.jpeg
#   ./out/file2_200_150.jpg
img = svg.export(stem='out/file2', format=['png','jpeg'], size=[(100, 80), (200, 150)])
```

Finally, if you do not need to create an SVG instance, there are class method variations of both `SVG::im` and `SVG::export` which take the filepath directly, loading an Image instance or exporting.
```py
from pyscape import SVG

img = SVG.IM('path/to/svg/file.svg')
SVG.EXPORT('path/to/svg/file.svg')
```

The default renderer is `skia` but skia has limited svg support and some svg objects may not render properly. If your svg has imports of other svg's, I would recommend the inkscape renderer.

## Install

I personally don't feel this is fleshed out enough to publish, so for now, the easiest way to use this is to clone the repo and run `python -m pip install .`. You can then import and use pyscape.