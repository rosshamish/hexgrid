"""
module hexgrid provides functions for working with a hexagonal settlers of catan grid. 

This module implements the coordinate system described in Robert S. Thomas's PhD dissertation on 
JSettlers2, Appendix A. See the project at https://github.com/jdmonin/JSettlers2 for details.

Grids have tiles, nodes, and edges. Tiles, nodes, and edges all have coordinates
on the grid. Tiles also have identifiers numbered counter-clockwise starting from
the north-west edge. There are 19 tiles.

Adjacent locations can be computed by adding an offset to the given location. These
offsets are defined as dictionaries named _<type1>_<type2>_offsets, mapping offset->direction.
This direction is a cardinal direction represented as a string.

The edge and node coordinate spaces share values. That is, the coordinate value is
not enough to uniquely identify a location on the grid. For that reason, it is recommended
to represent locations as a (CoordType, 0xCoord) pair, each of which is guaranteed
to be unique.

See individual methods for usage.
"""
import logging

__author__ = "Ross Anderson <ross.anderson@ualberta.ca>"
__version__ = "0.1.1"


EDGE = 0
NODE = 1
TILE = 2

_tile_id_to_coord = {
    # 1-19 clockwise starting from Top-Left
    1: 0x37, 12: 0x59, 11: 0x7B,
    2: 0x35, 13: 0x57, 18: 0x79, 10: 0x9B,
    3: 0x33, 14: 0x55, 19: 0x77, 17: 0x99, 9: 0xBB,
    4: 0x53, 15: 0x75, 16: 0x97, 8: 0xB9,
    5: 0x73, 6: 0x95, 7: 0xB7
}

_tile_tile_offsets = {
    # tile_coord - tile_coord
    -0x20: 'NW',
    -0x22: 'W',
    -0x02: 'SW',
    +0x20: 'SE',
    +0x22: 'E',
    +0x02: 'NE',
}

_tile_node_offsets = {
    # node_coord - tile_coord
    +0x01: 'N',
    -0x10: 'NW',
    -0x01: 'SW',
    +0x10: 'S',
    +0x21: 'SE',
    +0x12: 'NE',
}

_tile_edge_offsets = {
    # edge_coord - tile_coord
    -0x10: 'NW',
    -0x11: 'W',
    -0x01: 'SW',
    +0x10: 'SE',
    +0x11: 'E',
    +0x01: 'NE',
}


def location(hexgrid_type, coord):
    """
    Returns a formatted string representing the coordinate. The format depends on the
    coordinate type.

    Tiles look like: 1, 12
    Nodes look like: (1 NW), (12 S)
    Edges look like: (1 NW), (12 SE)

    :param hexgrid_type: hexgrid.TILE, hexgrid.NODE, hexgrid.EDGE
    :param coord: integer coordinate in this module's hexadecimal coordinate system
    :return: formatted string for display
    """
    if hexgrid_type == TILE:
        return str(coord)
    elif hexgrid_type == NODE:
        tile_id = nearest_tile_to_node(coord)
        dirn = tile_node_offset_to_direction(coord - tile_id_to_coord(tile_id))
        return '({} {})'.format(tile_id, dirn)
    elif hexgrid_type == EDGE:
        tile_id = nearest_tile_to_edge(coord)
        dirn = tile_edge_offset_to_direction(coord - tile_id_to_coord(tile_id))
        return '({} {})'.format(tile_id, dirn)
    else:
        logging.warning('unsupported hexgrid_type={}'.format(hexgrid_type))
        return None


def coastal_tile_ids():
    """
    Returns a list of tile identifiers which lie on the border of the grid.
    """
    return list(filter(lambda tid: len(coastal_edges(tid)) > 0, legal_tile_ids()))


def coastal_coords():
    """
    A coastal coord is a 2-tuple: (tile id, direction).

    An edge is coastal if it is on the grid's border.

    :param tile_id:
    :return: list( (tile_id, direction) )
    """
    coast = list()
    for tile_id in coastal_tile_ids():
        tile_coord = tile_id_to_coord(tile_id)
        for edge_coord in coastal_edges(tile_id):
            dirn = tile_edge_offset_to_direction(edge_coord - tile_coord)
            if tile_id_in_direction(tile_id, dirn) is None:
                coast.append((tile_id, dirn))
    # logging.debug('coast={}'.format(coast))
    return coast


def coastal_edges(tile_id):
    """
    Returns a list of coastal edge coordinate.

    An edge is coastal if it is on the grid's border.
    :param tile_id:
    :return: list(int)
    """
    edges = list()
    tile_coord = tile_id_to_coord(tile_id)
    for edge_coord in edges_touching_tile(tile_id):
        dirn = tile_edge_offset_to_direction(edge_coord - tile_coord)
        if tile_id_in_direction(tile_id, dirn) is None:
            edges.append(edge_coord)
    return edges


