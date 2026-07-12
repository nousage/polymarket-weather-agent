"""Ensemble weather model normalization."""
from __future__ import annotations

@staticmethod
def ensemble_forecast(openmeteo_high: float) -> "EnsembleForecast":
    ecmwf = openmeteo_high
    icon = openmeteo_high
    ukmo = openmeteo_high
    gfs = openmeteo_high
    return EnsembleForecast(ecmwf=ecmwf, icon=icon, ukmo=ukmo, gfs=gfs)

class EnsembleForecast:
    def __init__(self, ecmwf: float, icon: float, ukmo: float, gfs: float) -> None:
        self.ecmwf = float(ecmwf)
        self.icon = float(icon)
        self.ukmo = float(ukmo)
        self.gfs = float(gfs)

    def mean(self) -> float:
        return (self.ecmwf + self.icon + self.ukmo + self.gfs) / 4.0

    def spread(self) -> float:
        vals = [self.ecmwf, self.icon, self.ukmo, self.gfs]
        return max(vals) - min(vals)
