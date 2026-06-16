l_pp = 45*10^-3;
l_mp = 20*10^-3;
l_dp = 25*10^-3;

kA = 1000000; % Nm/rad
kB = 1000000; % Nm/rad
kC = 0.1;

T = 0.1; % N

kA = [fit(1) fit(2) fit(3) fit(4)];

kB = kA;

kC = kA;

[thetaA, thetaB, thetaC, F_tip] = hand_model_3rd(l_pp,l_mp, l_dp,kA(1), kA(2), kA(3), kA(4), kB(1), kB(2), kB(3), kB(4), kC(1), kC(2), kC(3), kC(4), T);

hold on
plot([0 l_pp*cos(thetaA), l_pp*cos(thetaA) + l_mp*cos(thetaA + thetaB), l_pp*cos(thetaA) + l_mp*cos(thetaA + thetaB) + l_dp*cos(thetaA + thetaB + thetaC)],[0, l_pp*sin(thetaA), l_pp*sin(thetaA) + l_mp*sin(thetaA + thetaB), l_pp*sin(thetaA) + l_mp*sin(thetaA + thetaB) + l_dp*sin(thetaA + thetaB + thetaC)])
scatter([0 l_pp*cos(thetaA), l_pp*cos(thetaA) + l_mp*cos(thetaA + thetaB), l_pp*cos(thetaA) + l_mp*cos(thetaA + thetaB) + l_dp*cos(thetaA + thetaB + thetaC)],[0, l_pp*sin(thetaA), l_pp*sin(thetaA) + l_mp*sin(thetaA + thetaB), l_pp*sin(thetaA) + l_mp*sin(thetaA + thetaB) + l_dp*sin(thetaA + thetaB + thetaC)])
axis equal
