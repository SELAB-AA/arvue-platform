set terminal postscript color lw 1.5
set output "figures.ps"
set style data linespoints
#set grid
unset key
NX=1; NY=4
DX=0.08; DY=0.01; SX=0.8; SY=0.25

set bmargin DX; set tmargin DX; set lmargin DY; set rmargin DY
set size SX*NX+DX*1.5,SY*NY+DY*1.8
set multiplot

set ytics nomirror
set size SX,SY
set origin DX,DY;
set xlabel "time (hours)" offset 0,0.5
set ylabel "sessions" offset 2,0
set xrange[0:25530/3600]
set xtics 0, 1
set yrange [0:1390]
set ytics 0, 200

set y2label "servers" offset -1,0
set y2range [0:31.9]
set y2tics 0, 4
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
set origin DX,DY+2*SY;
set ylabel "load average" offset 2,0
set yrange[0:1.69]
set ytics 0, 0.3

set y2label "memory" offset -1.5,0
set y2range[0:1.69]
set y2tics 0, 0.3


plot "sim-report.dat" using ($1/3600):5 with lines title "CPU load average", 1.0 lc 4 axis x1y1, \
     "sim-report.dat" using ($1/3600):6 with lines title "memory utilization" axis x1y2

unset xlabel
unset ylabel
unset yrange
unset ytics

unset y2label
unset y2range
unset y2tics

set origin DX,DY+SY;
set ylabel "overloaded servers" offset 2,0
set yrange [0:27.8]
set ytics 0, 4

set y2label "response time (ms)" offset -1.5,0
set y2range[0:834]
set y2tics 0, 120


plot "sim-report.dat" using ($1/3600):10 smooth csplines with lines title "overloaded servers" axis x1y1, \
     "sim-report.dat" using ($1/3600):($3*1000) smooth csplines with lines title "response time (ms)" axis x1y2 lc 3
     

unset ylabel
unset yrange
unset ytics

unset y2label
unset y2range
unset y2tics




set origin DX,DY+3*SY;
set ylabel "weighted load average" offset 2,0
set yrange[0:1.69]
set ytics 0, 0.3

set y2label "weighted memory" offset -1.5,0
set y2range [0:1.69]
set y2tics 0, 0.3

plot "sim-report.dat" using ($1/3600):14 with lines title "weighted CPU load average", 1.0 lc 4 axis x1y1, \
     "sim-report.dat" using ($1/3600):15 with lines title "weighted memory utilization" axis x1y2

unset ylabel
unset yrange
unset ytics

unset y2label
unset y2range
unset y2tics

unset multiplot