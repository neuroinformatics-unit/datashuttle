\# Screenshots



Screenshots were taken in Windows on
on a large LG screen monitor model: 35WN75C
resolution 3440x1440 / 85 Hz.

Windows terminal was used, default size set to 150 x 45.

Then:

1. ShareX 16.0.1 to take screenshot.
2. Copy these to photoshop. Set DPI to desired. Save as PNG.

The raw screenshots .PSD files available on the NeuroInformatics
Unit dropbox. Please request if required.



\# GIFS



The videos used for the GIFS are at: https://www.dropbox.com/home/NIU/resources/datashuttle/website-gifs. Please contact for access.



Videos were created on Windows with Clipchamp.



The GIFS are created with the following commands:



\## DARK

.\\ffmpeg.exe -i datashuttle-gif-dark.mp4 -vf "fps=9,scale=600:-1:flags=lanczos,unsharp=3:3:0.5,palettegen=stats\_mode=diff:max\_colors=256" palette-dark.png



.\\ffmpeg.exe -i datashuttle-gif-dark.mp4 -i palette-dark.png -filter\_complex "fps=9,scale=600:-1:flags=lanczos,unsharp=3:3:0.5\[x];\[x]\[1:v]paletteuse=dither=bayer:bayer\_scale=2:diff\_mode=rectangle" datashuttle-demo-dark.gif



\## LIGHT

.\\ffmpeg.exe -i datashuttle-gif-light.mp4 -vf "fps=9,scale=600:-1:flags=lanczos,unsharp=3:3:0.5,palettegen=stats\_mode=diff:max\_colors=256" palette-light.png



.\\ffmpeg.exe -i datashuttle-gif-light.mp4 -i palette-light.png -filter\_complex "fps=9,scale=600:-1:flags=lanczos,unsharp=3:3:0.5\[x];\[x]\[1:v]paletteuse=dither=bayer:bayer\_scale=2:diff\_mode=rectangle" datashuttle-demo-light.gif
