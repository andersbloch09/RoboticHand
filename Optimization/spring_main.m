clc; clear; close all


%% spring A

p1A = [-45*10^-3; 8*10^-3];

lA = 14*10^-3;

lsA = 27.2*10^-3;

kA = 0.06*1000;

T_s_A = 4.26;

ROMdeg = 87;

angleA = 170;

KA = spring_model(p1A, lA, lsA, kA, ROMdeg, T_s_A, angleA);

%% spring B

p1B = [-50*10^-3; 13*10^-3];

lB = 14*10^-3;

lsB = 30.4*10^-3;

kB = 0.15*1000;

T_s_B = 6.5;

ROMdegB = 110;

angleB = 165;

KB = spring_model(p1B, lB, lsB, kB, ROMdegB, T_s_B, angleB);

%% spring C

p1C = [-36*10^-3; 10*10^-3];

lC = 14*10^-3;

lsC = 22.1*10^-3;

kC = 0.49*1000;

T_s_C = 10.7;

ROMdeg = 60;

angleC = 160;

KC = spring_model(p1C, lC, lsC, kC, ROMdeg, T_s_C, angleC);