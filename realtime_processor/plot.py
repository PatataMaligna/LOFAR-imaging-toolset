from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import cm
from matplotlib.patches import Circle
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.axes as maxes
import numpy as np
import os
from datetime import datetime

import astropy.units as u
from realtime_processor.lofarimaging import sky_imager, skycoord_to_lmn
from realtime_processor.singlestationutil import apply_calibration, get_station_xyz, get_full_station_name, freq_from_sb
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
        self.marker_sources = []
        self._setup_axes()

    def _setup_axes(self):
        self.ax.set_xlim(1, -1)
        self.ax.set_ylim(-1, 1)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_aspect('equal')
        
        ## draw exterior circle
        # circle = Circle((0, 0), 1, edgecolor='k', facecolor='none', alpha=0.7, zorder=0)
        # self.ax.add_patch(circle)
        # self.ax.add_artist(circle)

        ## elevation rings
        for el in [15, 30, 45, 60, 75]:
            radius = np.cos(np.deg2rad(el))
            ring = Circle((0, 0), radius,   
                          edgecolor='black', facecolor='none',
                          linestyle='-', alpha=0.7, zorder=1, linewidth=0.5)
            self.ax.add_patch(ring)
        
            ## labeling the rings
            theta = np.deg2rad(337)
            x, y = np.sin(theta)*radius, np.cos(theta)*radius
            self.ax.text(x, y + 0.02, f"{el}°",
                         color='black', fontsize=6,
                         ha='left', va='bottom', zorder=2)

        ## azimuth spokes every 45°
        for az in range(0, 360, 45):
            theta = np.deg2rad(az)
            x = np.sin(theta)
            y = np.cos(theta)
            ## spoke line
            self.ax.plot([0, x], [0, y],
                         linestyle='-', color='black',
                         alpha=0.7, zorder=1, linewidth=0.5)
            
            ## labeling spokes
            self.ax.text(1.1*x, 1.1*y,
                         f"{az}°",
                         ha='center', va='center',
                         color='black', fontsize=8, zorder=2)

        ## N/E/S/W
        for az, lbl in [(0,'N'), (90,'E'), (180,'S'), (270,'W')]:
            theta = np.deg2rad(az)
            x, y = np.sin(theta)*1.2, np.cos(theta)*1.2
            self.ax.text(x, y, lbl,
                         ha='center', va='center',
                         color='black', fontsize=14, zorder=2)

        self.fig.tight_layout(rect=[0, 0, 1, 0.85])
    def plot_matrix(self,
    xst_data,
    dat_path,
    subband = None,
    rcu_mode = "3",
    obstime = datetime.now(),
    sources_to_display = None,
    title = None,
    caltable_dir: str = "./test/CalTables/LV614",
    configSourcersFile = "sources.ini",
    station_name = "LV614",
    npix_l = 131,
    npix_m = 131,
    **kwargs):
    
        config = configparser.ConfigParser()
        config.read(configSourcersFile)
        
        # obsdatestr, obstimestr, *_ = os.path.basename(dat_path).rstrip(".dat").split("_")
        # time = datetime.strptime(obsdatestr + ":" + obstimestr, '%Y%m%d:%H%M%S')

        # now = datetime.now()
        # obstime = now.strftime('%Y%m%d:%H%M%S')
        # obstime = datetime.strptime(obstime, '%Y%m%d:%H%M%S')


        assert xst_data.ndim == 2, "xst_data must be a 2D array"

        freq = freq_from_sb(subband, rcu_mode)
        visibilities, calibration_info = apply_calibration(xst_data, station_name, rcu_mode, subband,
                                                       caltable_dir=caltable_dir)
        db = LofarAntennaDatabase()
        # Split into the XX and YY polarisations (RCUs)
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
            '3C48': SkyCoord(config['3C48']['ICRS_coord'], unit=(u.hourangle, u.deg)),
            'For A': SkyCoord(config['For A']['ICRS_coord'], unit=(u.hourangle, u.deg)),
            '3C123': SkyCoord(config['3C123']['ICRS_coord'], unit=(u.hourangle, u.deg)),
            '3C138': SkyCoord(config['3C138']['ICRS_coord'], unit=(u.hourangle, u.deg)),
            'Pic A': SkyCoord(config['Pic A']['ICRS_coord'], unit=(u.hourangle, u.deg)),
            'Tau A': SkyCoord(config['Tau A']['ICRS_coord'], unit=(u.hourangle, u.deg)),
            '3C147': SkyCoord(config['3C147']['ICRS_coord'], unit=(u.hourangle, u.deg)),
            '3C286': SkyCoord(config['3C286']['ICRS_coord'], unit=(u.hourangle, u.deg)),
            '3C353': SkyCoord(config['3C353']['ICRS_coord'], unit=(u.hourangle, u.deg)),
            '3C380': SkyCoord(config['3C380']['ICRS_coord'], unit=(u.hourangle, u.deg)),
            '3C444': SkyCoord(config['3C444']['ICRS_coord'], unit=(u.hourangle, u.deg)),
        }

        filtered_bodies = {}
        for k, v in marked_bodies.items():
            if k in sources_to_display:
                filtered_bodies[k] = v
        marked_bodies = filtered_bodies

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

        circle1 = Circle((0, 0), 1.0, edgecolor='k', fill=False, facecolor='none', alpha=0.3)
        self.ax.add_artist(circle1)

        if self.image is None:
            self.image = self.ax.imshow(sky_img, origin='lower', cmap=cm.Spectral_r,
                                        extent=(1, -1, -1, 1), clip_path=circle1, clip_on=True, **kwargs)
            divider = make_axes_locatable(self.ax)
            cax = divider.append_axes("right", size="5%", pad=1, axes_class=maxes.Axes)
            self.colorbar = self.fig.colorbar(self.image, cax=cax, orientation="vertical", format="%.2e")
        else:
            self.image.set_data(sky_img)
            self.image.autoscale()
        
        ##Clear markers and text from previous plot
        for artist in getattr(self, "marker_sources", []):
            artist.remove()
        self.marker_sources = []
        
        # Remove previous info text if it exists
        if hasattr(self, "info_text") and self.info_text is not None:
            self.info_text.remove()

        # Group sources 3 per line
        bodies_info_lines = [
            f"{name}: Elevation {data['elevation']:.2f}°, Azimuth {data['azimuth']:.2f}°"
            for name, data in marked_bodies_lmn.items()
        ]
        # Split into lines of 3
        grouped_lines = [
            "    ".join(bodies_info_lines[i:i+3])
            for i in range(0, len(bodies_info_lines), 3)
        ]
        bodies_info = "\n".join(grouped_lines)

        subtitle_text = (f"({freq / 1e6:.1f} MHz), {str(obstime)}\n" + bodies_info)

        self.fig.suptitle(f"Sky image for {station_name}", fontsize=16)
        self.info_text = self.fig.text(
            0.5, 0.94, subtitle_text,
            ha='center', va='top',
            fontsize=8,
            color='black'
        )
        
        if marked_bodies_lmn:
            for body_name, data in marked_bodies_lmn.items():
                lmn = data['lmn']
                marker, = self.ax.plot([lmn[0]], [lmn[1]], marker='x', color='black', mew=0.5)
                label = self.ax.text(lmn[0], lmn[1], body_name, color='black',
                            fontsize=9, ha='left', va='bottom', zorder=2)
                
                self.marker_sources.extend([marker, label])
        
        # self.draw()


        fname = f"{obstime:%Y%m%d}_{obstime:%H%M%S}_{station_name}"
        today_date = datetime.today().strftime('%Y-%m-%d')
        output_dir = os.path.join(os.path.dirname(dat_path), f"{today_date}_realtime_observation")

        self.fig.savefig(os.path.join(output_dir, f'{fname}_sky_calibrated_{freq / 1e6:.1f}MHz.png'), bbox_inches='tight', dpi=100)
