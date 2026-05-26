clc; clear; close all


%%% design variables
l_pp = 45*10^-3;
l_mp = 20*10^-3;
l_dp = 25*10^-3;

kA = 1; % Nm/rad
kB = 0.6; % Nm/rad
kC = 0.3;

T = 10; % N

%%% finger functions
syms thetaPIP

thetaDIP = 0.7*thetaPIP;



%%% simulating
[thetaA, thetaB, thetaC, F_tip] = hand_model(l_pp, l_mp, l_dp, kA, kB, kC, T);


hold on
plot([0 l_pp*cos(thetaA), l_pp*cos(thetaA) + l_mp*cos(thetaA + thetaB), l_pp*cos(thetaA) + l_mp*cos(thetaA + thetaB) + l_dp*cos(thetaA + thetaB + thetaC)],[0, l_pp*sin(thetaA), l_pp*sin(thetaA) + l_mp*sin(thetaA + thetaB), l_pp*sin(thetaA) + l_mp*sin(thetaA + thetaB) + l_dp*sin(thetaA + thetaB + thetaC)])
scatter([0 l_pp*cos(thetaA), l_pp*cos(thetaA) + l_mp*cos(thetaA + thetaB), l_pp*cos(thetaA) + l_mp*cos(thetaA + thetaB) + l_dp*cos(thetaA + thetaB + thetaC)],[0, l_pp*sin(thetaA), l_pp*sin(thetaA) + l_mp*sin(thetaA + thetaB), l_pp*sin(thetaA) + l_mp*sin(thetaA + thetaB) + l_dp*sin(thetaA + thetaB + thetaC)])
axis equal