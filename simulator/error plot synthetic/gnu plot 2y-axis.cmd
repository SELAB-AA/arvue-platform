set terminal postscript color lw 1.5

#terminal=pdf,terminaloptions=enhanced

set output "error-figures.ps"

#set style data linespoints

#set grid
#unset key
#NX=1; NY=4
#DX=0.08; DY=0.01; SX=0.8; SY=0.5

#set bmargin DX; set tmargin DX; set lmargin DY; set rmargin DY
#set size SX*NX+DX*1.5,SY*NY+DY*1.8
#set multiplot

#set ytics nomirror
#set size SX,SY
#set origin DX,DY;

set xlabel "time (hours)" offset 0,0.5

#set ylabel "sessions" offset 2.5,0

set xrange[0:31600/3600]

set yrange[0:1]

#set yrange [0:1590]
#set ytics 0, 0.1

#set key 

plot "alternative-report.dat" using ($1/3600):(abs(0.8 - $5)) with lines title "ARVUE error", \
     "cramp-report.dat" using ($1/3600):(abs(0.8 - $5)) with lines title "CRAMP error" lc 3
     

#unset xlabel
#unset ylabel
#unset yrange


#unset xtics
#unset xlabel


#unset multiplot