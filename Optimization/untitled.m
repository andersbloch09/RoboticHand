clc;clear;close all

T = readtable("Data1.csv");

% Vector from DIP to PIP (medial phalanx)
v_medial = [T.PIP_x - T.DIP_x, ...
      T.PIP_y - T.DIP_y];

% Vector from DIP to TIP
v_distal = [T.TIP_x - T.DIP_x, ...
      T.TIP_y - T.DIP_y];

% Dot product
dotprod = sum(v_medial .* v_distal, 2);

% Vector magnitudes
norm_medial = sqrt(sum(v_medial.^2, 2));
norm_distal = sqrt(sum(v_distal.^2, 2));

l_medial_px = mean(norm_medial);
l_distal_px = mean(norm_distal);

l_medial_mm = 27*10^-3;

factor = l_medial_mm/l_medial_px;

l_proximal_mm = 45*10^-3;
l_proximal_px = l_proximal_mm/factor;

MCP_x = T.PIP_x(1) - l_proximal_px;
MCP_y = T.PIP_y(1);

%proximal vector
v_proximal = [MCP_x - T.PIP_x, ...
      MCP_y - T.PIP_y];

norm_proximal = sqrt(sum(v_proximal.^2, 2));


dotprod2 = sum(v_proximal .* v_medial, 2);
theta_PIP = acos(dotprod2 ./ (norm_proximal .* norm_medial));
theta_PIP_deg = rad2deg(theta_PIP);

% DIP angle in radians
theta_DIP = acos(dotprod ./ (norm_medial .* norm_distal));
theta_DIP = abs(theta_DIP - deg2rad(180));
% Convert to degrees
theta_DIP_deg = rad2deg(theta_DIP);

% Add to table
T.DIP_angle = theta_DIP_deg;

%%
figure
scatter(MCP_x,MCP_y)
hold on
scatter(T.PIP_x,T.PIP_y)
scatter(T.DIP_x,T.DIP_y)
axis equal

figure
scatter(theta_PIP_deg,theta_DIP_deg,'.')