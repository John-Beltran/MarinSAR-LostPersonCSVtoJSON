import argparse
import csv
from datetime import datetime
import json
from typing import Dict

#determine the marker-color from the 'Outcome' row value, or some other property if 'Outcome' is not available
color_outcome = {
    'Person Assisted': '#00FF00',
    'Life Saved': '#0000FF',
    'Deceased': '#FF0000',
    'Not Located': '#000000'
}

def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False
    
def csv_to_json(csv_file_path, json_file_path=None):
    """
    Convert a CSV file to JSON array of objects.
    
    Args:
        csv_file_path: Path to the input CSV file
        json_file_path: Path to save the output JSON file (optional)
    
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


def parse_args():
    parser = argparse.ArgumentParser(description='Convert CSV to JSON.')
    parser.add_argument('-i', '--input', default='input.csv', help='Input CSV file path')
    parser.add_argument('-o', '--output', default='output.json', help='Output JSON file path')
    return parser.parse_args()

def get_findmarker_properties(data: Dict[str, str]) -> Dict[str, str]:
    # Implementation for getting find marker properties from a CSV row of data
    properties = {}
    if(is_float(data['Find Lng']) and is_float(data['Find Lat'])):
        # Dump all rows not otherwise used as properties
        properties = {key: value for key, value in data.items() if key not in ['Find Lng', 'Find Lat', '\ufeff\"Mission #\"']}

        # Title is the mission number string
        title = data['\ufeff\"Mission #\"']

        # It is an error in the incident data if the mission number starts with a '#', 
        # but if it does, remove the '#' from the title
        if (title.startswith('#')):
            title = title[1:]
        properties['title'] = title

        # Marker size
        properties['marker-size'] = '1'
        properties['marker-color'] = color_outcome.get(data.get('Outcome'), '#000000') # Default to black if no match

        #determine the marker-symbol from the 'Outcome' row value, or some other property if 'Outcome' is not available
        symbol_outcome = {
            'Person Assisted': 'circle-a',
            'Life Saved': 'circle-b',
            'Deceased': 'circle-c',
            'Not Located': 'circle-u'
        }
        properties['marker-symbol'] = symbol_outcome.get(data.get('Outcome'), 'circle-u')
        properties['class'] = 'Marker'

        #folder is "Finds/" + the year of the find, which is extracted from the 'Incident Date' column
        #if 'Incident Date' in data:
        #    date = datetime.strptime(data['Incident Date'], "%Y-%m-%d %H:%M:%S").date()
        #    #properties['folder'] = 'Find/' + date.strftime("%Y")
        #    properties['folder'] = date.strftime("%Y")
        #else:                 
        #    properties['folder'] = 'Unknown Year'

        return properties

def get_ippmarker_properties(data: Dict[str, str]) -> Dict[str, str]:
    # Implementation for getting IPP marker properties from a CSV row of data
    properties = {}
    # Title is the mission number + ' IPP'
    # It is an error in the incident data if the mission number starts with a '#', 
    # but if it does, remove the '#' from the title
    title = data['\ufeff\"Mission #\"']
    if (title.startswith('#')):
            title = title[1:]
    space_index = title.find(' ')
    if (space_index != -1):
        properties['title'] = title[:space_index] + ' IPP'
    else:
        properties['title'] = title + ' IPP'

    # Marker size
    properties['marker-size'] = '1'
    properties['marker-color'] = color_outcome.get(data.get('Outcome'), '#000000') # Default to black if no match
    properties['marker-symbol'] = 'point'
    properties['class'] = 'Marker'

    return properties
    
def get_line_properties(data: Dict[str, str]) -> Dict[str, str]:
    # Implementation for getting line properties from a CSV row of data
    properties = {}
    # Title is the mission number
    # It is an error in the incident data if the mission number starts with a '#', 
    # but if it does, remove the '#' from the title
    title = data['\ufeff\"Mission #\"']
    if (title.startswith('#')):
        title = title[1:]
    space_index = title.find(' ')
    if (space_index != -1):
        properties['title'] = title[:space_index]
    else:
        properties['title'] = title
    properties['stroke'] = color_outcome.get(data.get('Outcome'), '#000000') # Default to black if no match
    properties['stroke-opacity'] = 1
    properties['stroke-width'] = 2
    properties['pattern'] = 'M-5 8 L0 -2 L5 8 Z,100%,,T' # Line with arrow
    properties['class'] = 'Shape'

    return properties
    
def convert_csv_to_geojson(csv_file_path, geojson_file_path=None):
    """
    Convert a CSV file to GeoJSON format.
    
    Args:
        csv_file_path: Path to the input CSV file
        geojson_file_path: Path to save the output GeoJSON file (optional)
    
    Returns:
        GeoJSON object as a dictionary
    """
    features = []
    
    with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:

            # For rows with valid find location coordinates, create a GeoJSON feature for the 
            # find marker and add it to the features list, as well as possibly the 
            # IPP marker and line connecting the IPP marker to the find marker 
            # if the IPP coordinates are valid
            if(is_float(row['Find Lng']) and is_float(row['Find Lat'])):

                # Get properties for the find marker from the CSV row and add it 
                # to the features list
                find_properties = get_findmarker_properties(row)

                find_feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(row['Find Lng']), float(row['Find Lat'])]
                    },
                    "properties": find_properties
                }
                features.append(find_feature)

                # Get properties for the IPP marker fromt the CSV row and add the IPP marker 
                # and line connecting the IPP marker to the find marker
                if(is_float(row['IPP Lng']) and is_float(row['IPP Lat'])):
                    ipp_properties = get_ippmarker_properties(row)
                    ipp_feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [float(row['IPP Lng']), float(row['IPP Lat'])]
                        },
                        "properties": ipp_properties                    }
                    features.append(ipp_feature)

                    # Add line feature connecting IPP to find location
                    line_properties = get_line_properties(row)
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
    result = convert_csv_to_geojson(args.input, args.output)
    print(json.dumps(result, indent=2))