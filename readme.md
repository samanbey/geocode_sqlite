# Geocode Sqlite table

This plugin performs bulk geocoding of records in an SQLite table using OSM Nominatim.

## Usage

Select the database file, the table and the field to geocode, then press "Start".
Setting the W (west), S (south), E (east) and N (north) fields of BBOX limits the search to the given geographical quadrangle.

Depending on the number of records, processing may take several minutes. 

## Known issues

If there are multiple geocoding results, the first one is used. 
Sometimes this may lead to false geocodes.

