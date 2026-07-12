"""Atmospheric bias correction for raw model outputs."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AtmosphericCorrection:
    city: str
    corrected_temperature: float
    icon: float
    ukmo: float
    gfs: float
    wind_correction: float
    dew_correction: float
    cloud_correction: float
    zone: str


def atmospheric_correction(
    city: str,
    raw_temp_f: float,
    ecmwf_f: float,
    cloud_avg: float,
    wind_speed: float,
    dew_avg: float,
) -> AtmosphericCorrection:
    wind_corr = 0.0
    dew_corr = 0.0
    cloud_corr = 0.0
    if cloud_avg >= 90:
        cloud_corr = min(cloud_avg / 100.0 * 3.5, 3.5)
    wind_corr = min(wind_speed / 25.0, 1.0)
    corrected = raw_temp_f - cloud_corr - wind_corr + dew_corr * 0.1
    zone = "normal"
    if corrected >= 95:
        zone = "danger"
    elif corrected >= 85:
        zone = "warning"
    return AtmosphericCorrection(
        city=city,
        corrected_temperature=corrected,
        icon=ecmwf_f,
        ukmo=ecmwf_f,
        gfs=ecmwf_f,
        wind_correction=wind_corr,
        dew_correction=dew_corr,
        cloud_correction=cloud_corr,
        zone=zone,
    )
