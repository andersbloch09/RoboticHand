clc; clear; close all

%%% design variables
l_pp = 45*10^-3;
l_mp = 20*10^-3;
l_dp = 25*10^-3;

kA = 0.01; % Nm/rad 0.1
kB = 0.04; % Nm/rad 0.1
kC = 0.08; 

T = 2; % N

r=7.5*10^-3;

[thetaA, thetaB, thetaC] = hand_model_pulley(r,r,r,kA,kB,kC, T);


hold on
plot([0 l_pp*cos(thetaA), l_pp*cos(thetaA) + l_mp*cos(thetaA + thetaB), l_pp*cos(thetaA) + l_mp*cos(thetaA + thetaB) + l_dp*cos(thetaA + thetaB + thetaC)],[0, l_pp*sin(thetaA), l_pp*sin(thetaA) + l_mp*sin(thetaA + thetaB), l_pp*sin(thetaA) + l_mp*sin(thetaA + thetaB) + l_dp*sin(thetaA + thetaB + thetaC)])
scatter([0 l_pp*cos(thetaA), l_pp*cos(thetaA) + l_mp*cos(thetaA + thetaB), l_pp*cos(thetaA) + l_mp*cos(thetaA + thetaB) + l_dp*cos(thetaA + thetaB + thetaC)],[0, l_pp*sin(thetaA), l_pp*sin(thetaA) + l_mp*sin(thetaA + thetaB), l_pp*sin(thetaA) + l_mp*sin(thetaA + thetaB) + l_dp*sin(thetaA + thetaB + thetaC)])
axis equal
