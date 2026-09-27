# svg-nv

SVG is a vector image format written as XML, specified in
[SVG 1.1](https://www.w3.org/TR/SVG11/). This package holds an SVG document as
a value in novo-lang: a tree of shapes, each carrying its own geometry, its own
style and its own transform. Its points and transforms are
[geometry-nv](https://novo-lang.org/packages/geometry-nv)'s and its colours are
[color-nv](https://novo-lang.org/packages/color-nv)'s. Two other packages on
the registry are built on it: [font-nv](https://novo-lang.org/packages/font-nv)
and [raster-nv](https://novo-lang.org/packages/raster-nv).

## What it is

An SVG document is a **viewport**, which is how large the image is, and a
**view box**, which is the coordinate system its contents are drawn in.
Everything inside is drawn in **user units**, and the view box is what maps
them onto the viewport.

Inside the document is a tree of elements. Each element that draws something
carries the same three things beside its geometry: an **id**, a **transform**
of its own, and the **presentation attributes**, which are the fill, the
stroke, the opacity, the font and the rest of how it looks. Here that is one
node type carrying one shape, one style and one transform, rather than a
different type per element.

SVG's presentation attributes are **inherited**: an element with no `fill` of
its own takes its parent's. A style in this package is **absolute** instead.
The reader resolves inheritance on the way in, so every node carries the style
it actually renders with and nothing needs a walk to the root to be understood.

A `<path>` element's geometry is its `d` attribute, and a `d` attribute is a
small language. `"M 0 0 L 10 0 l 0 10 z"` has two coordinate modes, five
shorthand commands that borrow a control point from the command before them,
and a number syntax in which `1.5.5` is two numbers. Here a path is a typed
list of commands instead. Every command is **absolute** and no command is a
shorthand, so a program never has to track a current point to understand one.

| Element | Modelled as |
| --- | --- |
| `svg` | `SvgDocument` |
| `g` | `SvgGroupShape` |
| `rect` | `SvgRectShape`, with corner radii |
| `circle` | `SvgCircleShape` |
| `ellipse` | `SvgEllipseShape` |
| `line` | `SvgLineShape` |
| `polyline` | `SvgPolylineShape` |
| `polygon` | `SvgPolygonShape` |
| `path` | `SvgPathShape` |
| `text` | `SvgTextShape`, one run at one anchor point |

| Path command | What it carries |
| --- | --- |
| `SvgMoveTo` | a point |
| `SvgLineTo` | a point |
| `SvgQuadTo` | one control point and an end point |
| `SvgCubicTo` | two control points and an end point |
| `SvgArcTo` | two radii, a rotation in radians, two flags, and an end point |
| `SvgClosePath` | nothing |

| Presentation attribute | Read and written |
| --- | --- |
| `fill`, `stroke`, `fill-rule`, `opacity` | yes |
| `stroke-width`, `stroke-linecap`, `stroke-linejoin`, `stroke-miterlimit` | yes |
| `stroke-dasharray`, `stroke-dashoffset` | yes |
| `font-family`, `font-size`, `font-weight`, `font-style`, `text-anchor` | yes |
| `transform`, `id`, `viewBox`, `width`, `height` | yes |

## Install

```
novo pkg add svg-nv
```

## Example

```novo
use geompoint
use geomrect
use srgb
use svgdoc
use svgfault
use svgstyle
use svgwrite

fn main() [io]
    // A style is absolute: every node carries the one it renders with.
    let blue = svgstyle.filled(srgb.opaque(srgb.rgb8(60, 110, 200)))

    // One bar of a chart, and a label beside it.
    let bar = svgdoc.rect(geomrect.of_xywh(0.0, 100.0, 30.0, 100.0), blue)
    let label = svgdoc.text("42", geompoint.ptf(0.0, 96.0), svgstyle.plain())

    // A 640 by 200 document with those two elements in a group.
    let doc = svgdoc.document(640.0, 200.0, [svgdoc.group([bar, label])])

    // The whole document as one string. `svgwrite.writer` is the form
    // that hands back one element at a time and never holds the text.
    match svgwrite.to_string(doc, svgwrite.minimal())
        Ok(text) => println(text)
        Err(f)   => println("${svgfault.offset_of(f)}")
```

## What the package contains

| Module | Contents |
| --- | --- |
| `svgdoc` | The document and the node: the ten shapes, the constructors for each, the view box, the bridge to geometry-nv's transform type, and the walks over a tree that answer its bounds, its nodes and its node with a given id. |
| `svgstyle` | The presentation attributes as one value: the paints, the caps and joins, the text anchor, the font, the lengths with their units, and the functions that write each one the way SVG spells it. |
| `svgpath` | A path as a typed command list: the constructors, the shapes turned into paths, the bounds, the flattening to straight segments, the arc and quadratic conversions, and the two `d` attribute spellings. |
| `svgwrite` | A document into text: one call for the whole thing, or a writer that hands back one element at a time. The number formatter and the XML escaper are public, for a caller writing an attribute this package does not model. |
| `svgread` | Text into a document, with inheritance resolved and paths normalised. The attribute parsers stand alone, so a `d` attribute can be lifted out of a font or an icon set on its own. |
| `svgfault` | Eleven ways reading an SVG can go wrong, each carrying a byte offset into the caller's own string. |

## How to choose an entry point

**`svgwrite.to_string` writes a whole document.** It is what a caller
producing a chart of a few kilobytes wants.

**`svgwrite.writer` and `next_chunk` write a document the caller never holds
as text.** Each chunk is one element: an opening tag through a closing tag for
a leaf, and an opening tag alone for a group. A chunk that finishes a group
also carries the group's closing tag. A scatter plot with a million points
never exists as a string.

**`svgread.parse` reads a document.** `parse_report` reads the same document
and counts what it skipped, which is how a caller tells "read it all" from
"read the half of it that was shapes".

**`svgread.parse_path`, `parse_transform`, `parse_paint`, `parse_length`,
`parse_view_box` and `parse_dash_array` read one attribute each.** Lifting a
`d` attribute out of a font or an icon set is the most common thing anyone
does to an SVG.

**`svgdoc.to_path` turns a whole subtree into one path.** Every shape is
converted and every transform applied. A rasteriser wants that, and
`svgpath.flatten` turns the result into straight segments.

**`svgwrite.pretty` and `svgwrite.minimal` are the two write styles.**
`pretty` indents, writes newlines and keeps three decimals. `minimal` does
none of that, keeps two decimals and compacts paths.

## The rules a user needs

1. **A style is absolute, in a document this package built and in one it
   read.** Nothing in the tree inherits. The writer does not refactor common
   attributes back onto a group on the way out, because that would change what
   the tree means.
2. **SVG's default style is a black fill and no stroke.** A node built with
   `svgstyle.plain` draws a black shape. A caller who wanted an outline and set
   only the stroke gets a black shape with an outline on it.
3. **Every path command is absolute and no command is a shorthand.** The
   reader turns relative into absolute, expands `H` and `V` into `SvgLineTo`,
   and expands `S` and `T` into their long forms with the reflected control
   point computed. A written-out path is longer than the one that came in, and
   `svgwrite`'s `compact_paths` takes that size back on the way out. The tree
   is never shorthand.
4. **An arc stays an arc.** Most vector pipelines expand SVG's elliptical arc
   into cubics on the way in. This one does not, because an arc is exactly
   representable and a cubic approximation is not, so converting by default
   would silently change the geometry of every rounded rectangle that passed
   through. `svgpath.to_cubics` is there for a renderer with no arc primitive.
5. **`SvgArcTo`'s rotation is in radians.** SVG writes the attribute in
   degrees. The reader and the writer convert.
6. **A path that does not start with a `SvgMoveTo` draws nothing.** That is
   what SVG requires, and `svgpath.is_well_formed` is the question.
7. **An element or attribute this package does not model is skipped, not
   refused.** Gradients, patterns, masks, clip paths, filters, markers, `use`,
   `image`, `symbol`, `switch`, CSS and animation all pass through the reader
   without stopping it. A reader that refused every document with a `<style>`
   block would refuse most SVG files in the world.
   `svgread.parse_report` counts what was skipped and names the first few.
8. **A `url(#id)` paint survives as `SvgPaintRef`, and nothing resolves it.** A
   document that used a gradient comes back with its reference intact even
   though the gradient was skipped, so writing it out again names a paint
   server that is no longer there. `SvgReadReport.has_dangling_paint` is how a
   caller knows.
9. **A shape read in comes back as the same shape.** A `<rect>` is an
   `SvgRectShape`, not a path. That is what makes a document read and written
   back the document that went in.
10. **A fault means the text is not well-formed XML, or a number is not a
    number.** Nothing else is a fault. Every variant carries a byte offset into
    the string the caller handed over, so slicing around it shows what the
    parser was looking at.
11. **`svgdoc.text_advance_estimate` is an estimate, and it is the one number
    here that is not exact.** It is the string's length times the font size
    times a constant near the average advance of a proportional Latin face,
    which is right to within a fifth for ordinary text and wrong for anything
    else. It exists because `bounds` has to answer something for a text node,
    and a silent zero would make an automatically sized view box clip its own
    labels. A caller who needs the real width measures it with a font package
    and unions it in.
12. **An attribute is omitted on the way out when a reader would get the same
    value without it.** An inherited presentation attribute is written where
    it differs from the parent's value, and any other attribute where it
    differs from SVG's initial value. A size a shape needs, such as a
    rectangle's `width` or a circle's `r`, is always written. A document
    written by this package and read back gives the same tree.
13. **Numbers decide the output size, so `decimals` is on the write style.**
    Three decimal places on a view box a thousand units wide is a thousandth of
    a pixel. Trailing zeroes are always dropped, so 2.500 is written `2.5` and
    2.000 is written `2`.
14. **`svgwrite.number` never writes an exponent.** A naive float formatter
    emits `1e-7`, which is valid XML and invalid SVG. `number` and
    `svgwrite.escape` are public so that a caller writing an attribute this
    package does not model spells numbers and text the same way.
15. **`SvgTransform` and `SvgViewBox` hold the same numbers as geometry-nv's
    `GeomXform` and `GeomRectF`, and convert at the edge.** A document tree is
    boxed, because it nests, and a boxed aggregate cannot have an unboxed field
    (SPEC section 14.5). `svgdoc.to_xform`, `of_xform`, `view_box_rect` and
    `view_box_of` are the four conversions, and each is six field reads.
    geometry-nv owns the transform algebra and this package never reimplements
    it.
16. **`svgdoc.bounds` answers the rectangle in the coordinate system the
    subtree's parent uses.** A node's own transform is applied; its parent's is
    not. `svgdoc.flatten_transforms` composes every transform down from the
    root first.
17. **`svgdoc.find_by_id` answers the subtree's own root when no node carries
    the id.** `has_id` is the question that answers yes or no.
18. **The fill rule is geometry-nv's `GeomFillRule`, not a type of this
    package's own.** There is one fill rule in the registry rather than two
    that have to agree.
19. **A colour's alpha travels as `fill-opacity` or `stroke-opacity`.** SVG
    1.1 has no colour with an alpha. The writer writes the colour as
    `#rrggbb` and its alpha as the opacity, with at least three decimals so
    the alpha byte reads back unchanged. The reader multiplies the opacity
    into the colour's alpha.
20. **A `style` attribute outranks the presentation attributes beside it.**
    The reader applies an element's attributes first and its `style`
    declarations after them (SVG 1.1 section 6.4). A class selector or a
    `<style>` block is CSS and is not read.
21. **A value that is not finite has no SVG spelling.** `svgwrite.to_string`
    refuses a document holding one with `SvgBadNumber`. The streaming writer
    cannot refuse, and writes `NaN`, `inf` or `-inf`, which no reader
    accepts.

## What is not included

- **Gradients, patterns, masks, clip paths, filters and markers.** A `url(#id)`
  paint is preserved as a reference. Everything else in that list is dropped by
  the reader and cannot be constructed. A renderer that needs a paint server
  needs a package with one in it.
- **CSS and animation.** A `<style>` block is skipped and counted.
- **`use`, `image`, `symbol` and `switch`.** Same.
- **A nested `svg` element, an `a` element and `tspan` positioning.** A
  nested viewport and a link are skipped with their contents. The text of a
  `tspan` is kept in its run, and its own position and style are not.
- **`display`, `visibility` and the other presentation attributes not in
  the table above.** They are skipped and counted.
- **Text measurement.** Resolving a font family to glyph advances needs a font
  file, which needs a filesystem, which this package does not have. See rule
  11.
- **Rendering.** There is no rasteriser here.
  [raster-nv](https://novo-lang.org/packages/raster-nv) is the package that
  draws, and `svgpath.flatten` and `svgdoc.to_path` are what it takes.
- **A device build.** There is no `tests/embedded_probe.nv` and no claim that
  any module runs on a microcontroller. A document tree is allocation from end
  to end.

## Related packages

- [geometry-nv](https://novo-lang.org/packages/geometry-nv) owns the points,
  the rectangles, the transforms and the fill rule. This package carries the
  numbers and converts at the edge, so the algebra lives in one place.
- [color-nv](https://novo-lang.org/packages/color-nv) owns the colour type.
  Every paint in a document is its `Srgba8`, which is also what png-nv and
  qoi-nv speak, so a chart rendered to SVG and the same chart rendered to a PNG
  cannot disagree about a shade.
- [font-nv](https://novo-lang.org/packages/font-nv) reads font files. A glyph
  outline comes out as one of this package's paths.
- [raster-nv](https://novo-lang.org/packages/raster-nv) draws these shapes into
  a surface.
- `std.xml` in the standard library is a general XML parser. This package's
  reader is narrower and answers a document rather than a tree of elements.

## Tests

```bash
novo test tests/svg_tests.nv          # one suite; the table below lists them all
bash tests/coverage.sh                # every suite, and the line coverage of src/
```

| Suite | What it asserts |
| --- | --- |
| `svg_tests.nv` | The API: the style, the path, the document, a write and a read |
| `write_tests.nv` | The writer's output byte for byte, in both styles, and the streaming writer's chunks joining to the same text |
| `pathdata_tests.nv` | 43 `d` attributes, each read as the independent Python reader `tools/pathref.py` reads it, or refused at the same byte |
| `roundtrip_tests.nv` | Hand-written documents, one as a drawing program exports it: what the reader makes of them, and a write and a read giving the same text again |
| `reader_tests.nv` | Every refusal at its exact offset, and every attribute the reader takes |
| `geometry_tests.nv` | Arc boxes worked out by hand; tight boxes against flattened ones; paths through rotation, scale, mirror and shear against their points mapped one by one |
| `format_tests.nv` | The number spelling, the style keywords and the fault messages |

The writer's goldens were checked to be well-formed XML with Python's
`xml.etree`. `python3 tools/pathref.py > tests/pathdata_tests.nv` writes the
path data suite again from its cases.

The reference implementations are [usvg](https://github.com/RazrFalcon/resvg)
for the reader's contract and [svgwrite](https://github.com/mozman/svgwrite)
for the writer's shape. Both are permissively licensed. Every test declares
the effects `[io]` and nothing else, and no function in the package declares
any effect.

## Licence

Apache-2.0. See `LICENSE`.

<!-- docs/writing-a-readme.md is the style guide for this page. -->
