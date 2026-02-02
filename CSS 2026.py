# -*- coding: utf-8 -*-
"""
Created on Sun Feb  1 16:27:31 2026

@author: Ntando Mtshali
"""

import ee
import geemap
import matplotlib.pyplot as plt

# Initialize Earth Engine
ee.Initialize()

# Define the area of interest (Drakensberg Mountains, South Africa)
drakensberg = ee.Geometry.Polygon(
    [[[28.6, -29.7], [29.6, -29.7], [29.6, -28.7], [28.6, -28.7]]
)

# Load SRTM elevation data and clip to the Drakensberg region
srtm = ee.Image('USGS/SRTMGL1_003').clip(drakensberg)

# Calculate the Terrain Ruggedness Index (TRI)
tri = srtm.unitScale(0, 3000) \
    .focal_mean(radius=3, units='pixels') \
    .subtract(srtm) \
    .abs() \
    .rename('TRI') \
    .clip(drakensberg)

# Load Sentinel-2 surface reflectance data (Harmonized) and calculate NDVI
sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
    .filterBounds(drakensberg) \
    .filterDate('2023-01-01', '2023-12-31') \
    .median() \
    .clip(drakensberg)

ndvi = sentinel2.normalizedDifference(['B8', 'B4']).rename('NDVI')

# Load ESA WorldCover land cover data and clip to the Drakensberg region
landCover = ee.Image('ESA/WorldCover/v100/2020').clip(drakensberg)

# Visualize the datasets
Map = geemap.Map()
Map.centerObject(drakensberg, 10)
Map.addLayer(tri, {'min': 0, 'max': 1, 'palette': ['white', 'green', 'brown']}, 'Terrain Ruggedness Index (TRI)')
Map.addLayer(ndvi, {'min': 0, 'max': 1, 'palette': ['white', 'green']}, 'NDVI (Sentinel-2)')
Map.addLayer(landCover, {'min': 10, 'max': 100, 'palette': ['006400', 'ffbb22', 'ffff4c', 'f096ff', 'fa0000', 'b4b4b4', 'f0f0f0']}, 'Land Cover (ESA WorldCover)')

# Time series analysis for temperature and surface pressure over the past 10 years, by season
startDate = '2013-01-01'
endDate = '2023-12-31'

# Load ERA5 climate data for temperature and pressure
era5 = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY') \
    .filterDate(startDate, endDate) \
    .filterBounds(drakensberg)

# Function to calculate seasonal mean
def seasonalMean(collection, season):
    return collection.filter(ee.Filter.calendarRange(season[0], season[1], 'month')) \
        .mean() \
        .set('season', season[2])

# Define seasons
seasons = [
    [12, 2, 'DJF'],  # December-January-February
    [3, 5, 'MAM'],   # March-April-May
    [6, 8, 'JJA'],   # June-July-August
    [9, 11, 'SON']   # September-October-November
]

# Apply seasonal calculation to temperature and pressure
seasonalTemp = [seasonalMean(era5.select('temperature_2m'), season).set('system:time_start', ee.Date.fromYMD(2023, season[0], 1).millis()) for season in seasons]
seasonalPressure = [seasonalMean(era5.select('surface_pressure'), season).set('system:time_start', ee.Date.fromYMD(2023, season[0], 1).millis()) for season in seasons]

# Convert seasonal images to image collections
seasonalTempCollection = ee.ImageCollection.fromImages(seasonalTemp)
seasonalPressureCollection = ee.ImageCollection.fromImages(seasonalPressure)

# Generate a seasonal time series chart for temperature
tempChart = seasonalTempCollection.getRegion(drakensberg, 10000).getInfo()
pressureChart = seasonalPressureCollection.getRegion(drakensberg, 10000).getInfo()

# Plot the charts
plt.figure(figsize=(10, 6))
plt.plot([x[0] for x in tempChart[1:]], [x[1] for x in tempChart[1:]], label='Temperature (K)')
plt.title('Seasonal Mean 2m Air Temperature Over Drakensberg (2013-2023)')
plt.xlabel('Season')
plt.ylabel('Temperature (K)')
plt.legend()
plt.show()

plt.figure(figsize=(10, 6))
plt.plot([x[0] for x in pressureChart[1:]], [x[1] for x in pressureChart[1:]], label='Pressure (Pa)')
plt.title('Seasonal Mean Surface Pressure Over Drakensberg (2013-2023)')
plt.xlabel('Season')
plt.ylabel('Pressure (Pa)')
plt.legend()
plt.show()

Map