def tile_id_in_direction(from_tile_id, direction):
    """
    Variant on direction_to_tile. Returns None if there's no tile there.

    :param from_tile_id: tile identifier, int
    :param direction: str
    :return: tile identifier, int or None
    """
    coord_from = tile_id_to_coord(from_tile_id)
    for offset, dirn in _tile_tile_offsets.items():
        if dirn == direction:
            coord_to = coord_from + offset
            if coord_to in legal_tile_coords():
                return tile_id_from_coord(coord_to)
    return None


def direction_to_tile(from_tile_id, to_tile_id):
    """
    Convenience method wrapping tile_tile_offset_to_direction. Used to get the direction
    of the offset between two tiles. The tiles must be adjacent.

    :param from_tile_id: tile identifier, int
    :param to_tile_id: tile identifier, int
    :return: direction from from_tile to to_tile, str
    """
    coord_from = tile_id_to_coord(from_tile_id)
    coord_to = tile_id_to_coord(to_tile_id)
    direction = tile_tile_offset_to_direction(coord_to - coord_from)
    # logging.debug('Tile direction: {}->{} is {}'.format(
    #     from_tile.tile_id,
    #     to_tile.tile_id,
    #     direction
    # ))
    return direction


def tile_tile_offset_to_direction(offset):
    """
    Get the cardinal direction of a tile-tile offset. The tiles must be adjacent.

    :param offset: tile_coord - tile_coord, int
    :return: direction of the offset, str
    """
    try:
        return _tile_tile_offsets[offset]
    except KeyError:
        logging.critical('Attempted getting direction of non-existent tile-tile offset={:x}'.format(offset))
        return 'ZZ'


def tile_node_offset_to_direction(offset):
    """
    Get the cardinal direction of a tile-node offset. The tile and node must be adjacent.

    :param offset: node_coord - tile_coord, int
    :return: direction of the offset, str
    """
    try:
        return _tile_node_offsets[offset]
    except KeyError:
        logging.critical('Attempted getting direction of non-existent tile-node offset={:x}'.format(offset))
        return 'ZZ'


def tile_edge_offset_to_direction(offset):
    """
    Get the cardinal direction of a tile-edge offset. The tile and edge must be adjacent.

    :param offset: edge_coord - tile_coord, int
    :return: direction of the offset, str
    """
    try:
        return _tile_edge_offsets[offset]
    except KeyError:
        logging.critical('Attempted getting direction of non-existent tile-edge offset={:x}'.format(offset))
        return 'ZZ'


def edge_coord_in_direction(tile_id, direction):
    """
    Returns the edge coordinate in the given direction at the given tile identifier.

    :param tile_id: tile identifier, int
    :param direction: direction, str
    :return: edge coord, int
    """
    tile_coord = tile_id_to_coord(tile_id)
    for edge_coord in edges_touching_tile(tile_id):
        if tile_edge_offset_to_direction(edge_coord - tile_coord) == direction:
            return edge_coord
    raise ValueError('No edge found in direction={} at tile_id={}'.format(
        direction,
        tile_id
    ))



def tile_id_to_coord(tile_id):
    """
    Convert a tile identifier to its corresponding grid coordinate.

    :param tile_id: tile identifier, Tile.tile_id
    :return: coordinate of the tile, int
    """
    try:
        return _tile_id_to_coord[tile_id]
    except KeyError:
        logging.critical('Attempted conversion of non-existent tile_id={}'.format(tile_id))
        return -1


def tile_id_from_coord(coord):
    """
    Convert a tile coordinate to its corresponding tile identifier.

    :param coord: coordinate of the tile, int
    :return: tile identifier, Tile.tile_id
    """
    for i, c in _tile_id_to_coord.items():
        if c == coord:
            return i
    raise Exception('Tile id lookup failed, coord={} not found in map'.format(hex(coord)))


def nearest_tile_to_edge(edge_coord):
    """
    Convenience method wrapping nearest_tile_to_edge_using_tiles. Looks at all tiles in legal_tile_ids().
    Returns a tile identifier.

    :param edge_coord: edge coordinate to find an adjacent tile to, int
    :return: tile identifier of an adjacent tile, Tile.tile_id
    """
    return nearest_tile_to_edge_using_tiles(legal_tile_ids(), edge_coord)


def nearest_tile_to_edge_using_tiles(tile_ids, edge_coord):
    """
    Get the first tile found adjacent to the given edge. Returns a tile identifier.

    :param tile_ids: tiles to look at for adjacency, list(Tile.tile_id)
    :param edge_coord: edge coordinate to find an adjacent tile to, int
    :return: tile identifier of an adjacent tile, Tile.tile_id
    """
    for tile_id in tile_ids:
        if edge_coord - tile_id_to_coord(tile_id) in _tile_edge_offsets.keys():
            return tile_id
    logging.critical('Did not find a tile touching edge={}'.format(edge_coord))


def nearest_tile_to_node(node_coord):
    """
    Convenience method wrapping nearest_tile_to_node_using_tiles. Looks at all tiles in legal_tile_ids().
    Returns a tile identifier.

    :param node_coord: node coordinate to find an adjacent tile to, int
    :return: tile identifier of an adjacent tile, Tile.tile_id
    """
    return nearest_tile_to_node_using_tiles(legal_tile_ids(), node_coord)


