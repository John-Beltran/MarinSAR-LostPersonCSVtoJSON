import argparse
import csv
from datetime import datetime
import json

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
            if(is_float(row['Find Lng']) and is_float(row['Find Lat'])):
                # Dump all rows not otherwise used as properties
                properties = {key: value for key, value in row.items() if key not in ['Find Lng', 'Find Lat', '\ufeff\"Mission #\"']}

                # Title is the mission number string. Strip any leading '#' character if it exists, 
                # since that is used in some of the data but not all.
                properties['title'] = row['\ufeff\"Mission #\"']
                if properties['title'].startswith('#'):
                    properties['title'] = properties['title'][1:]

                # Marker size
                properties['marker-size'] = '1'

                # note that some fields, like outcome, ages, etc., can be comma-delimited lists if the number of subjects > 1,
                # so we will just take the worst-case outcome for color and symbol.                
                # determine the marker-color from the 'Outcome' row value, or some other property if 'Outcome' is not available
                # determine the marker-symbol from the 'Outcome' row value, or some other property if 'Outcome' is not available

                if row.get('Outcome').find('Deceased') != -1:
                    properties['marker-color'] = '#FF0000'
                    properties['marker-symbol'] = 'circle-c'
                elif row.get('Outcome').find('Life Saved') != -1:
                        properties['marker-color'] = '#0000FF'
                        properties['marker-symbol'] = 'circle-b'
                elif row.get('Outcome').find('Person Assisted') != -1:
                    properties['marker-color'] = '#00FF00'
                    properties['marker-symbol'] = 'circle-a'
                else:
                    properties['marker-color'] = '#000000'
                    properties['marker-symbol'] = 'circle-u'    

                # TBD - This doesn't create folders on import, needs more work
                #folder is "Finds/" + the year of the find, which is extracted from the 'Incident Date' column
                #if 'Incident Date' in row:
                #    date = datetime.strptime(row['Incident Date'], "%Y-%m-%d %H:%M:%S").date()
                #    #properties['folder'] = 'Find/' + date.strftime("%Y")
                #    properties['folder'] = date.strftime("%Y")
                #else:                 
                #    properties['folder'] = 'Unknown Year'

                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(row['Find Lng']), float(row['Find Lat'])]
                    },
                    "properties": properties
                }
                features.append(feature)
    
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