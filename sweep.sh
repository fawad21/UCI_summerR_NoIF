#!/usr/bin/env bash
set -euo pipefail

SUMMARY=summary.txt
echo -e "inj_rate\tavg_flit_latency_ticks\tflits_received" > $SUMMARY

# build a list of rates: 0.01,0.03,...,0.49, then finally 0.80
RATES=($(awk 'BEGIN{for(i=0.01;i<0.80;i+=0.02) printf("%.2f ",i); print "0.80"}'))

for inj in "${RATES[@]}"; do
  # e.g. for inj=0.01 → out_inj0_01 / stats_inj0_01.txt
  OUTDIR=out_inj${inj//./_}
  STATS=stats_inj${inj//./_}.txt

  echo "=== Running inj_rate=$inj ==="
  build/NULL/gem5.opt \
    --outdir=$OUTDIR \
    --stats-file=$STATS \
    configs/example/garnet_synth_traffic.py \
      --network=garnet \
      --topology=new \
      --num-cpus=80 \
      --num-dirs=64 \
      --synthetic=uniform_random \
      --injectionrate=$inj \
      --sim-cycles=100000000 \
      --vcs-per-vnet=16 \
      --link-width-bits=128 \
      --garnet-deadlock-threshold=100000000
       
  # now grep inside the outdir
  fullpath=${OUTDIR}/${STATS}
  if [[ ! -f $fullpath ]]; then
    echo "ERROR: stats file not found: $fullpath" >&2
    exit 1
  fi

  avg_latency=$(grep "^system.ruby.network.average_flit_network_latency" $fullpath \
                | awk '{print $2}')
  flits_recv=$(grep "^system.ruby.network.flits_received::total" $fullpath \
                | awk '{print $2}')

  echo -e "${inj}\t${avg_latency}\t${flits_recv}" >> $SUMMARY
done

echo "Sweep complete. Results in $SUMMARY"

