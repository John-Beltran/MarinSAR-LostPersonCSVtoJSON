# LostPersonCSVtoGeoJSON.py

This script converts a CSV file of lost-person observations into a GeoJSON FeatureCollection suitable for mapping and geospatial analysis.

## Usage

Run the script from a terminal with Python:

```bash
python LostPersonCSVtoGeoJSON.py --input <input.csv> --output <output.geojson>
```

### Required arguments

- `-i INPUT, --input INPUT`: Path to the source CSV file.
- `-o OUTPUT, --output OUTPUT`: Path where the generated GeoJSON should be written.

### Optional arguments
The supported options are:

- `-h, --help`: Show this help message and exit
- `--no-ipps` : Do not include IPP markers or lines in the output GeoJSON
- `--outcome-symbols OUTCOME_SYMBOLS` : Comma separated list of keywords and corresponding marker symbols to use for outcomes, in the format "keyword1:symbol1,keyword2:symbol2,...". If not provided, default symbols will be used for each outcome. Allowed keywords are [Deceased, Life Saved, Person Assisted, Not Located]
- `--outcome-colors OUTCOME_COLORS` : Comma separated list of keywords and corresponding marker colors to use for outcomes, in the format "keyword1:#RRGGBB,keyword2:#RRGGBB,...". If not provided, default colors will be used for each outcome. Allowed keywords are [Deceased, Life Saved, Person Assisted, Not Located]
- `--outcome-circle-radius OUTCOME_CIRCLE_RADIUS` : Radius in feet to use for circles around outcome markers. Default is 100 feet. Set to 0 to not include outcome circles.
- `--outcome-circle-segments OUTCOME_CIRCLE_SEGMENTS` : Number of segments to use for the circles around outcome markers. Default is 36.
- `--print-json` : Print the resulting GeoJSON to the console after conversion
- `--outcome-folder OUTCOME_FOLDER` : Name of the folder to put outcome markers in. Default is "Finds".
- `--ipp-folder IPP_FOLDER` : Name of the folder to put IPP markers and lines in. Default is "IPPs".

### Default colors and markers 

| Outcome | Marker | Color |
| ------- | ------ | ----- |
| Deceased | C | <span style="color:red">Red (#FF0000)</span> |
| Life Saved | B | <span style="color:blue">Blue (#0000FF)</span> |
| Person Assisted | A | <span style="color:green">Green (#00FF00)</span> |
| Not Located | U | Black (#000000)|

### Example

```bash
python LostPersonCSVtoGeoJSON.py \
  --input data/lost_persons.csv \
  --output data/lost_persons.geojson \

```

## Input expectations

The CSV should contain one row per mission and include the following columns:

- `Mission #`: mission number, used for naming features
- `IPP Lat`: initial planning point latitude
- `IPP Lng`: initial planning point longitude
- `Find Lat`: find latitude
- `Find Lng`: find longitude
- `Outcome`: mission outcome

The script assumes that latitude and longitude values are valid geographic coordinates in decimal degrees.

## Output

The script writes a GeoJSON FeatureCollection containing:
- A folder named "Finds" containing a geolocated point for each mission with a find coordinate. 
- A folder named "IPPs" containing a geolocated point for each mission with an IPP coordinate, and a line connecting the IPP point to the corresponding find point. This folder also contains a "find radius" circle co-located with the find coordinate. 
- "Find" markers at each non-empty find coordinate labeled using the Mission ID, holding custom properties created from each of the other columns in the imported CSV data
- "IPP" markers at each non-empty IPP coordinate labeled using the Mission ID
- Lines with arrows connecting each IPP marker to the corresponding find marker
- Geometry and markers are color coded based on the "Outcome" field for each row



Example:

```json
{
  "type": "FeatureCollection",
  "features": [
    // Find folder
    {
      "geometry": null,
      "type": "Feature",
      "properties": {
        "title": "Finds",
        "class": "Folder",
        "labelVisible": true,
        "visible": true
      },
      "id": "52c237cf-888b-4254-9f60-64c17387abf6"
    },
    // IPP folder
    {
      "geometry": null,
      "type": "Feature",
      "properties": {
        "title": "IPPs",
        "class": "Folder",
        "labelVisible": false,
        "visible": false
      },
      "id": "7473bdc6-2af7-49ec-a36b-0fcb4977cc1f"
    },
    // Find marker and imported properties
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [
          -122.58642527484,
          39.071904981858
        ]
      },
      "properties": {
        "Incident Date": "2013-05-15 05:00:00",
        "Incident Type": "Search",
        "Find Feature": "Lake/Pond/Water",
        "Outcome": "Deceased",
        "IPP Coordinates": "38.930487355489,-122.62872666116",
        "IPP Lat": "38.9304873554890000",
        "IPP Lng": "-122.6287266611600000",
        "Find Coordinates": "38.931203026268,-122.62988805766",
        "Comment": "",
        "title": "13-15-3 Day 3 ",
        "folderId": "52c237cf-888b-4254-9f60-64c17387abf6"
      }
    },
    // Tessellated find circle colocated with find marker
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [
            -122.62988805766,
            38.931477139493495
          ],
          // [ ... other points omitted ...]
          [
            -122.62988805766,
            38.931477139493495
          ]
        ]
      },
      "properties": {
        "title": "13-15-3 100ft",
        "stroke-opacity": 1,
        "stroke-width": 2,
        "class": "Shape",
        "folderId": "7473bdc6-2af7-49ec-a36b-0fcb4977cc1f",
        "stroke": "#FF0000"
      }
    },
    // IPP marker
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [
          -122.62872666116,
          38.930487355489
        ]
      },
      "properties": {
        "title": "13-15-3 IPP",
        "marker-size": "1",
        "marker-symbol": "point",
        "class": "Marker",
        "folderId": "7473bdc6-2af7-49ec-a36b-0fcb4977cc1f",
      }
    },
    // Line connecting IPP and find markers
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [
            -122.62872666116,
            38.930487355489
          ],
          [
            -122.62988805766,
            38.931203026268
          ]
        ]
      },
      "properties": {
        "title": "13-15-3",
        "stroke-opacity": 1,
        "stroke-width": 2,
        "pattern": "M-5 8 L0 -2 L5 8 Z,100%,,T",
        "class": "Shape",
        "folderId": "7473bdc6-2af7-49ec-a36b-0fcb4977cc1f",
      }
    },
  ]
}
```

## Limitations and caveats

- The script is designed to take "Lost Person Behavior Data" exported from a D4H incidents (http://www.d4h.com) as input, and produce a GeoJSON file suitable for import by CalTopo map (http://www.caltopo.com).
- The script is designed for point-based data. It does not create line or polygon geometries from sequences of records unless additional logic is added.
- Missing, null, malformed, or out-of-range coordinates may be skipped or cause conversion errors.
- Field (column) names and values are preserved as strings unless additional type conversion is implemented. Dates, integers, and booleans may need cleanup before downstream analysis.
- CSV parsing is sensitive to delimiter, quoting, and encoding differences. If the source file is not formatted consistently, rows may be misread.