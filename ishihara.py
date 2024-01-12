#!/usr/bin/env python3
from random import uniform
from colorsys import hsv_to_rgb
from svgwrite import rgb
from math import pi, log10, cos, sin, ceil, floor, sqrt


def circle(point, base_color) -> dict:
    variability: float = 0.3
    
    h: float = base_color[0]
    s: float = base_color[1]
    v: float = base_color[2] + (uniform(0, variability) - (variability / 2))
    v = 0 if v < 0 else v
    v = 1 if v > 1 else v

    r, g, b = hsv_to_rgb(h, s, v)
    color = '#%02x%02x%02x' % (round(r * 255), round(g * 255), round(b * 255))    
    return {
        r'cx': point[r'coords'][0],
        r'cy': point[r'coords'][1],
        r'r': point[r'smallest_dist'],
        r'fill': color
    }
#circle(range(1,6), range(1,4))


def make_circles(size, count, base_color_a, base_color_b, mask_function):
    points: list = []
    for _ in range(count):
        angle = uniform(0, 2 * pi)
        distance = uniform(1, 10)
        distance = log10(distance) / log10(10) * (size / 2)

        x = size / 2 + distance * cos(angle)
        y = size / 2 + distance * sin(angle)

        points.append({r'coords': (x, y), 'blx': None, r'bly': None, r'smallest_dist': None})
    seen = set()  # To prevent duplication
    blocks: list = []
    block_count_per_axis: int = int(log10(count) / log10(2))
    for p in points:
        block_x = (p[r'coords'][0] / size) * block_count_per_axis
        block_y = (p[r'coords'][1] / size) * block_count_per_axis
        blx = [x for x in [floor(block_x), ceil(block_x)] if not (x in seen or seen.add(x))]
        bly = [y for y in [floor(block_y), ceil(block_y)] if not (y in seen or seen.add(y))]

        p[r'blx'] = blx
        p[r'bly'] = bly

        for blx_item in blx:
            blocks.extend([[] for _ in range(blx_item - len(blocks) + 1)])
            for bly_item in bly:
                blocks[blx_item].extend([[] for _ in range(bly_item - len(blocks[blx_item]) + 1)])
  # now let's find out the smallest distance from a point to any
      
    for p in points:
        other_points: list = []
        for blx in p[r'blx']:
            for bly in p[r'bly']:
                for other_p in blocks[blx][bly]:
                    if other_p != p:
                        other_points.append(other_p)
        other_points = list(set(other_points))
        smallest_dist = size
        for op in other_points:
            if op[0] == p[0] and op[1] == p[1]:
                continue
            dist = sqrt(((op[0] - p[0])**2 + (op[1] - p[1])**2))
            if dist < smallest_dist:
                smallestdist = dist
            p[r'smallest_dist'] = smallestdist
        return [circle(p, base_color_a if mask_function(p) else base_color_b) for p in points]


def mask_function(point):
    x, y = point[r'coords']

    return x > y


def ishihara_circles(size, count, base_color_a, base_color_b, mask_function):
    circles: list = [{"circle": circle} for circle in make_circles(size, count, base_color_a, base_color_b, mask_function)]
    return circles


def ishihara_svg_data(size, count, base_color_a, base_color_b, mask_function):
    circles = ishihara_circles(size, count, base_color_a, base_color_b, mask_function)
    return {
        'width': size,
        'height': size,
        'cho_desc': circles,
    }



def make_mask_func(mask, size):
    mask_arr = [list(row) for row in mask.split('\n')]
    y_size = len(mask_arr)
    x_sizes = [len(row) for row in mask_arr]
    x_size = max(x_sizes)

    def mask_func(p):
        mx = round((p[0] / size) * x_size)
        my = round((p[1] / size) * y_size)
        if 0 <= my < y_size and 0 <= mx < x_size and mask_arr[my][mx] != " ":
            return 1
        return 0

    return mask_func



from lxml import etree
from math import isclose

def ishihara_svg_data(size, count, base_color_a, base_color_b, mask_func):
    circles = ishihara_circles(size, count, base_color_a, base_color_b, mask_func)
    return {
        'width': size,
        'height': size,
        'cho_desc': circles,
    }

def make_mask_func(mask, size):
    mask_arr = [list(row) for row in mask.split('\n')]
    y_size = len(mask_arr)
    x_sizes = [len(row) for row in mask_arr]
    x_size = max(x_sizes)

    def mask_func(p):
        mx = round((p[0] / size) * x_size)
        my = round((p[1] / size) * y_size)
        if 0 <= my < y_size and 0 <= mx < x_size and mask_arr[my][mx] != " ":
            return 1
        return 0

    return mask_func



from lxml import etree
import xmlschema

# Load the XML Schema
svg_xsd = xmlschema.XMLSchema(etree.parse('SVG.xsd'))
xlink_xsd = xmlschema.XMLSchema(etree.parse('xlink.xsd'))
xml_xsd = xmlschema.XMLSchema(etree.parse('xml.xsd'))

# Your existing XML data (replace this with your actual XML)
xml_data = """
<svg xmlns="http://www.w3.org/2000/svg" width="600" height="300">
    <!-- Your SVG content here -->
</svg>
"""

# Parse the XML document
root = etree.fromstring(xml_data)

# Validate against the corresponding XSD
if root.tag.endswith('svg'):
    svg_xsd.validate(root)
elif root.tag.endswith('xlink'):
    xlink_xsd.validate(root)
elif root.tag.endswith('xml'):
    xml_xsd.validate(root)
else:
    print("Unknown XML namespace")


mask = """
	 
    	###
       #  #
      #	  #  
     #######
	      #
          #
"""

# Example usage:
size = 600
count = 3000
base_color_a = [319, 0.36, 0.55]
base_color_b = [0, 0.36, 0.55]

data = ishihara_svg_data(size, count, base_color_a, base_color_b, make_mask_func(mask, size))

# Create XML document using lxml
svg_ns = "http://www.w3.org/2000/svg"
svg = etree.Element("{{{}}}svg".format(svg_ns), width=str(data['width']), height=str(data['height']))

# Add your SVG content here

# Print the XML document
print(etree.tostring(svg, pretty_print=True, encoding="utf-8").decode())
