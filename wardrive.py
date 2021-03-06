import argparse
from recon import Recon

from auth import auth
import sys

import json
import time

import simplekml

parser = argparse.ArgumentParser(description="Wardriving software for Wifi pineapple")

parser.add_argument("-H", "--host", type=str, metavar='', help="IP of the wifi pineapple service")
parser.add_argument("-p", "--port", type=int, metavar='', help="Port of the wifi pineapple service")

parser.add_argument("-u", "--user", required=True, type=str, metavar='', help="user of wifi pineapple portal")
parser.add_argument("-P", "--password", required=True, type=str, metavar='', help="password of wifi pineapple portal")

parser.add_argument("-b", "--band", type=int, metavar='', help="Channel of recon scan")

args = parser.parse_args()

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


banner = r"""
                                           .NN,
                                .cxxdl'    xMMO    'cdxxl'
                                  .c0WMNk;,NMMW:,xXMMKo.
                                  ...:KMMMWMMMMWMMMXc...           .
                     ,        .l0NMMMNXMMMMMMMMMMMMXNMMMWKl'      xWd
                   ,0Wd         .':xNMMMMMMMMMMMMMMMMNkc'.        ;KM0'
                  lWMo            .;dNMMMMMMMMMMMMMMWx:.      .l.   dMWc
                 :WWo   oNd   .;xKWMMMMMMMMMMMMMMMMMMMMWXx:.  dWX:   dMW;
                ,NWo   oMW:   .. ..,lOXWMMMMMMMMMMWN0o;.. ..   cWMl   dMN'
               .XMx   oWN;   lc     .loooolcooclooool.    cXl   oMWc   kMK.
               oMW'  ,WMl   cMW:   lWMW0d:;cdd:;:o0WMWl   lMW:   OMW'  ,WMl
               0M0   xMX.  .XMd   .lo:.,dXMMMMMMXd,.:ol.   kMK.  'NMd   KMO
               NMd   KMk   lMN.  .;:xOxollccddcclloxOx:;.  'WM:   OM0   xMX
               WMo  .XMx   dMK   oNMMMMWOc;;ol;;cOWMMMMNo  .XMl   kMK   dMN
               NMx   0MO   :Kd. .lllcl;.:0WMMMMW0:.;lclll. .xK;   0MO   kMX
 __          ___ ______ _   _____ _  oxl:::oOOo:::lxo,;0W:       _.O   KMk
 \ \        / (_|  ____(_) |  __ (_) MMWk:.;,.;kWMMMMKc;.       | |  .OX:
  \ \  /\  / / _| |__   _  | |__) _ _ __   ___  __ _ _ __  _ __ | | ___
   \ \/  \/ / | |  __| | | |  ___| | '_ \ / _ \/ _` | '_ \| '_ \| |/ _ \
    \  /\  /  | | |    | | | |   | | | | |  __| (_| | |_) | |_) | |  __/
     \/  \/   |_|_|    |_| |_|   |_|_| |_|\___|\__,_| .__/| .__/|_|\___|
----------------------------------------------------| |-- | |-----------------
                                                    |_|   |_|  

* Rembmer to start the webserver

"""

if __name__ == "__main__":

    print(f"{colors.WARNING}{banner}{colors.ENDC}")

    host = "172.16.42.1" if args.host is None else args.host
    port = 1471 if args.port is None else args.port

    band = 2 if args.band is None else args.band

    user = args.user
    password = args.password

    url = f"http://{host}:{port}"

    authHelper = auth(user, password, url)

    status, token = authHelper.generateBearer()

    if not status:
        print(f"{colors.FAIL}[-] {token}, please recheck arguments.{colors.ENDC}")
        sys.exit()
    
    print(f"{colors.OKGREEN}[+] Authentication Successful.{colors.ENDC}")

    reconHandler = Recon(token, band, url)

    status, scanID = reconHandler.startScan()

    if not status:
        print(f"{colors.FAIL}[-] Failed Starting Scan, please recheck arguments.{colors.ENDC}")
        sys.exit()
    
    print(f"{colors.OKGREEN}[+] Scan Started Successfuly.{colors.ENDC}")

    wardriveData = {}

    while True:
        try:
            time.sleep(1)

            status, scanResults = reconHandler.newAPS(scanID)

            if status:
                f = open("location.json")

                location = json.load(f)

                f.close()

                formated = f"{location['latitude']}, {location['longitude']}"

                if formated in wardriveData:
                    for i in scanResults:
                        wardriveData[formated].append(i)
                else:
                    wardriveData[formated] = scanResults

                kml=simplekml.Kml()

                for key in wardriveData:
                    it = 0.0000001

                    for item in wardriveData[key]:
                            lat = float(key.split(", ")[0])
                            long = float(key.split(", ")[1])


                            clat = (lat) + (lat * it) / lat
                            clong = (long) + (long * it) / long

                            descp = f"bssid: {item[1]}\nchannel: {item[2]}\nSignal Strength: {item[3]}dBi\nSecurity: {item[4]}\nisHidden: {item[5]}\nWPS: {item[6]}"

                            kml.newpoint(name=item[0], description=descp, coords=[(clong,clat)])

                            it += 0.000001
                kml.save('wardriveData.kml')
        except KeyboardInterrupt as e:
            if reconHandler.stopScan():
                print(f"{colors.OKGREEN}[*] Scan Stopped Successfuly.{colors.ENDC}")
                break
            else:
                print(f"{colors.FAIL}[-] Scan Failed to Stop.{colors.ENDC}")
                sys.exit()