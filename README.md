# svg-nv

**Status: NOT IMPLEMENTED — interface only.**

Every public function below is published with its signature and its
effect row, and every body is `todo()`. Installing this package works;
calling it panics with `not implemented`.

## What this is

SVG as a value. A document is a tree of shapes, each carrying its own
geometry, its own absolute style and its own transform; a path is a
typed command list rather than a string; the writer hands back text one
element at a time and never holds the document; and the reader takes the
subset a program round-trips.

It is [`plot-nv`](https://github.com/novolang/plot-nv)'s second output —
a chart in a notebook is an SVG — and it is the answer for anything that
has to produce a vector drawing a browser or a printer will take.

```
novo pkg add svg-nv
novo pkg build
novo test
```

## The one example that will work

```novo
use svgdoc
use svgstyle
use svgwrite
use geomrect
use srgb

// A bar chart's bars, as a group of rectangles.  Every one of them
// carries the style it renders with — nothing here inherits.
fn bars(values: [Float], bar_w: Float, scale: Float) -> SvgNode
    let blue = svgstyle.filled(srgb.opaque(srgb.rgb8(60, 110, 200)))
    var kids: [SvgNode] = []
    var i = 0
    for v in values
        let r = geomrect.of_xywh(int.to_float(i) * bar_w, 0.0 - v * scale,
                                 bar_w - 2.0, v * scale)
        kids = list.push(kids, svgdoc.rect(r, blue))
        i = i + 1
    svgdoc.group(kids)

fn chart(values: [Float]) -> Result<Str, SvgFault>
    let doc = svgdoc.document(640.0, 200.0, [bars(values, 32.0, 4.0)])
    svgwrite.to_string(doc, svgwrite.minimal())
```

## The layer, and why

`core`. A document is a value; building one touches nothing. The writer
produces text and the caller places it; the reader takes the text the
caller already holds. There is no file anywhere in this package, and for
a text format that costs almost nothing — a caller reading an SVG has
the string a line earlier.

No `@tier(embedded)` claim, and none is intended: a document tree is
allocation from end to end, and a microcontroller that wanted to emit
SVG would emit it a chunk at a time out of its own loop rather than
building a tree first.

## The load-bearing interface

```novo ignore
pub struct SvgNode
    shape: SvgShape          // the geometry, and only the geometry
    style: SvgStyle          // ABSOLUTE — nothing in the tree inherits
    transform: SvgTransform  // this element's own
    id: Str
    children: [SvgNode]      // non-empty only on a group

pub enum SvgPathCmd         // all absolute, no shorthand, arcs kept
    SvgMoveTo(x: Float, y: Float)
    SvgCubicTo(x1: Float, y1: Float, x2: Float, y2: Float, x: Float, y: Float)
    SvgArcTo(rx: Float, ry: Float, rotation: Float, large_arc: Bool, sweep: Bool, …)
    …

pub fn next_chunk(w: SvgWriter) -> (SvgWriter, Str)   // one element, never the document
```

Three decisions, and every signature follows from them.

**One node type, not nine.** Every SVG element that draws carries the
same three things — an id, a transform and the presentation attributes —
and differs only in the geometry. A variant per element would repeat the
style nine times, give the writer nine branches doing identical
attribute work, and let the reader forget `transform` in one of nine
places.

**A style is absolute.** SVG inherits presentation attributes down the
tree; a reader that preserved that hands the caller a document in which
no element knows how it looks without a walk to the root. The reader
resolves inheritance on the way in — usvg's decision, and the reason
usvg exists — so every node carries the style it actually renders with.

**A path is a command list, and the `d` attribute is a language.**
`"M 0 0 L 10 0 l 0 10 z"` is a program: two coordinate modes, five
shorthands that borrow a control point from the command before them, and
a number syntax in which `1.5.5` is two numbers. Storing that string
hands every consumer the job of parsing it, and every consumer does it
slightly differently. So the reader normalises — relative to absolute,
`H`/`V`/`S`/`T` expanded, current point gone — and a program never meets
a shorthand. `svgwrite`'s `compact_paths` takes the bytes back on the
way out; the tree is never shorthand.

The arc is the exception that proves the third rule: most pipelines
expand SVG's elliptical arc into cubics on the way in, and this one does
not, because an arc is exactly representable and a cubic approximation
is not. Converting by default would silently change the geometry of
every rounded rectangle that passed through. `svgpath.to_cubics` is
there for a renderer with no arc primitive.

### The bridge types, and why they exist

`SvgTransform` and `SvgViewBox` hold the same numbers as geometry-nv's
`GeomXform` and `GeomRectF`, with `to_xform` / `of_xform` / `to_rect` /
`of_rect` between them. That looks like duplication and is not: those
two are `@value` structs, a **boxed aggregate cannot have an unboxed
field** (SPEC §14.5), and a document tree is boxed by construction
because it nests. So the tree carries the numbers and converts at the
edge, where the arithmetic starts. The conversion is six field reads;
what it buys is that geometry-nv owns the transform algebra and this
package never reimplements it.

The same rule is why `SvgShape`'s variants carry bare `Float`s rather
than points — a `@value` struct cannot be an enum payload either — while
`SvgPolylineShape` carries a `[GeomPointF]`, because a LIST of unboxed
elements is allowed and is in fact the efficient form: one flat buffer,
no per-point cell.

Two types are shared rather than redeclared: `GeomFillRule` is
geometry-nv's, so there is one fill rule in the registry, and every
colour is color-nv's `Srgba8`, so a plot rendered to SVG and the same
plot rendered to a PNG cannot disagree about a shade.

## What it ports

[usvg](https://github.com/RazrFalcon/resvg) for the reader's contract
and [svgwrite](https://github.com/mozman/svgwrite) for the writer's
shape. Both are permissive, and usvg's own test corpus is the oracle the
implementation lane should measure against.

One departure from usvg, and it is the point of the difference: **usvg
converts every shape to a path**, because its consumer is a renderer
that wants one primitive. This package keeps a `<rect>` a rectangle,
because its first job is a ROUND TRIP — a document read and written back
should be the document that went in. `svgdoc.to_path` is usvg's answer,
for a caller that wants it.

## The subset, stated plainly

Read and written: `svg`, `g`, `rect`, `circle`, `ellipse`, `line`,
`polyline`, `polygon`, `path`, `text`, with `fill`, `stroke`,
`stroke-width`, `stroke-linecap`, `stroke-linejoin`, `stroke-miterlimit`,
`stroke-dasharray`, `stroke-dashoffset`, `opacity`, `fill-rule`,
`font-family`, `font-size`, `font-weight`, `font-style`, `text-anchor`,
`transform`, `id`, `viewBox`, `width` and `height`.

Not modelled: gradients, patterns, masks, clip paths, filters, markers,
`use`, `image`, `symbol`, `switch`, CSS and animation.

**They are skipped, not refused.** A reader that rejected every document
with a `<style>` block would reject most SVG files in the world.
`svgread.parse_report` counts what it skipped and names the first few, so
a caller can tell "read it all" from "read the half of it that was
shapes". A `url(#id)` paint survives as `SvgPaintRef` even though the
gradient it names was skipped — which means a document can come back out
naming a paint server that is no longer in it, and
`SvgReadReport.has_dangling_paint` is how a caller knows.

## Two things this package cannot do, and says so

**It cannot measure text.** Resolving a font family to glyph advances
needs a font file, which needs a filesystem, which is `host`. So
`svgdoc.text_advance_estimate` is named an estimate: the string length
times the font size times a constant near the average advance of a
proportional Latin face — right to within a fifth for ordinary text and
wrong for anything else. It exists because `bounds` has to answer
something for a text node, and a silent zero would make a plot's
auto-sized viewBox clip its own axis labels. A caller who needs the real
width measures it with a font package and unions it in.

**It cannot render.** There is no rasteriser here. `svgpath.flatten`
turns curves into segments and `svgdoc.to_path` turns a tree into one
path, which is what a rasteriser needs — and `raster-nv` is the row on
the plan that consumes them.

## Related

- [`geometry-nv`](https://github.com/novolang/geometry-nv) — the points
  and transforms this package is built on
- [`color-nv`](https://github.com/novolang/color-nv) — every colour in a
  document
- [`plot-nv`](https://github.com/novolang/plot-nv) — the first consumer
- [Publishing a package to Orbit](https://novo-lang.org/publishing) —
  the layer rules this package is held to
