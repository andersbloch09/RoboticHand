clc; clear; close all

ROM_MCP_deg = 90; %deg
ROM_PIP_deg = 90; %deg
ROM_DIP_deg = 90; %deg

% MCP spring
p1MCP = [-40*10^-3; 10*10^-3];

r_s_MCP = 14*10^-3; %spring pull radius

l_s_MCP = 27.2*10^-3; %spring free length

k_MCP = 0.06*1000; %spring stiffness N/m

T_s_MCP = 0.1; %spring pre tensions N

[tauMCP, thetaMCP] = spring_model_int(p1MCP, r_s_MCP, l_s_MCP, k_MCP, ROM_MCP_deg, T_s_MCP);

[tauMCP_peak, idx_peak] = max(tauMCP);

tauMCP_left = tauMCP(1:idx_peak);
thetaMCP_left = thetaMCP(1:idx_peak);
thetaMCP_peak = thetaMCP(idx_peak);

tauMCP_right = tauMCP(idx_peak+1:length(tauMCP));
thetaMCP_right = thetaMCP(idx_peak+1:length(thetaMCP));

figure
scatter(thetaMCP_left,tauMCP_left)
hold on
scatter(thetaMCP_right,tauMCP_right)

% PIP spring
p1PIP = [-45*10^-3; 10*10^-3];

r_s_PIP = 14*10^-3;

l_s_PIP = 30.4*10^-3;

k_PIP = 0.15*1000;

T_s_PIP = 0.1; %spring pre tensions N

[tauPIP, thetaPIP] = spring_model_int(p1PIP, r_s_PIP, l_s_PIP, k_PIP, ROM_PIP_deg,T_s_PIP);

[tauPIP_peak, idx_peak] = max(tauPIP);

tauPIP_left = tauPIP(1:idx_peak);
thetaPIP_left = thetaPIP(1:idx_peak);
thetaPIP_peak = thetaPIP(idx_peak);

tauPIP_right = tauPIP(idx_peak+1:length(tauPIP));
thetaPIP_right = thetaPIP(idx_peak+1:length(thetaPIP));

% DIP spring
p1DIP = [-34*10^-3; 10*10^-3];

r_s_DIP = 14*10^-3;

l_s_DIP = 22.1*10^-3;

k_PIP = 0.49*1000;

T_s_PIP = 0.1; %spring pre tensions N

[tauDIP, thetaDIP] = spring_model_int(p1DIP, r_s_DIP, l_s_DIP, k_PIP, ROM_DIP_deg, T_s_PIP);

[tauDIP_peak, idx_peak] = max(tauPIP);

tauDIP_left = tauDIP(1:idx_peak);
thetaDIP_left = thetaDIP(1:idx_peak);
thetaDIP_peak = thetaDIP(idx_peak);

tauDIP_right = tauDIP(idx_peak+1:length(tauDIP));
thetaDIP_right = thetaDIP(idx_peak+1:length(thetaDIP));


rA = 7.5*10^-3;
rB = 7.5*10^-3;
rC = 7.5*10^-3;

k_MCP = 0.01; % Nm/rad
k_PIP = 0.04; % Nm/rad
kC = 0.08; 


syms thetaPIP
thetaDIP = 0.6*thetaPIP;

T_max = 10; %N


thetaMCP(1) = 0;
thetaPIP(1) = 0;
thetaDIP(1) = 0;

steps = 10000;
%%
for i = 1:steps

    tauMCP_sim(i) = i/steps*T_max*rA;
    thetaMCP_sim(i) = interp1(tauMCP_left,thetaMCP_left,tauMCP_sim(i));
end
clear i


for i = steps:steps*2
    tauMCP_sim(i) = (i-steps)/steps*T_max*rA;
    thetaMCP_sim(i) = interp1(tauMCP_right,thetaMCP_right,tauMCP_sim(i));
end
clear i


for i = 1:steps

    tauPIP_sim(i) = i/steps*T_max*rB;
    thetaPIP_sim(i) = interp1(tauPIP_left,thetaPIP_left,tauPIP_sim(i));
end
clear i


for i = steps:steps*2
    tauPIP_sim(i) = (i-steps)/steps*T_max*rB;
    thetaPIP_sim(i) = interp1(tauPIP_right,thetaPIP_right,tauPIP_sim(i));
end

for i = 1:steps

    tauDIP_sim(i) = i/steps*T_max*rC;
    thetaDIP_sim(i) = interp1(tauDIP_left,thetaDIP_left,tauDIP_sim(i));
end
clear i


for i = steps:steps*2
    tauDIP_sim(i) = (i-steps)/steps*T_max*rB;
    thetaDIP_sim(i) = interp1(tauDIP_right,thetaDIP_right,tauDIP_sim(i));
end



fit1=fitlm(rad2deg(thetaMCP_sim), rad2deg(thetaPIP_sim))

figure
plot(fit1)

fit2 = fitlm(rad2deg(thetaPIP_sim), rad2deg(thetaDIP_sim))

figure
plot(fit2)

%%
for i = 1:steps

    T=i/steps*T_max;
    
    taus = [T*rA; T*rB; T*rC];

    tau1(i) = taus(1);

    thetaMCP_left_sim(i) = interp1(tauMCP_left,thetaMCP_left,taus(1));
    thetaMCP_right_sim(i) = interp1(tauMCP_right,thetaMCP_right,taus(1));
    

    thetaPIP_left_sim(i) = interp1(tauPIP_left,thetaPIP_left,taus(2));
    thetaPIP_right_sim(i) = interp1(tauPIP_right,thetaPIP_right,taus(2));

    thetaDIP_left_sim(i) = interp1(tauDIP_left,thetaDIP_left,taus(3));
    thetaDIP_right_sim(i) = interp1(tauDIP_right,thetaDIP_right,taus(3));

   

end

%thetaMCP_left_sim = thetaMCP_left_sim(~isnan(thetaMCP_left_sim));
%thetaMCP_right_sim = thetaMCP_right_sim(~isnan(thetaMCP_right_sim));



figure
scatter(thetaMCP_sim, tau1)
hold on
scatter(thetaMCP_right_sim, tau1)


%%
for i = 2:steps
    T = i/steps*T_max;
    fMCP = @(theta) T*rA - spring_model_int(p1MCP, r_s_MCP, l_s_MCP, k_MCP, ROM_MCP_deg,theta);

    thetaMCP(i) = fzero(fMCP, thetaMCP(i-1));

    fPIP = @(theta) T*rB - spring_model_int(p1PIP, r_s_PIP, l_s_PIP, k_PIP, ROM_PIP_deg,theta);

    thetaPIP(i) = fzero(fPIP, thetaPIP(i-1));

    fDIP = @(theta) T*rC - spring_model_int(p1DIP, r_s_DIP, l_s_DIP, k_DIP, ROM_DIP_deg,theta);

    thetaDIP(i) = fzero(fDIP, thetaDIP(i-1));
end

%thetaDIP_ref = double(subs(thetaDIP,thetaPIP, thetaPIP_sim));

%finding the theoretical values of thetaA

%RMSE = rmse(thetaDIP_ref, thetaC_sim); 

figure
%plot(thetaDIP_ref,thetaPIP_sim)
hold on
plot(rad2deg(thetaC_sim),rad2deg(thetaB_sim))
