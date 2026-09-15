# svg-nv

SVG is a vector image format written as XML, specified in
[SVG 1.1](https://www.w3.org/TR/SVG11/). This package holds an SVG document as
a value in novo-lang: a tree of shapes, each carrying its own geometry, its own
style and its own transform. Its points and transforms are
[geometry-nv](https://novo-lang.org/packages/geometry-nv)'s and its colours are
[color-nv](https://novo-lang.org/packages/color-nv)'s. Two other packages on
the registry are built on it: [font-nv](https://novo-lang.org/packages/font-nv)
and [raster-nv](https://novo-lang.org/packages/raster-nv).

**Status: NOT IMPLEMENTED — interface only.** Every function is declared with
its full signature, but every body is a `todo()` that panics when called. The
package is published so its design can be reviewed and depended on before it
is implemented. Version 0.1.0 will be the first working release.

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

Build and test with `novo pkg build` and `novo test`. Today `novo test` fails
on purpose: every test reaches a `not implemented: svg-nv.<module>.<fn>` panic.
The tests are the specification the implementation will have to satisfy.

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
as text.** Each chunk is one complete element: an opening tag through a
closing tag for a leaf, and an opening tag alone for a group. A scatter plot
with a million points never exists as a string.

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
12. **An attribute whose value is SVG's own default is omitted on the way
    out.** An attribute a renderer needs to get the geometry right is always
    written, default or not. Those two rules together are why a document
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

## What is not included

- **Gradients, patterns, masks, clip paths, filters and markers.** A `url(#id)`
  paint is preserved as a reference. Everything else in that list is dropped by
  the reader and cannot be constructed. A renderer that needs a paint server
  needs a package with one in it.
- **CSS and animation.** A `<style>` block is skipped and counted.
- **`use`, `image`, `symbol` and `switch`.** Same.
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
novo test tests/svg_tests.nv    # the document, the style, the path and the round trip
```

The reference implementations are [usvg](https://github.com/RazrFalcon/resvg)
for the reader's contract and
[svgwrite](https://github.com/mozman/svgwrite) for the writer's shape. Both
are permissively licensed, and usvg's own test corpus is the oracle.

The suite states usvg's contract as assertions: that a parsed document carries
absolute styles, that paths come out absolute and free of shorthand, and that
a shape is still a shape. Each case fixes a small document and an exact
answer. Every test declares the effects `[io]` and nothing else, which is the
claim: a writer that had needed to write anywhere, or a reader that had needed
to open anything, would have declared a file effect here.

The tests compile today and fail at run, each on the
`not implemented: svg-nv.<module>.<fn>` panic that is its body. That is the
expected state of an interface release. They turn green one at a time as
bodies land. `novo test --isolate tests/svg_tests.nv` prints one verdict per
test.

## Implementation status

| Item | Implemented |
| --- | --- |
| `svgdoc.SvgDocument`, `.SvgNode`, `.SvgShape`, `.SvgTransform`, `.SvgViewBox` | the types are declared; nothing constructs one |
| `svgdoc.document`, `.document_with`, `.add`, `.child_count_of`, `.document_bounds` | no |
| `svgdoc.view_box`, `.view_box_rect`, `.view_box_of`, `.no_transform`, `.to_xform`, `.of_xform` | no |
| `svgdoc.group`, `.rect`, `.rounded_rect`, `.circle`, `.ellipse`, `.line` | no |
| `svgdoc.polyline`, `.polygon`, `.path`, `.text` | no |
| `svgdoc.with_transform`, `.with_id`, `.with_style`, `.add_child` | no |
| `svgdoc.child_count`, `.node_count`, `.is_leaf`, `.shape_tag`, `.walk` | no |
| `svgdoc.find_by_id`, `.has_id`, `.flatten_transforms`, `.bounds` | no |
| `svgdoc.text_advance_estimate`, `.to_path` | no |
| `svgstyle.SvgStyle`, `.SvgPaint`, `.SvgLineCap`, `.SvgLineJoin`, `.SvgTextAnchor` | the types are declared; nothing constructs one |
| `svgstyle.SvgUnitKind`, `.SvgLength`, `.SvgFontSpec` | the types are declared; nothing constructs one |
| `svgstyle.plain`, `.filled`, `.stroked` | no |
| `svgstyle.with_fill`, `.with_stroke`, `.with_dash`, `.with_opacity`, `.with_font`, `.with_anchor` | no |
| `svgstyle.default_font`, `.font`, `.user`, `.px`, `.percent`, `.to_user_units` | no |
| `svgstyle.unit_suffix`, `.length_to_string`, `.paint_to_string`, `.paint_opacity` | no |
| `svgstyle.cap_to_string`, `.join_to_string`, `.anchor_to_string`, `.fill_rule_to_string` | no |
| `svgstyle.is_visible` | no |
| `svgpath.SvgPathCmd`, `.SvgPath`, `.SvgSubpath` | the types are declared; nothing constructs one |
| `svgpath.empty`, `.of_commands`, `.push`, `.move_to`, `.line_to` | no |
| `svgpath.cubic_to`, `.quad_to`, `.arc_to`, `.close` | no |
| `svgpath.of_rect`, `.of_ellipse`, `.of_points` | no |
| `svgpath.command_count`, `.commands_of`, `.subpath_count`, `.is_well_formed` | no |
| `svgpath.current_point`, `.bounds`, `.length` | no |
| `svgpath.flatten`, `.to_cubics`, `.quads_to_cubics`, `.transform` | no |
| `svgpath.to_string`, `.to_string_compact` | no |
| `svgwrite.SvgWriteStyle`, `.SvgWriter` | the types are declared; nothing constructs one |
| `svgwrite.pretty`, `.minimal`, `.to_string`, `.node_to_string` | no |
| `svgwrite.writer`, `.next_chunk`, `.is_done`, `.progress`, `.byte_length` | no |
| `svgwrite.number`, `.escape`, `.transform_attr` | no |
| `svgread.SvgReadReport` | the type is declared; nothing constructs one |
| `svgread.parse`, `.parse_report`, `.parse_within`, `.looks_like_svg` | no |
| `svgread.parse_path`, `.parse_transform`, `.parse_length`, `.parse_view_box` | no |
| `svgread.parse_paint`, `.parse_dash_array` | no |
| `svgfault.SvgFault`, `.offset_of` | the type is declared; `offset_of` is not implemented |

## Licence

Apache-2.0. See `LICENSE`.

<!-- docs/writing-a-readme.md is the style guide for this page. -->
