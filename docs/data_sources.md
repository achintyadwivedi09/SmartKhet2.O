# SmartKhet 2.0: Authentic Data Sources & Provenance Registry

SmartKhet 2.0 strictly adheres to scientific data integrity. Below are the official documentation, licensing, variables, and download methodologies for the primary datasets utilized.

---

## 1. Primary Source A: IMD Gridded Daily Rainfall
* **Official Publisher:** India Meteorological Department (IMD), Ministry of Earth Sciences, Pune.
* **Official Source URL:** https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html
* **Spatial Resolution:** 0.25° × 0.25° (~27 km × 27 km grid cells).
* **Temporal Coverage:** 1901–2024 (Daily resolution).
* **Primary Variable:** `rainfall` (Daily total precipitation in millimeters).
* **Format:** NetCDF-4 (`.nc`).
* **License:** Government of India Open Data License / IMD Data Policy.
* **Access Protocol:** Direct registration and NetCDF download through IMD Pune portal.
* **Demonstration Grid Cells Selected:**
  - Thanjavur: Grid center (10.75°N, 79.25°E)
  - Coimbatore: Grid center (11.00°N, 77.00°E)
  - Madurai: Grid center (10.00°N, 78.00°E)

---

## 2. Primary Source B: ISRO MOSDAC Soil Moisture & Wetness
* **Official Publisher:** Space Applications Centre (SAC), Indian Space Research Organisation (ISRO).
* **Official Source URL:** https://www.mosdac.gov.in/soil-moisture-0
* **Sensor / Product:** SMAP-derived Soil Wetness Index and CYGNSS Soil Moisture Products.
* **Spatial Resolution:** 25 km grid composite.
* **Temporal Coverage:** 2015–Present.
* **Primary Variables:**
  - `soil_moisture_index`: Dimensionless normalized index [0.0, 1.0].
  - `soil_wetness_index`: Root-zone wetness proxy.
* **Format:** NetCDF / HDF5 / GeoTIFF.
* **License:** SAC/ISRO Open Access Scientific Data Policy.
* **Access Protocol:** Free registration at MOSDAC portal; authenticated HTTPS/FTP download.

---

## 3. Primary Source C: SMAP Assimilated ILDAS Reference
* **Scientific Reference:** *SMAP Assimilated Soil Moisture Over India*, Journal of Hydrology (2024).
* **DOI:** https://doi.org/10.1016/j.jhydrol.2024.131581
* **Coverage:** Pan-India high-resolution land surface data assimilation.
* **Variables:** Volumetric soil moisture (0–5 cm topsoil and 0–100 cm root-zone in m³/m³).

---

## 4. Primary Source D: Copernicus ERA5-Land Reanalysis
* **Official Publisher:** European Centre for Medium-Range Weather Forecasts (ECMWF) / Copernicus Climate Change Service (C3S).
* **Official Source URL:** https://cds.climate.copernicus.eu/
* **DOI:** 10.24381/cds.e2161bac
* **Spatial Resolution:** 0.1° × 0.1° (~9 km grid).
* **Temporal Coverage:** 1950–Present (Hourly aggregated to Daily).
* **Primary Variables:**
  - `2m_temperature` (Kelvin → Converted to Celsius).
  - `2m_dewpoint_temperature` (Kelvin → Converted to Celsius).
* **Derived Variable (Magnus Clausius-Clapeyron Formula):**
  $$\text{RH} = 100 \times \frac{\exp\left(\frac{17.625 \cdot T_d}{243.04 + T_d}\right)}{\exp\left(\frac{17.625 \cdot T}{243.04 + T}\right)}$$
  Where $T$ is air temperature in °C and $T_d$ is dewpoint temperature in °C.
* **License:** Copernicus Open Access License v1.2.

---

## 5. Supplementary Source E: Kaggle Indian Agricultural Weather
* **Publisher / Host:** Kaggle Community (Aggregated from IMD & Agricultural State Portals).
* **License:** CC0 Public Domain.
* **Use:** Supplementary historical validation for localized station trends.

