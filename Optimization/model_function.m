function [thetaMCP_sim, thetaPIP_sim, thetaDIP_sim, valid] = model_function(params, ROM_MCP,ROM_PIP,ROM_DIP)

%MCP
[tauMCP, thetaMCP] = spring_model_int(params.MCP.p1, params.MCP.rs, params.MCP.ls, params.MCP.K, ROM_MCP, params.MCP.Ts, params.MCP.angle0);
[tauMCP_peak, idxMCP_peak] = max(tauMCP);
tauMCP_left = tauMCP(1:idxMCP_peak);
thetaMCP_left = thetaMCP(1:idxMCP_peak);
thetaMCP_peak = thetaMCP(idxMCP_peak);

tauMCP_right = tauMCP(idxMCP_peak+1:length(tauMCP));
thetaMCP_right = thetaMCP(idxMCP_peak+1:length(thetaMCP));

dMCP = diff(tauMCP);

signChange = diff(sign(dMCP));

idxMCP_peak = find(signChange < 0, 1, 'first') + 1;
idxMCP_valley = find(signChange > 0, 1, 'first') + 1;

idx_turnoverMCP = min([idxMCP_valley, idxMCP_peak]);

isIncreasing = all(dMCP >= 0);
isDecreasing = all(dMCP <= 0);

isMonotonic = isIncreasing || isDecreasing;

valid = true;

if ~isMonotonic
    frac = idx_turnoverMCP/length(tauMCP);
else
    frac = 1;
end
%disp(frac)

if frac < 0.75
    valid = false;
end
%valid = isMonotonic;

clear isMonotonic isIncreasing isDecreasing signChange


%PIP
[tauPIP, thetaPIP] = spring_model_int(params.PIP.p1, params.PIP.rs, params.PIP.ls, params.PIP.K, ROM_PIP, params.PIP.Ts, params.PIP.angle0);
[tauPIP_peak, idxPIP_peak] = max(tauPIP);

tauPIP_left = tauPIP(1:idxPIP_peak);
thetaPIP_left = thetaPIP(1:idxPIP_peak);
thetaPIP_peak = thetaPIP(idxPIP_peak);

tauPIP_right = tauPIP(idxPIP_peak+1:length(tauPIP));
thetaPIP_right = thetaPIP(idxPIP_peak+1:length(thetaPIP));

dPIP = diff(tauPIP);

signChange = diff(sign(dPIP));

idxPIP_peak = find(signChange < 0, 1, 'first') + 1;
idxPIP_valley = find(signChange > 0, 1, 'first') + 1;

idx_turnoverPIP = min([idxPIP_valley, idxPIP_peak]);

isIncreasing = all(dPIP >= 0);
isDecreasing = all(dPIP <= 0);

isMonotonic = isIncreasing || isDecreasing;

if ~isMonotonic
    frac = idx_turnoverPIP/length(tauPIP);
else
    frac = 1;
end
%disp(frac)

if valid
    if frac < 0.75
        valid = false;
    end
end


clear isMonotonic isIncreasing isDecreasing signChange

%DIP
[tauDIP, thetaDIP] = spring_model_int(params.DIP.p1, params.DIP.rs, params.DIP.ls, params.DIP.K, ROM_DIP, params.DIP.Ts, params.DIP.angle0);
[tauDIP_peak, idxDIP_peak] = max(tauDIP);

tauDIP_left = tauDIP(1:idxDIP_peak);
thetaDIP_left = thetaDIP(1:idxDIP_peak);
thetaDIP_peak = thetaDIP(idxDIP_peak);

tauDIP_right = tauDIP(idxDIP_peak+1:length(tauDIP));
thetaDIP_right = thetaDIP(idxDIP_peak+1:length(thetaDIP));

dDIP = diff(tauDIP);

signChange = diff(sign(dDIP));

idxDIP_peak = find(signChange < 0, 1, 'first') + 1;
idxDIP_valley = find(signChange > 0, 1, 'first') + 1;

