# -*- coding: utf-8 -*-
"""
/***************************************************************************
 # Geocode Sqlite table
                                 A QGIS plugin
 This plugin helps geocoding an sqlite table using OSM Nominatim
                             -------------------
        begin                : 2018-11-12
        copyright            : (C) 2018 by Mátyás Gede
        email                : saman@map.elte.hu
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load GeocodeSqlite class from file geocode_sqlite.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .geocode_sqlite import GeocodeSqlite
    return GeocodeSqlite(iface)
