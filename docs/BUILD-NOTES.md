# Environment build notes

Raven Ridge is a newly authored portfolio environment, created for a Roblox military-builder opportunity. It is a personal portfolio piece, not a past client commission. No purchased or marketplace models are included.

## Design

The layout uses a fortified approach as its first reveal, a central cross-compound lane for navigation, and four observation towers as landmarks. The command bunker, helipad, logistics yard, and maintenance pavilion are deliberately distinct zones. Concrete buttresses, corrugated siding, window mullions, pipework, warning paint, and field supplies give close camera angles something to show.

The landscape is an original low-poly alpine setting. Native wedge pairs tile a continuous ground surface. Corner wedges form spruce crowns and granite peaks; no externally uploaded meshes are required. Buildings, vehicles, and props are built from editable anchored parts rather than opaque combined meshes.

## Source of truth

`tools/build_scene.py` generates the native `.rbxlx` place and `viewer/scene.json` together. Position, orientation, size, color, groups, lights, labels, and mechanism tags all originate in this generator. `src/` contains the embedded native Luau scripts. A seeded generator keeps the scenery reproducible.

The exporter accounts for native primitive conventions: cylinders use the X axis, corner wedges receive a local 180-degree basis correction, and nonuniform ellipsoids use native `SpecialMesh` Sphere shapes. The geometry verifier checks corner-apex agreement and the presence of ellipsoid meshes, in addition to part positions and sizes.

The web preview renders the manifest with Three.js, instancing repeated geometry for fewer draw calls. It also supplies orbit controls, fixed camera views, day/dusk lighting, and previews of the two architectural mechanisms. The browser uses eight prioritized point lights and caches shadows until a mechanism changes; the Studio export contains the full native lighting rig.

## Native interactions

- The checkpoint control raises and lowers the barrier through a server-side proximity prompt.
- The command door slides to open its explorable operations room.
- F6 cycles portfolio cameras; F7 returns to character exploration; L changes local lighting.
- One spawn sits on the approach road. No combat system or flyable/drivable vehicle system is claimed.

Prompt handlers run on the server, check character distance, and guard against overlapping tweens. The web viewer previews the architectural changes independently; it does not execute native Luau.

## Validation and limits

Geometry count, coordinates, sizes, anchoring, unique references, spawn, prompts, and source inclusion are checked by `tools/verify_scene.py`. `tools/roundtrip.lua` additionally uses rbxmk to decode the native XML, encode a binary `.rbxl`, decode that file again, and compare instance counts.

The video is a real browser recording of the same authored geometry, with deterministic camera motion and titles. Capture uses a vertex-lit diffuse preview shader and a smaller internal framebuffer for the software GPU; titles and encoded output are 1920×1080. It is explicitly labeled as a browser render. It is not footage recorded inside Roblox Studio or Roblox gameplay.

Roblox Studio is unavailable in the Linux build environment. Native rendering, prompt behavior, player movement, collision edge cases, and multi-client behavior still require a Studio playtest on Windows or macOS. The file-format round trip is useful export validation, not a substitute for that runtime check.

## Performance choices

Parts are anchored, and nonessential touch events are disabled. The repeated native modules stay editable and organized into models. The viewer groups repeated geometry into instanced batches. A production Roblox game should profile the place on its target devices and consider terrain conversion, distance-based prop reduction, and selective mesh consolidation where needed.

## References

- [Roblox primitive part types](https://create.roblox.com/docs/reference/engine/enums/PartType)
- [Roblox atmosphere](https://create.roblox.com/docs/reference/engine/classes/Atmosphere)
- [Roblox proximity prompt API](https://create.roblox.com/docs/reference/engine/classes/ProximityPrompt)
- [Roblox client/server security guidance](https://github.com/Roblox/creator-docs/blob/main/content/en-us/scripting/security/client-server-boundary.md)
- [rbxmk native file tools](https://github.com/Anaminus/rbxmk)
- [Native wedge and corner-wedge vertex coordinates](https://github.com/FrostDracony/Roblox/blob/master/Tutorials/GetCornersOfAllBaseParts/GetCornersOfWedgeAndCornerWedge.md)
- [Native sphere mesh scaling](https://create.roblox.com/docs/reference/engine/classes/SpecialMesh/MeshType)

Barlow Condensed is distributed under the SIL Open Font License, included in `viewer/fonts/OFL.txt`. Three.js and Vite are third-party dependencies with their own licenses. The scene geometry and project code are newly authored portfolio work.
