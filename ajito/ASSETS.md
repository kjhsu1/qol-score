# Artwork and libraries

- `web/assets/ajito.png`: created with the built-in image-generation tool, saved into this workspace from the generated output; no CLI/API key was used. The current hero is the approved, less dramatic hyperrealistic Boyacki portrait at Ocean Beach, San Francisco (version 2.0.3). The cinematic Hokusai-wave variant was previewed and not selected. It is background artwork, not a flattened UI.
- `web/mascot.js`: original procedural 3D Boyacki model and animation in code, independent of the background illustration. Version 2.0.1 replaces the small engineer cap with tall swept twin points, gold ear covers and a red B crest; face geometry is unchanged.
- `icon.svg`, `Ajito.icns`: original vector skull button icon rendered at standard macOS icon sizes.
- `web/vendor/three.module.min.js`: Three.js **0.160.1**, MIT; license in `THREE-LICENSE.txt`. This version supports WebGL 1. The application does not fetch it from a CDN.
- Visual references inspected: https://teenage.engineering/products/ep-133 and https://poolsuite.net/. These informed material and navigation choices; their assets/code are not included.

## Image prompt (built-in generation, selected Ocean Beach version)

Hyperrealistic live-action Boyacki from Yatterman at Ocean Beach, San Francisco, facing straight into the camera with a closed-mouth, deadpan, confident mogging expression. Slim middle-aged man, long projecting nose, thin angular moustache, green eye mask, green costume and helmet with widely splayed twin horns, gold ear covers and red B emblem. Real skin pores, textured weathered leather and fabric. Frontal level face, squared shoulders, chest-up portrait in right half; left 45% spacious for app headline. Whole helmet and both horn tips in frame. Broad pale sand, gray-blue Pacific surf and foam, coastal dunes and cool marine-layer sky; soft natural late-afternoon coastal light. Wide 2.5:1 banner, no typography, no extra characters, no watermark. Generated with the built-in image tool; no CLI/API key. Source: exec-b8274009-f7c5-4f96-acf7-3c905d62611f.png.

- `web/assets/ajito-banner-bold.ttf`: Noto Sans JP, weight 700 (Bold), instantiated, subset to the Japanese banner characters and renamed Ajito Banner. Bundled locally for consistent offline rendering; SIL Open Font License in `NOTO-OFL.txt`. Source: https://github.com/google/fonts/tree/main/ofl/notosansjp.

Approved banner styling: variation A, dark Bold-weight Japanese copy, 12-degree forward slant, pale coastal overlay and punctuation: 「限界を超えろ、運命を変えろ。」. Typography remains live HTML/CSS rather than text flattened into the artwork.
