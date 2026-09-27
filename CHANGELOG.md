# Changelog

All notable changes to svg-nv are recorded here. The format is
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
package follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the pre-1.0 rule that a breaking change bumps the MINOR number.

## 0.1.0 — 2026-09-27

The first implementation of the interface published as 0.0.1: the
style, the path arithmetic, the document tree, the writer and the
reader.

### Added

- `svgpath` computes tight boxes (curve turning points and arc extremes
  from SVG 1.1 appendix F.6), flattens within a tolerance, converts arcs
  to cubics, and transforms arcs exactly, reversing the sweep under a
  mirror.  `to_string_compact` writes each command in its shortest
  spelling, relative to where a reader's pen will be.
- `svgwrite` leaves out every attribute a reader would get anyway: an
  inherited one where it equals the parent's, any other where it equals
  SVG's initial value.  A colour's alpha is written as `fill-opacity` or
  `stroke-opacity` with at least three decimals.
- `svgread` reads XML 1.0 elements, attributes, the five predefined
  entities, character references, CDATA sections, comments and
  processing instructions, and skips a document type declaration.  It
  resolves inheritance, reads the `style` attribute's declarations after
  the attributes, resolves `currentColor`, `inherit`, percentages, `em`
  and `ex`, and folds the opacities into the paints.
- `tools/pathref.py`, an independent reader of path data, and the
  suites described in the README.

### Changed

- The dependencies are geometry-nv `^0.1.0` and color-nv `^0.1.1`, and
  the toolchain floor is 0.13.0.
- `svgwrite.to_string` and `node_to_string` refuse a value that is not
  finite with `SvgBadNumber`, whose offset is into the text that would
  have been written.
- `svgdoc.with_transform` replaces the node's transform; the interface
  did not say whether it replaced or composed.

## 0.0.2 — 2026-09-15

- README rewritten to the package README style guide (docs/writing-a-readme.md); no change to the interface.

## 0.0.1 — 2026-09-11

The **interface**: every signature and every effect row, and no bodies.
`stability = "draft"`, and the release is recorded `implemented = false`.

### Added

- `svgdoc` — `SvgDocument`, `SvgNode` and `SvgShape`. One node type
  carrying a shape, an absolute style, a transform and an id, rather
  than nine element variants with the style repeated in each.
  `SvgTransform` and `SvgViewBox` are the boxed bridges to geometry-nv's
  unboxed `GeomXform` and `GeomRectF`.
- `svgstyle` — the presentation attributes as one value, absolute rather
  than inherited, with `SvgPaint` carrying a `url(#id)` reference this
  package preserves and does not resolve. `GeomFillRule` is reused from
  geometry-nv rather than redeclared.
- `svgpath` — `SvgPathCmd` as a typed command list, all absolute, no
  shorthand, arcs kept exact. `SvgSubpath` is what `flatten` returns,
  because a list of lists of an unboxed element is refused (SPEC §14.6)
  and because a run's `closed` flag is information a bare point list
  loses.
- `svgwrite` — `to_string` for the whole document, and an `SvgWriter`
  whose chunk boundary is ONE ELEMENT, so a scatter plot with a million
  points never exists as a string. `number` and `escape` are public
  because a caller writing an attribute this package does not model has
  to spell numbers the same way — and because a naive float formatter
  emits `1e-7`, which is valid XML and invalid SVG.
- `svgread` — parse with inheritance resolved and paths normalised, and
  `parse_report` counting what was skipped. The attribute parsers stand
  alone, because lifting a `d` attribute out of a font or an icon set is
  the most common thing anyone does to an SVG.
- `svgfault` — eleven variants, every one carrying a byte offset.

### Decided

- **Shapes stay shapes.** usvg converts everything to paths because its
  consumer is a renderer; this package's first job is a round trip, so a
  `<rect>` comes back a rectangle. `svgdoc.to_path` is usvg's answer for
  a caller who wants it.
- **Unknown elements are skipped, not refused.** A reader that rejected
  a document with a `<style>` block would reject most SVG files in the
  world. `SvgReadReport` is how a caller learns what was lost.
- **Arcs are not expanded on the way in.** An arc is exactly
  representable and a cubic approximation is not; converting by default
  would silently change every rounded rectangle that passed through.

### Known

- **Text cannot be measured.** A font database needs a filesystem, which
  would put this package in `host`. `svgdoc.text_advance_estimate` is
  named for what it is, and it is the one number this package returns
  that is not exact.
- No `@tier(embedded)` claim, and none is intended: a document tree is
  allocation from end to end.
- `geometry-nv` is a PATH dependency while the two are developed
  together. It converts to `^0.0.1` before publish, and geometry-nv is
  published first.
