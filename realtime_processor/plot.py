from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import cm
from matplotlib.patches import Circle
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.axes as maxes
import numpy as np
import os
import datetime

import astropy.units as u
from lofarimaging import apply_calibration, sky_imager, get_station_xyz, skycoord_to_lmn, get_full_station_name, sb_from_freq, freq_from_sb
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, GCRS, get_sun, get_body
from astropy.time import Time
from lofarantpos.db import LofarAntennaDatabase
import configparser
class Plot(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(8, 8))
        super().__init__(self.fig)
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.image = None 
        self.colorbar = None
        self.circle = Circle((0, 0), 1.0, edgecolor='k', fill=False, facecolor='none', alpha=0.3)
        self.ax.add_artist(self.circle)
        self._setup_axes()
        self.marker_sources = []

    def _setup_axes(self):
        self.ax.set_xlim(1, -1)
        self.ax.set_xticks(np.arange(-1, 1.1, 0.5))
        self.ax.set_yticks(np.arange(-1, 1.1, 0.5))
        self.ax.set_xlabel('$ℓ$', fontsize=14)
        self.ax.set_ylabel('$m$', fontsize=14)
        self.ax.set_title("Sky Plot", fontsize=14, pad=250)

        # Cardinal directions
        self.ax.text(0.9, 0, 'E', ha='center', va='center', color='w', fontsize=17)
        self.ax.text(-0.9, 0, 'W', ha='center', va='center', color='w', fontsize=17)
        self.ax.text(0, 0.9, 'N', ha='center', va='center', color='w', fontsize=17)
        self.ax.text(0, -0.9, 'S', ha='center', va='center', color='w', fontsize=17)
        self.fig.tight_layout(rect=[0, 0, 1, 0.95])

    def plot_matrix(self,
    xst_data,
    dat_path,
    subband = None,
    rcu_mode = "3",
    title = None,
    caltable_dir: str = "./test/CalTables/LV614",
    configSourcersFile = "sources.ini",
    station_name = "LV614",
    npix_l = 130,
    npix_m = 130,
    **kwargs):
    
        config = configparser.ConfigParser()
        config.read(configSourcersFile)
        
        obsdatestr, obstimestr, *_ = os.path.basename(dat_path).rstrip(".dat").split("_")
        obstime = datetime.datetime.strptime(obsdatestr + ":" + obstimestr, '%Y%m%d:%H%M%S')

        assert xst_data.ndim == 2, "xst_data must be a 2D array"

        freq = freq_from_sb(subband, rcu_mode)
        visibilities, calibration_info = apply_calibration(xst_data, station_name, rcu_mode, subband,
                                                       caltable_dir=caltable_dir)
        db = LofarAntennaDatabase()
        # Split into the XX and YY polarisations (RCUs)
        # This needs to be modified in future for LBA sparse
        visibilities_xx = visibilities[0::2, 0::2]
        visibilities_yy = visibilities[1::2, 1::2]
        # Stokes I
        visibilities_stokes_i = visibilities_xx + visibilities_yy
        
        station_xyz, pqr_to_xyz = get_station_xyz(station_name, rcu_mode, db)

        station_name = get_full_station_name(station_name, rcu_mode)

        baselines = station_xyz[:, np.newaxis, :] - station_xyz[np.newaxis, :, :]

        sky_img = sky_imager(visibilities_stokes_i, baselines, freq, npix_l, npix_m)

        obstime_astropy = Time(obstime)
        station_earthlocation = EarthLocation.from_geocentric(*(db.phase_centres[station_name] * u.m))
        gcrs_instance = GCRS(obstime = obstime_astropy)
        zenith = AltAz(az=0 * u.deg, alt=90 * u.deg, obstime=obstime_astropy,
                    location=station_earthlocation).transform_to(gcrs_instance)
    
        marked_bodies = {
            'Cas A': SkyCoord(ra=float(config['Cas A']['RA']) * u.deg, dec=float(config['Cas A']['DEC']) * u.deg),
            'Cyg A': SkyCoord(ra=float(config['Cyg A']['RA']) * u.deg, dec=float(config['Cyg A']['DEC']) * u.deg),
            'Per A': SkyCoord(ra=float(config['Per A']['RA']) * u.deg, dec=float(config['Per A']['DEC']) * u.deg),
            'Her A': SkyCoord(ra=float(config['Her A']['RA']) * u.deg, dec=float(config['Her A']['DEC']) * u.deg),
            'Cen A': SkyCoord(ra=float(config['Cen A']['RA']) * u.deg, dec=float(config['Cen A']['DEC']) * u.deg),
            'Vir A': SkyCoord(ra=float(config['Vir A']['RA']) * u.deg, dec=float(config['Vir A']['DEC']) * u.deg),
            '3C295': SkyCoord(ra=float(config['3C295']['RA']) * u.deg, dec=float(config['3C295']['DEC']) * u.deg),
            'Moon': get_body('moon', time=obstime_astropy),
            'Sun': get_sun(time=obstime_astropy).transform_to(gcrs_instance),
            '3C196': SkyCoord(ra=float(config['3C196']['RA']) * u.deg, dec=float(config['3C196']['DEC']) * u.deg),
            # SkyCoord("23 23 26.0 +58 48 41", unit=(u.hourangle, u.deg))
            # 'J0133-3629': [1.0440, -0.662, -0.225],
            '3C48': SkyCoord(config['3C48']['ICRS_coord'], unit=(u.hourangle, u.deg)),
            'For A': SkyCoord(config['For A']['ICRS_coord'], unit=(u.hourangle, u.deg)),
            '3C123': SkyCoord(config['3C123']['ICRS_coord'], unit=(u.hourangle, u.deg)),
            # 'J0444-2809': [0.9710, -0.894, -0.118],
            '3C138': SkyCoord(config['3C138']['ICRS_coord'], unit=(u.hourangle, u.deg)),
            'Pic A': SkyCoord(config['Pic A']['ICRS_coord'], unit=(u.hourangle, u.deg)),
            'Tau A': SkyCoord(config['Tau A']['ICRS_coord'], unit=(u.hourangle, u.deg)),
            '3C147': SkyCoord(config['3C147']['ICRS_coord'], unit=(u.hourangle, u.deg)),
            # 'Hyd A': [1.7795, -0.9176, -0.084, -0.0139, 0.030],
            '3C286': SkyCoord(config['3C286']['ICRS_coord'], unit=(u.hourangle, u.deg)),
            '3C353': SkyCoord(config['3C353']['ICRS_coord'], unit=(u.hourangle, u.deg)),
            '3C380': SkyCoord(config['3C380']['ICRS_coord'], unit=(u.hourangle, u.deg)),
            '3C444': SkyCoord(config['3C444']['ICRS_coord'], unit=(u.hourangle, u.deg)),
            # 'casa': [3.3584, -0.7518, -0.035, -0.071]
        }

        marked_bodies_lmn = {}
        for body_name, body_coord in marked_bodies.items():
            # print(body_name, body_coord.separation(zenith), body_coord.transform_to(AltAz(location=station_earthlocation, obstime=obstime_astropy)).alt)
            altaz = body_coord.transform_to(AltAz(location=station_earthlocation, obstime=obstime_astropy))
            if altaz.alt > 0:
                marked_bodies_lmn[body_name] = {
                    'lmn' : skycoord_to_lmn(marked_bodies[body_name], zenith),
                    'elevation': altaz.alt.deg,
                    'azimuth': altaz.az.deg
                }

        bodies_info = "\n".join(
                [f"{name}: Elevation {data['elevation']:.2f}°, Azimuth {data['azimuth']:.2f}°"
                for name, data in marked_bodies_lmn.items()]
            )

        subtitle_text = (f"({freq / 1e6:.1f} MHz), {str(obstime)[:16]}\n" + bodies_info)

        if self.image is None:
            self.image = self.ax.imshow(sky_img, origin='lower', cmap=cm.Spectral_r,
                                        extent=(1, -1, -1, 1), clip_path=self.circle, clip_on=True, **kwargs)
            divider = make_axes_locatable(self.ax)
            cax = divider.append_axes("right", size="5%", pad=0.2, axes_class=maxes.Axes)
            self.colorbar = self.fig.colorbar(self.image, cax=cax, orientation="vertical", format="%.2e")
        else:
            self.image.set_data(sky_img)
            self.image.autoscale()

        ##Clear previous
        # self.ax.set_title("") 
        for text in self.ax.texts:
            text.remove()
        for artist in getattr(self, "marker_sources", []):
            artist.remove()
        self.marker_sources = []

        self.ax.set_title(f"Sky image for {station_name}", fontsize=14, pad=250)
        self.ax.text(0.5, 1.02, subtitle_text, transform=self.ax.transAxes,
                     ha='center', va='bottom', fontsize=11)

        if marked_bodies_lmn:
            for body_name, data in marked_bodies_lmn.items():
                lmn = data['lmn']
                marker, = self.ax.plot([lmn[0]], [lmn[1]], marker='x', color='black', mew=0.5)
                self.marker_sources.append(marker)
                self.ax.annotate(body_name, (lmn[0], lmn[1]))

        self.draw()
