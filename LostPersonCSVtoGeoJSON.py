import argparse
import csv
from datetime import datetime
import json
from typing import Dict, Tuple, List
import uuid

from math import asin, atan2, cos, degrees, radians, sin

def get_point_at_distance(lat1: float, 
                          lon1 :float, 
                          d: float, 
                          bearing : float, 
                          R : float = 6371) -> Tuple[float, float] :
    """
    lat: initial latitude, in decimal degrees
    lon: initial longitude, in decimal degrees
    d: target distance from initial point, in kilometers
    bearing: (true) heading in degrees
    R: optional radius of sphere, defaults to mean radius of earth in km

    Returns new lat/lon coordinate {d}km from initial, in degrees
    """
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    a = radians(bearing)
    lat2 = asin(sin(lat1) * cos(d/R) + cos(lat1) * sin(d/R) * cos(a))
    lon2 = lon1 + atan2(
        sin(a) * sin(d/R) * cos(lat1),
        cos(d/R) - sin(lat1) * sin(lat2)
    )
    return (degrees(lat2), degrees(lon2),)

def feet_to_km(feet : float) -> float:
    return feet * 0.0003048

def km_to_feet(km : float) -> float:
    return km / 0.0003048

# A function that takes a string of the format "keyword1:value1,keyword2:value2,..." 
# and returns a dictionary mapping the keywords to the corresponding values
def parse_keyword_value_arg(keywordValueString: str) -> Dict[str, str]:
    parsedDict = {}
    for pair in keywordValueString.split(','):
        keyword, value = pair.split(':')
        parsedDict[keyword] = value
    return parsedDict


def is_float(string: str) -> bool:
    try:
        float(string)
        return True
    except ValueError:
        return False
    
