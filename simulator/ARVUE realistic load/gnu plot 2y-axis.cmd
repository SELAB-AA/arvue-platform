set terminal postscript color lw 1.5
set output "figures.ps"
set style data linespoints
#set grid
unset key
NX=1; NY=4
DX=0.08; DY=0.01; SX=0.8; SY=0.3

set bmargin DX; set tmargin DX; set lmargin DY; set rmargin DY
set size SX*NX+DX*1.5,SY*NY+DY*1.8
set multiplot

set ytics nomirror
set size SX,SY
set origin DX,DY;
set xlabel "time (hours)" offset 0,0.5
set ylabel "sessions" offset 2.5,0
set xrange[0:22980/3600]
set yrange [0:1590]
set ytics 0, 200

set y2label "servers" offset -1,0
set y2range [0:31.90]
set y2tics 0, 3
set key 

plot "sim-report.dat" using ($1/3600):2 with lines title "sessions" axis x1y1, \
     "sim-report.dat" using ($1/3600):4 with lines title "servers" axis x1y2 lc 3

unset xlabel
unset ylabel
unset yrange

unset y2label
unset y2range
unset ytics
unset y2tics

unset xtics
unset xlabel
set origin DX,DY+SY;
set ylabel "load average" offset 2,0
set yrange[0:1.49]
set ytics 0, 0.2

set y2label "response time (ms)" offset -1.5,0
set y2range [0:149]
set y2tics 0, 20


plot "sim-report.dat" using ($1/3600):5 with lines title "load average", 1.0 lc 4 axis x1y1, \
     "sim-report.dat" using ($1/3600):3 with lines title "response time (ms)" axis x1y2

unset xlabel
unset ylabel
unset yrange
unset ytics

unset y2label
unset y2range
unset y2tics

set origin DX,DY+2*SY;
set ylabel "memory utilization" offset 2,0
set yrange[0:1.49]
set ytics 0, 0.2

set y2label "apps. per server" offset -1.5,0
set y2range [0:149]
set y2tics 0, 20

plot "sim-report.dat" using ($1/3600):6 with lines title "memory utilization", 1.0 lc 4 axis x1y1, \
     "sim-report.dat" using ($1/3600):7 with lines title "apps. per server" axis x1y2

unset ylabel
unset yrange
unset ytics

unset y2label
unset y2range
unset y2tics


unset multiplot