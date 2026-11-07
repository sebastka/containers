#!/usr/bin/env python3
"""Lift the square Element mark out of upstream's React component, as a standalone SVG.

Upstream draws its logo inline in src/components/logo.tsx and ships no icon file anywhere, so the
built dist/ has nothing to answer a browser's automatic request for /favicon.ico. This takes the
one square variant out of that component so the Dockerfile can rasterise it.

It fails rather than guessing. A favicon that quietly becomes an empty square is worse than a
build that stops and says the component moved.
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ElementTree

COMPONENT = "ElementLogoPart"

# JSX spells SVG's hyphenated attributes in camelCase and React converts them when it renders.
# Nothing does that here, so they are converted on the way out.
RENAME = {
    "fillRule": "fill-rule",
    "clipRule": "clip-rule",
    "fillOpacity": "fill-opacity",
    "strokeWidth": "stroke-width",
    "strokeLinecap": "stroke-linecap",
    "strokeLinejoin": "stroke-linejoin",
    "strokeOpacity": "stroke-opacity",
    "stopColor": "stop-color",
    "stopOpacity": "stop-opacity",
    "strokeDasharray": "stroke-dasharray",
    "strokeDashoffset": "stroke-dashoffset",
    "strokeMiterlimit": "stroke-miterlimit",
    "clipPath": "clip-path",
    "vectorEffect": "vector-effect",
    "shapeRendering": "shape-rendering",
    "paintOrder": "paint-order",
    "fontFamily": "font-family",
    "fontSize": "font-size",
    "fontWeight": "font-weight",
    "letterSpacing": "letter-spacing",
    "textAnchor": "text-anchor",
}

# Attributes that really are camelCase in SVG and must be left alone
SVG_CAMEL = {
    "viewBox",
    "preserveAspectRatio",
    "gradientUnits",
    "gradientTransform",
    "patternUnits",
    "clipPathUnits",
    "markerWidth",
    "markerHeight",
}

# The Element green. Asserted so a component that still parses but no longer draws the mark -- a
# placeholder, a themed variant -- does not reach the image as a blank icon.
BRAND = "#0DBD8B"
MIN_PATHS = 5

# The mark is one filled disc and the arcs cut out of it in white. --disc and --arcs recolour them
# on the way out, which is how the favicon is told apart from Element's other tabs.
ARCS = "white"


def fail(message):
    sys.exit(f"extract-logo: {message}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="upstream's src/components/logo.tsx")
    parser.add_argument("destination", help="the SVG to write")
    parser.add_argument("--disc", help=f"colour to use instead of {BRAND} for the disc")
    parser.add_argument("--arcs", help=f"colour to use instead of {ARCS} for the arcs")
    arguments = parser.parse_args()
    source, destination = arguments.source, arguments.destination

    with open(source, encoding="utf-8") as handle:
        text = handle.read()

    start = text.find(f"const {COMPONENT}")
    if start < 0:
        fail(f"{source} no longer defines {COMPONENT}: upstream moved or renamed the mark")

    open_tag = text.find("<svg", start)
    close_tag = text.find("</svg>", open_tag)
    if open_tag < 0 or close_tag < 0:
        fail(f"{COMPONENT} no longer contains an <svg> element")
    markup = text[open_tag:close_tag + len("</svg>")]

    # {...props} is the component's spread, not an attribute
    markup = re.sub(r"\s*\{\.\.\.\w+\}", "", markup)

    for jsx, svg in RENAME.items():
        markup = re.sub(rf"\b{jsx}=", f"{svg}=", markup)

    leftover = {
        name for name in re.findall(r"\b([a-z]+[A-Z]\w*)=", markup)
        if name not in SVG_CAMEL
    }
    if leftover:
        fail(f"{COMPONENT} uses JSX attributes this script does not know: {sorted(leftover)}")

    if "{" in markup:
        fail(f"{COMPONENT} interpolates values, so it cannot be rendered without React: {markup[:120]}")

    try:
        root = ElementTree.fromstring(markup)
    except ElementTree.ParseError as error:
        fail(f"{COMPONENT} did not yield well-formed XML: {error}")

    paths = root.findall("{http://www.w3.org/2000/svg}path") or root.findall("path")
    if len(paths) < MIN_PATHS:
        fail(f"expected at least {MIN_PATHS} paths in the mark, found {len(paths)}")
    if BRAND.lower() not in markup.lower():
        fail(f"the mark no longer uses {BRAND}: check it is still the Element logo")

    # Recoloured only once the mark is known to be the one expected, and counted so a changed
    # drawing cannot leave some of it in the old colours.
    for option, before, expected in ((arguments.disc, BRAND, 1), (arguments.arcs, ARCS, MIN_PATHS - 1)):
        if option is None:
            continue
        found = len(re.findall(rf'fill="{before}"', markup, flags=re.IGNORECASE))
        if found < expected:
            fail(f'expected at least {expected} fill="{before}" in the mark, found {found}')
        markup = re.sub(rf'fill="{before}"', f'fill="{option}"', markup, flags=re.IGNORECASE)

    with open(destination, "w", encoding="utf-8") as handle:
        handle.write(markup + "\n")

    print(f"extract-logo: {len(paths)} paths, {root.get('width')}x{root.get('height')}"
          f", disc {arguments.disc or BRAND}, arcs {arguments.arcs or ARCS}")


if __name__ == "__main__":
    main()