def csv_to_json(csv_file_path : str, json_file_path : str =None) -> List[Dict[str, str]]:
    """
    Convert a CSV file to JSON array of objects.
    
    Args:
        csv_file_path: Path to the input CSV file
        json_file_path: Path to save the output GeoJSON file (optional)
    
    Returns:
        List of dictionaries with header names as keys
    """
    json_array = []
    
    with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            json_array.append(row)
    
    if json_file_path:
        with open(json_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(json_array, json_file, indent=2)
    
    return json_array

# Parse command line arguments
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Convert CSV to JSON.')
    parser.add_argument('-i', '--input', required=True, help='Input CSV file path')
    parser.add_argument('-o', '--output', required=True, help='Output JSON file path')
    parser.add_argument('--no-ipps', 
                        action='store_true', 
                        help='Do not include IPP markers or lines in the output GeoJSON')
    parser.add_argument('--outcome-symbols', 
                        default='Deceased:circle-c,Life Saved:circle-b,Person Assisted:circle-a,Not Located:circle-u', 
                        help='Comma separated list of keywords and corresponding marker symbols to use \
                        for outcomes, in the format "keyword1:symbol1,keyword2:symbol2,...". If not provided, \
                        default symbols will be used for each outcome. \
                        Allowed keywords are [Deceased, Life Saved, Person Assisted, Not Located]')
    parser.add_argument('--outcome-colors', 
                        default='Deceased:#FF0000,Life Saved:#0000FF,Person Assisted:#00FF00,Not Located:#000000',
                        help='Comma separated list of keywords and corresponding marker colors to use \
                        for outcomes, in the format "keyword1:#RRGGBB,keyword2:#RRGGBB,...". If not provided, \
                        default colors will be used for each outcome. \
                        Allowed keywords are [Deceased, Life Saved, Person Assisted, Not Located]')
    parser.add_argument('--outcome-circle-radius',
                        type=float,
                        default=100.0,
                        help='Radius in feet to use for circles around outcome markers. Default is 100 feet. \
                              Set to 0 to not include outcome circles.')
    parser.add_argument('--outcome-circle-segments',
                        type=int,
                        default=36,
                        help='Number of segments to use for the circles around outcome markers. Default is 36.')
    parser.add_argument('--print-json',
                        action='store_true',
                        help='Print the resulting GeoJSON to the console after conversion')
    parser.add_argument('--outcome-folder', 
                        default='Finds', 
                        help='Name of the folder to put outcome markers in. Default is "Finds".')
    parser.add_argument('--ipp-folder',
                        default='IPPs',
                        help='Name of the folder to put IPP markers and lines in. Default is "IPPs".')
    return parser.parse_args()

# Function to add a folder feature with a provided name to a collection of features and return the uuid of the folder as a string
def add_folder_feature(features: list, folder_name: str, folder_visible: bool, label_visible: bool) -> str:
    folder_uuid = str(uuid.uuid4())
    folder_feature = {
        "geometry": None,
        "type": "Feature",
        "properties": {
            "title": folder_name,
            "class": "Folder",
            "labelVisible": label_visible,
            "visible": folder_visible
        },
        "id": folder_uuid
    }
    features.append(folder_feature)
    return folder_uuid

def get_findmarker_properties(data: Dict[str, str], 
                              folder_uuid: str, 
                              outcome_symbols: Dict[str, str], 
                              outcome_colors: Dict[str, str]) -> Dict[str, str]:
    
    # Implementation for getting find marker properties from a CSV row of data
    properties = {}
    if(is_float(data['Find Lng']) and is_float(data['Find Lat'])):
        # Dump all rows not otherwise used as properties
        properties = {key: value for key, value in data.items() if key not in ['Find Lng', 'Find Lat', 'Mission #']}

        # Title is the mission number string
        title = data['Mission #']

        # It is an error in the incident data if the mission number starts with a '#', 
        # but if it does, remove the '#' from the title
        if (title.startswith('#')):
            title = title[1:]
        properties['title'] = title

        # Marker size
        properties['marker-size'] = '1'

        # Outcome based properties, iterating on color_outcome keys 
        # in *insertion order* for that dictionary to ensure that if an outcome 
        # contains multiple of the keywords, the most severe outcome will determine 
        # the marker color and symbol   
        outcome = data.get('Outcome')
        properties['marker-color'] = outcome_colors.get('Not Located')
        properties['marker-symbol'] = outcome_symbols.get('Not Located')
        for (color_outcome_key, color_outcome_value) in outcome_colors.items():
            if (outcome.find(color_outcome_key) != -1):
                properties['marker-color'] = color_outcome_value
                properties['marker-symbol'] = outcome_symbols.get(color_outcome_key, outcome_symbols.get('Not Located'))
                break

        properties['class'] = 'Marker'
        properties['folderId'] = folder_uuid

        return properties

def get_ippmarker_properties(data: Dict[str, str], folder_uuid: str, outcome_colors: Dict[str, str]) -> Dict[str, str]:
    # Implementation for getting IPP marker properties from a CSV row of data
    properties = {}
    # Title is the mission number + ' IPP'
    # It is an error in the incident data if the mission number starts with a '#', 
    # but if it does, remove the '#' from the title
    title = data['Mission #']
    if (title.startswith('#')):
            title = title[1:]
    space_index = title.find(' ')
    if (space_index != -1):
        properties['title'] = title[:space_index] + ' IPP'
    else:
        properties['title'] = title + ' IPP'

    # Marker size
    properties['marker-size'] = '1'
    properties['marker-symbol'] = 'point'
    properties['class'] = 'Marker'
    properties['folderId'] = folder_uuid

    # Outcome based properties, iterating on color_outcome keys 
    # in *insertion order* for that dictionary to ensure that if an outcome 
    # contains multiple of the keywords, the most severe outcome will determine 
    # the marker color and symbol       
    outcome = data.get('Outcome')
    properties['marker-color'] = outcome_colors.get('Not Located')
    for (color_outcome_key, color_outcome_value) in outcome_colors.items():
        if (outcome.find(color_outcome_key) != -1):
            properties['marker-color'] = color_outcome_value
            break

    return properties
    
def get_line_properties(data: Dict[str, str], 
                        folder_uuid: str,
                        outcome_colors: Dict[str, str], 
                        additional_title: str = "", 
                        pattern: str = "") -> Dict[str, str]:
    # Implementation for getting line properties from a CSV row of data
    properties = {}
    # Title is the mission number
    # It is an error in the incident data if the mission number starts with a '#', 
    # but if it does, remove the '#' from the title
    title = data['Mission #']
    if (title.startswith('#')):
        title = title[1:]
    space_index = title.find(' ')
    if (space_index != -1):
        properties['title'] = title[:space_index]
    else:
        properties['title'] = title
    properties['title'] += additional_title
    properties['stroke-opacity'] = 1
    properties['stroke-width'] = 2
    if (len(pattern) > 0):
        properties['pattern'] = pattern
    properties['class'] = 'Shape'
    properties['folderId'] = folder_uuid

    # Outcome based properties, iterating on color_outcome keys 
    # in *insertion order* for that dictionary to ensure that if an outcome 
    # contains multiple of the keywords, the most severe outcome will determine 
    # the marker color and symbol       
    outcome = data.get('Outcome')
    properties['stroke'] = outcome_colors.get('Not Located')
    for (color_outcome_key, color_outcome_value) in outcome_colors.items():
        if (outcome.find(color_outcome_key) != -1):
            properties['stroke'] = color_outcome_value
            break

    return properties


def convert_csv_to_geojson(csv_file_path : str, 
                           no_ipps: bool, 
                           outcome_symbol_overrides: str, 
                           outcome_color_overrides: str, 
                           outcome_circle_radius: float,
                           outcome_circle_segments: int,
                           outcome_folder: str,
                           ipp_folder: str,
                           geojson_file_path : str,) -> Dict:
    """
    Convert a CSV file to GeoJSON format.
    
    Args:
        csv_file_path: Path to the input CSV file
        geojson_file_path: Path to save the output GeoJSON file (optional)
    
    Returns:
        GeoJSON object as a dictionary
    """
    features = []
    
    # Add folders for finds and IPPs
    find_folder_uuid = add_folder_feature(features, outcome_folder, True, True)

    if (not no_ipps):
        ipp_folder_uuid = add_folder_feature(features, ipp_folder, False, False)

    # Default outcome colors
    outcome_colors = {
        'Deceased': '#FF0000',
        'Life Saved': '#0000FF',
        'Person Assisted': '#00FF00',
        'Not Located': '#000000'
    }
    # Override default outcome colors if provided in arguments
    outcome_colors.update(parse_keyword_value_arg(outcome_color_overrides))

    # Default outcome symbols
    outcome_symbols = {
        'Deceased': 'circle-c',
        'Life Saved': 'circle-b',
        'Person Assisted': 'circle-a',
        'Not Located': 'circle-u'
    }    
    # Override default outcome symbols if provided in arguments
    outcome_symbols.update(parse_keyword_value_arg(outcome_symbol_overrides))

    with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:

            # For rows with valid find location coordinates, create a GeoJSON feature for the 
            # find marker and add it to the features list, as well as possibly the 
            # IPP marker and line connecting the IPP marker to the find marker 
            # if the IPP coordinates are valid
            find_lat = row['Find Lat']
            find_lng = row['Find Lng']
            if(is_float(find_lng) and is_float(find_lat)):

                # Find markers
                find_properties = get_findmarker_properties(row, find_folder_uuid, outcome_symbols, outcome_colors)

                find_feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(find_lng), float(find_lat)]
                    },
                    "properties": find_properties
                }
                features.append(find_feature)

                # Range circles
                if(outcome_circle_radius > 0):
                    range_properties = get_line_properties(row, ipp_folder_uuid, outcome_colors,
                                                           ' ' + str(int(outcome_circle_radius)) + 'ft')
                    range_coordinates = []
                    rng = feet_to_km(outcome_circle_radius)
                    angle = 365 / outcome_circle_segments
                    for(vertex) in range(0, outcome_circle_segments):
                        # Note the order of coordinates in GeoJSON is (lng, lat)
                        coords = get_point_at_distance(float(find_lat), float(find_lng), rng, vertex * angle)
                        range_coordinates.append((coords[1], coords[0])) 

                    # Append closing coordinate to complete the circle
                    range_coordinates.append(range_coordinates[0])

                    range_circle_feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": range_coordinates
                        },
                        "properties": range_properties
                    }
                    features.append(range_circle_feature)

                # IPP markers and connecting lines
                if( not no_ipps):
                    # Get properties for the IPP marker fromt the CSV row and add the IPP marker 
                    # and line connecting the IPP marker to the find marker
                    if(is_float(row['IPP Lng']) and is_float(row['IPP Lat'])):
                        ipp_properties = get_ippmarker_properties(row, ipp_folder_uuid, outcome_colors)
                        ipp_feature = {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [float(row['IPP Lng']), float(row['IPP Lat'])]
                            },
                            "properties": ipp_properties                    }
                        features.append(ipp_feature)

                        # Add line feature connecting IPP to find location
                        line_properties = get_line_properties(row, 
                                                            ipp_folder_uuid,
                                                            outcome_colors,
                                                            '',
                                                            'M-5 8 L0 -2 L5 8 Z,100%,,T') # Line with arrow
                        line_feature = {
                            "type": "Feature",
                            "geometry": {
                                "type": "LineString",
                                "coordinates": [
                                    [float(row['IPP Lng']), float(row['IPP Lat'])],
                                    [float(row['Find Lng']), float(row['Find Lat'])]
                                ]
                            },
                            "properties": line_properties                    }
                        features.append(line_feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    if geojson_file_path:
        with open(geojson_file_path, 'w', encoding='utf-8') as geojson_file:
            json.dump(geojson, geojson_file, indent=2)
    
    return geojson

if __name__ == "__main__":
    args = parse_args()
    result = convert_csv_to_geojson(args.input, 
                                    args.no_ipps, 
                                    args.outcome_symbols, 
                                    args.outcome_colors, 
                                    args.outcome_circle_radius,
                                    args.outcome_circle_segments,
                                    args.outcome_folder,
                                    args.ipp_folder,
                                    args.output)
    if(args.print_json):
        print(json.dumps(result, indent=2))