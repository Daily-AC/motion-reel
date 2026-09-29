# Codex case study

An independently made15-second promotional motion reel, developed through the feedback documented in the skill's case study. This is a concrete outcome of the workflow, not a guarantee for every brief or model.

[Watch the accepted film](https://github.com/Daily-AC/motion-reel/releases/download/v0.1.0/codex-showcase.mp4)

```sh
python3 examples/codex/create.py /path/to/codex-example
cd /path/to/codex-example
node render.mjs render --out out/codex.mp4 --samples 16
python3 verify.py out/codex.mp4
```

`scenes.js` and `contours.js` preserve the accepted scene design and icon geometry. The public renderer supplies the compositor and sound arrangement. The original case uses macOS system typography for Chinese; the generic starter instead bundles redistributable Latin fonts. Another OS requires a licensed CJK font and fresh layout checks; it is not claimed to be pixel-identical.

The Codex/OpenAI mark is an example of brand fidelity, not an endorsement or a logo for unrelated projects. See `lobe-icons-LICENSE` and the repository's `THIRD_PARTY.md`.
