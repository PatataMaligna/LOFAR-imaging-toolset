rcumode=3
duration=$1  # observation duration in seconds
RCUS=$2

today="`date +"%Y.%m.%d"`"
start_time="`date +"%H%M%S"`"
datapath='/mnt/LOFAR0/erasmus_2025/'$today'_'$start_time


echo $datapath
mkdir $datapath

cp erasmus.sh $datapath


rspctl --mode=3 select=$RCUS
sleep 10

rspctl --bitmode=8
sleep 10

antennaset='LBA_INNER'
subbands='51:461'
band='10_90'

CASA="6.123487680622105,1.0265153995604648,J2000"



rspctl --xcsubband=167


nohup beamctl --antennaset='LBA_INNER' --rcus=$RCUS --band=$band --subbands=$subbands --beamlets=0:410 --anadir=$CASA --digdir=$CASA > $datapath/beamctl_1.log 2>&1 &

sleep 10

nohup  rspctl --xcstatistics --integration=1 --directory=$datapath  --duration=$duration > $datapath/rspctl_beamlet.log  2>&1 &

sleep $duration

killall beamctl # kill any existing beams

echo 'Stop recording'