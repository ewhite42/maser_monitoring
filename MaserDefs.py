from datetime import *
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation, AltAz

def sourceCheck(catline, min_separation=7, timezone='EDT'):

    # note about arguments:

    # use **min_separation** to specify how many days you want
    # between observations (default is 7 days)

    # use **timezone** to specify whether you in daylight time (EDT) 
    # or standard time (EST) -- default is EDT, but may want to change this

    # define observing location 
    gbt = EarthLocation(lat=38.433121*u.deg, lon=-79.839835*u.deg, height=807.43*u.m)

    # from catalog, read in RA and Dec
    fields = catline.split()
    ra = fields[1]
    dec = fields[2]
    coord_str = ra+' '+dec
    src = SkyCoord(coord_str, frame='icrs', unit=(u.hourangle, u.deg))

    # get current time
    now_time = datetime.now()

    # add conversion from UTC to Eastern Time
    if timezone == 'EDT':
        utcoffset = -4*u.hour  # Eastern Daylight Time
    elif timezone == 'EST':
        utcoffset = -5*u.hour # Eastern Standard Time

    t = Time(now_time, scale='utc') - utcoffset
    frame = AltAz(obstime=t, location=gbt) 

    # determine source elevation
    src_azel = src.transform_to(frame) 
    src_el = src_azel.alt.deg

    if src_el > 30.0:

        # check when source was last observed
        timestamp = fields[5]

        # set minimum separation between observations
        min_time_delta = timedelta(days = min_separation)

        # if timestamp = 0, the source hasn't been observed
        if int(timestamp) == 0:
            return 1
        else:
            ts_string = datetime.strptime(timestamp, "%d/%m/%Y %H:%M:%S")
            time_cutoff = now_time - min_time_delta

            # if source has been observed, make sure it was not observed too recently:
            if ts_string < time_cutoff:
                return 1
    return 0

def sourceSearch(catname):
    infile = open(catname, 'r')
    filetext = infile.readlines()   
    newlines = []

    for line in filetext[4:]:
        if line.strip() != '':
            fields = line.split()
            ready = sourceCheck(line)
            if ready:
                print(fields[0]+" is ready to be observed.")
                return(fields[0])
            else:
                continue
        else:
            continue

def main():
    sourceSearch("MMBGroup1_rev.cat")

if __name__ == '__main__':
    main()