idx_turnoverDIP = min([idxDIP_valley, idxDIP_peak]);

isIncreasing = all(dDIP >= 0);
isDecreasing = all(dDIP <= 0);

isMonotonic = isIncreasing || isDecreasing;

if ~isMonotonic
    frac = idx_turnoverDIP/length(tauDIP);
else
    frac = 1;
end

%disp(frac)

if valid
    if frac < 0.75
        valid = false;
    end
end

clear isMonotonic isIncreasing isDecreasing

% initializing the spring simulation

steps = 10000;

[maxtau, max_idx] = max([tauMCP_peak, tauPIP_peak, tauDIP_peak]);

if max_idx == 1
    r_max = params.MCP.rt;
end
if max_idx == 2
    r_max = params.PIP.rt;
end
if max_idx == 3
    r_max = params.DIP.rt;
end

T_max = maxtau/r_max*1.1;

T_max = max([tauMCP_peak/params.MCP.rt, tauPIP_peak/params.PIP.rt, tauDIP_peak/params.DIP.rt])*1.1;


disp("Tmax:" + num2str(T_max) + "N")

thetaMCP_sim = zeros(1, steps);


% MCP left side (increasing)
for i = 1:steps
    tauMCP_sim(i) = i/steps*T_max*params.MCP.rt;
    thetaMCP_sim(i) = interp1(tauMCP_left,thetaMCP_left,tauMCP_sim(i));
end
clear i

% MCP Right side (only relevant if non-monotonic solutions are accepted)
% for i = steps:steps*2
%     tauMCP_sim(i) = (i-steps)/steps*T_max*params.MCP.rt;
%     thetaMCP_sim(i) = interp1(tauMCP_right,thetaMCP_right,tauMCP_sim(i));
% end
%clear i

% PIP left side (increasing)
for i = 1:steps

    tauPIP_sim(i) = i/steps*T_max*params.PIP.rt;
    thetaPIP_sim(i) = interp1(tauPIP_left,thetaPIP_left,tauPIP_sim(i));
end
clear i

% PIP Right side (only relevant if non-monotonic solutions are accepted)
% for i = steps:steps*2
%     tauPIP_sim(i) = (i-steps)/steps*T_max*params.PIP.rt;
%     thetaPIP_sim(i) = interp1(tauPIP_right,thetaPIP_right,tauPIP_sim(i));
% end
%clear i

% DIP left side (increasing)
for i = 1:steps
    tauDIP_sim(i) = i/steps*T_max*params.DIP.rt;
    thetaDIP_sim(i) = interp1(tauDIP_left,thetaDIP_left,tauDIP_sim(i));
end
clear i

% DIP Right side (only relevant if non-monotonic solutions are accepted)
% for i = steps:steps*2
%     tauDIP_sim(i) = (i-steps)/steps*T_max*params.DIP.rt;
%     thetaDIP_sim(i) = interp1(tauDIP_right,thetaDIP_right,tauDIP_sim(i));
% end
%clear i


idx1 = find(~isnan(thetaMCP_sim),1, 'first');
idx4 = find(~isnan(thetaMCP_sim),1, 'last');
thetaMCP_sim(1:idx1-1) = 0;
%thetaMCP_sim(end) = deg2rad(90);
thetaMCP_sim(idx4+1:10000) = deg2rad(ROM_MCP);


idx2 = find(~isnan(thetaPIP_sim),1, 'first');
idx5 = find(~isnan(thetaPIP_sim),1, 'last');
thetaPIP_sim(1:idx2-1) = 0;
%thetaPIP_sim(end) = deg2rad(90);
thetaPIP_sim(idx5+1:10000) = deg2rad(ROM_PIP);

idx3 = find(~isnan(thetaDIP_sim),1, 'first');
idx6 = find(~isnan(thetaDIP_sim),1, 'last');
thetaDIP_sim(1:idx3-1) = 0;
%thetaDIP_sim(end) = deg2rad(90);
thetaDIP_sim(idx6+1:10000) = deg2rad(ROM_DIP);

end