def nearest_tile_to_node_using_tiles(tile_ids, node_coord):
    """
    Get the first tile found adjacent to the given node. Returns a tile identifier.

    :param tile_ids: tiles to look at for adjacency, list(Tile.tile_id)
    :param node_coord: node coordinate to find an adjacent tile to, int
    :return: tile identifier of an adjacent tile, Tile.tile_id
    """
    for tile_id in tile_ids:
        if node_coord - tile_id_to_coord(tile_id) in _tile_node_offsets.keys():
            return tile_id
    logging.critical('Did not find a tile touching node={}'.format(node_coord))


def edges_touching_tile(tile_id):
    """
    Get a list of edge coordinates touching the given tile.

    :param tile_id: tile identifier, Tile.tile_id
    :return: list of edge coordinates touching the given tile, list(int)
    """
    coord = tile_id_to_coord(tile_id)
    edges = []
    for offset in _tile_edge_offsets.keys():
        edges.append(coord + offset)
    # logging.debug('tile_id={}, edges touching={}'.format(tile_id, edges))
    return edges


def nodes_touching_tile(tile_id):
    """
    Get a list of node coordinates touching the given tile.

    :param tile_id: tile identifier, Tile.tile_id
    :return: list of node coordinates touching the given tile, list(int)
    """
    coord = tile_id_to_coord(tile_id)
    nodes = []
    for offset in _tile_node_offsets.keys():
        nodes.append(coord + offset)
    # logging.debug('tile_id={}, nodes touching={}'.format(tile_id, nodes))
    return nodes


def nodes_touching_edge(edge_coord):
    """
    Returns the two node coordinates which are on the given edge coordinate.

    :return: list of 2 node coordinates which are on the given edge coordinate, list(int)
    """
    a, b = hex_digit(edge_coord, 1), hex_digit(edge_coord, 2)
    if a % 2 == 0 and b % 2 == 0:
        return [coord_from_hex_digits(a, b + 1),
                coord_from_hex_digits(a + 1, b)]
    else:
        return [coord_from_hex_digits(a, b),
                coord_from_hex_digits(a + 1, b + 1)]


def legal_edge_coords():
    """
    Return all legal edge coordinates on the grid.
    """
    edges = set()
    for tile_id in legal_tile_ids():
        for edge in edges_touching_tile(tile_id):
            edges.add(edge)
    logging.debug('Legal edge coords({})={}'.format(len(edges), edges))
    return edges


def legal_node_coords():
    """
    Return all legal node coordinates on the grid
    """
    nodes = set()
    for tile_id in legal_tile_ids():
        for node in nodes_touching_tile(tile_id):
            nodes.add(node)
    logging.debug('Legal node coords({})={}'.format(len(nodes), nodes))
    return nodes


def legal_tile_ids():
    """
    Return all legal tile identifiers on the grid. In the range [1,19] inclusive.
    """
    return set(_tile_id_to_coord.keys())


def legal_tile_coords():
    """
    Return all legal tile coordinates on the grid
    """
    return set(_tile_id_to_coord.values())


def hex_digit(coord, digit=1):
    """
    Returns either the first or second digit of the hexadecimal representation of the given coordinate.
    :param coord: hexadecimal coordinate, int
    :param digit: 1 or 2, meaning either the first or second digit of the hexadecimal
    :return: int, either the first or second digit
    """
    if digit not in [1,2]:
        raise ValueError('hex_digit can only get the first or second digit of a hex number, was passed digit={}'.format(
            digit
        ))
    return int(hex(coord)[1+digit], 16)


def coord_from_hex_digits(digit_1, digit_2):
    """
    Returns an integer representing the hexadecimal coordinate with the two given hexadecimal digits.

    >> hex(coord_from_hex_digits(1, 3))
    '0x13'
    >> hex(coord_from_hex_digits(1, 10))
    '0x1A'

    :param digit_1: first digit, int
    :param digit_2: second digit, int
    :return: hexadecimal coordinate, int
    """
    return digit_1*16 + digit_2


def rotate_direction(hexgrid_type, direction, ccw=True):
    """
    Takes a direction string associated with a type of hexgrid element, and rotates it one tick in the given direction.
    :param direction: string, eg 'NW', 'N', 'SE'
    :param ccw: if True, rotates counter clockwise. Otherwise, rotates clockwise.
    :return: the rotated direction string, eg 'SW', 'NW', 'S'
    """
    if hexgrid_type in [TILE, EDGE]:
        directions = ['NW', 'W', 'SW', 'SE', 'E', 'NE', 'NW'] if ccw \
                else ['NW', 'NE', 'E', 'SE', 'SW', 'W', 'NW']
        return directions[directions.index(direction) + 1]
    elif hexgrid_type in [NODE]:
        directions = ['N', 'NW', 'SW', 'S', 'SE', 'NE', 'N'] if ccw \
            else ['N', 'NE', 'SE', 'S', 'SW', 'NW', 'N']
        return directions[directions.index(direction) + 1]
    else:
        raise ValueError('Invalid hexgrid type={} passed to rotate direction'.format(hexgrid_type))
