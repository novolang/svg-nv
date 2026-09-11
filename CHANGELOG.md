# Changelog

All notable changes to svg-nv are recorded here. The format is
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
package follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the pre-1.0 rule that a breaking change bumps the MINOR number.

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
