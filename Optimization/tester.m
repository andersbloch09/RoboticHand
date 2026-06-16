clc; clear; close all

var_strings = {'springID_MCP', 'springID_PIP', 'springID_DIP', 
               'p1xMCP', 'p1xPIP', 'p1xDIP',
               'p1yMCP', 'p1yPIP', 'p1yDIP', 
               'r_sMCP', 'r_sPIP', 'r_sDIP',
               'r_tMCP', 'r_tPIP', 'r_tDIP',
               'theta1MCP','theta1PIP','theta1DIP'};

%loading spring variables from RS components CSV file
opts = detectImportOptions('RS-DK-traekfjedre.csv', 'Delimiter', ',');
springTable = readtable('RS-DK-traekfjedre.csv', opts);

ROM_MCP = 87;
ROM_PIP = 110;
ROM_DIP = 60;



for i = 1:height(springTable)
    
    K = springTable.Fjederstivhed{i};
    ls = springTable.FriL_ngde{i};
    Ts = springTable.Injektionstid{i};
    maxl = springTable.UdstraktL_ngdeMaks_{i};

    spring_db(i).K = str2double(erase(K, 'N/mm')) * 1000;
    spring_db(i).ls = str2double(erase(ls, 'mm')) * 10^-3;
    spring_db(i).Ts = str2double(erase(Ts, 'N'));
    spring_db(i).maxl = str2double(erase(maxl, 'mm')) * 10^-3;

end
% ... up to 10

[~, idx] = sort([spring_db.K]);
spring_db = spring_db(idx);

x0 = [2, -45*10^-3, 8*10^-3, 14*10^-3, 5*10^-3,170,...
    7, -50*10^-3, 13*10^-3, 14*10^-3, 5*10^-3,165, ...
    8, -36*10^-3, 10*10^-3, 14*10^-3, 5*10^-3,160,];

x1_struct = load("x_opt_11.mat");
x1 = x1_struct.x_opt;

% x = [2, -40*10^-3, 10*10^-3, 14*10^-3, 5*10^-3,160,...
%     2, -40*10^-3, 10*10^-3, 14*10^-3, 5*10^-3,160, ...
%     2, -40*10^-3, 10*10^-3, 14*10^-3, 5*10^-3,160,];

%params = unpack_vars(x, spring_db);

%[thetaMCP_sim, thetaPIP_sim, thetaDIP_sim, valid] = model_function(params, ROM_MCP, ROM_PIP, ROM_DIP);
%%
% idx1 = find(~isnan(thetaMCP_sim),1, 'first');
% idx4 = find(~isnan(thetaMCP_sim),1, 'last');
% thetaMCP_sim(1:idx1-1) = 0;
% %thetaMCP_sim(end) = deg2rad(90);
% thetaMCP_sim(idx4+1:10000) = deg2rad(ROM_MCP);
% 
% 
% idx2 = find(~isnan(thetaPIP_sim),1, 'first');
% idx5 = find(~isnan(thetaPIP_sim),1, 'last');
% thetaPIP_sim(1:idx2-1) = 0;
% %thetaPIP_sim(end) = deg2rad(90);
% thetaPIP_sim(idx5+1:10000) = deg2rad(ROM_PIP);
% 
% idx3 = find(~isnan(thetaDIP_sim),1, 'first');
% idx6 = find(~isnan(thetaDIP_sim),1, 'last');
% thetaDIP_sim(1:idx3-1) = 0;
% %thetaDIP_sim(end) = deg2rad(90);
% thetaDIP_sim(idx6+1:10000) = deg2rad(ROM_DIP);
% 
%scatter(thetaMCP_sim, thetaPIP_sim)


% x1(5) = x1(5)*0.7;
% x1(11) = x1(11)*0.7;
% x1(17) = x1(17)*0.7;



% Compute error

%[c, ceq] = nonlcon(x1,spring_db)

cost = objective_function(x1, spring_db, ROM_MCP, ROM_PIP, ROM_DIP)

params = unpack_vars(x1,spring_db);

[thetaMCP, thetaPIP, thetaDIP, valid] = model_function(params, ROM_MCP, ROM_PIP, ROM_DIP);

%u = rad2deg(thetaPIP);

%thetaDIP_ref = deg2rad(-1.7e-6*u.^4 + 0.00026*u.^3 - 0.0053*u.^2 + 0.17*u + 0.52);



syms u x g
v = -1.7e-6*u.^4 + 0.00026*u.^3 - 0.0053*u.^2 + 0.17*u + 0.52;
y = 6e-6*x.^4 - 0.0015*x^3 + 0.11*x^2 - 0.96*x + 5.6;
d = 0.6 * x;
e = 3/4*x;
f = 2*x;

eq = g == deg2rad(0.77660232*x^2 + 1.37397306*x + 0.07324267*x);

h = solve(eq, x);

x = thetaPIP;
y = thetaDIP;
z = thetaMCP;


splitidx = find(thetaPIP == deg2rad(110), 1);
x(splitidx:end-1) = NaN;
y(splitidx:end-1) = NaN;
z(splitidx:end-1) = NaN;

valid = ~isnan(x) & ~isnan(y) & ~isnan(z);
x = x(valid);
y = y(valid);
z = z(valid);

[xu, ~, ic] = unique(x);
yu = accumarray(ic, y, [], @mean);
zu = accumarray(ic, z, [], @mean);

xq = linspace(min(xu), max(xu), 500);

yq = interp1(xu, yu, xq, 'pchip');

zq = interp1(xu, zu, xq, 'pchip');

width = 1.5;

figure
hold on
plot(rad2deg(xq), rad2deg(yq), Color='#7adecc', LineStyle='--', LineWidth=width, DisplayName='Expected path')
plot(rad2deg(thetaPIP(1:splitidx-1)),rad2deg(thetaDIP(1:splitidx-1)), Color='#06CAA6', LineWidth=width, DisplayName='Estimated path')
plot(rad2deg(thetaPIP(splitidx:end)),rad2deg(thetaDIP(splitidx:end)), Color='#06CAA6', LineWidth=width, HandleVisibility='off')
fplot(v, Color='#ff5a21', LineWidth=width/2, DisplayName='Reference path')
%fplot(d)
%plot(rad2deg(thetaPIP),rad2deg(thetaDIP_ref))
xlabel("PIP angle [°]")
ylabel("DIP angle [°]")
xlim([0 ROM_PIP])
ylim([0 ROM_DIP])
grid on
legend('Location', 'southeast')

figure
hold on
plot(rad2deg(zq), rad2deg(xq), Color='#7adecc', LineStyle='--', LineWidth=width, DisplayName='Expected path')
plot(rad2deg(thetaMCP(1:splitidx-1)),rad2deg(thetaPIP(1:splitidx-1)), Color='#06CAA6', LineWidth=width, DisplayName='Estimated path')
plot(rad2deg(thetaMCP(splitidx:end)),rad2deg(thetaPIP(splitidx:end)), Color='#06CAA6', LineWidth=width, HandleVisibility='off')
%fplot(y)
fplot(e, Color='#ff5a21', LineWidth=width/2, DisplayName='Boundaries')
fplot(f, Color='#ff5a21', LineWidth=width/2, HandleVisibility='off')
xlabel("MCP angle [°]")
ylabel("PIP angle [°]")
xlim([0 ROM_MCP])
ylim([0 ROM_PIP])

grid on
legend('Location', 'southeast')

thetaPIP = -thetaPIP;
thetaMCP = -thetaMCP;
thetaDIP = -thetaDIP;

%%

lproximal = 45*10^-3;
lmiddle = 27*10^-3;
ldistal = 20*10^-3;

figure
hold on



for i = 1:400:length(thetaMCP)
    s = [0, cos(thetaMCP(i))*lproximal, cos(thetaMCP(i))*lproximal+cos(thetaMCP(i) + thetaPIP(i))*lmiddle, cos(thetaMCP(i))*lproximal + cos(thetaMCP(i) + thetaPIP(i))*lmiddle + cos(thetaMCP(i) + thetaPIP(i) + thetaDIP(i))*ldistal];
    u = [0, sin(thetaMCP(i))*lproximal, sin(thetaMCP(i))*lproximal+sin(thetaMCP(i) + thetaPIP(i))*lmiddle, sin(thetaMCP(i))*lproximal + sin(thetaMCP(i) + thetaPIP(i))*lmiddle + sin(thetaMCP(i) + thetaPIP(i) + thetaDIP(i))*ldistal];
    plot(s(1,1:2),u(1,1:2),Color='#06CAA6',LineWidth=1.5)
    plot(s(1,2:3),u(1,2:3), Color='#ff5a21',LineWidth=1.5)
    plot(s(1,3:4),u(1,3:4), Color='#ffd648',LineWidth=1.5)
end

axis equal
legend('Proximal phalanx','Medial phalanx', 'Distal phalanx')

xlim([-0.04, 0.10])

xlabel('x [mm]')
ylabel('y [mm]')

%%



figure
hold on

% Original trajectory
h1 = plot([0 0],[0 0], ...
    'Color','#06CAA6','LineWidth',2,DisplayName='Robot proximal');

h2 = plot([0 0],[0 0], ...
    'Color','#ff5a21','LineWidth',2,DisplayName='Robot medial');

h3 = plot([0 0],[0 0], ...
    'Color','#ffd648','LineWidth',2,DisplayName='Robot distal');

% Overlay trajectory
h1b = plot([0 0],[0 0], '--', ...
    'Color','#06CAA6','LineWidth',1.5, HandleVisibility='off');

h2b = plot([0 0],[0 0], '--', ...
    'Color','#ff5a21','LineWidth',1.5,DisplayName='Reference medial');

h3b = plot([0 0],[0 0], '--', ...
    'Color','#ffd648','LineWidth',1.5,DisplayName='Reference distal');

axis equal
xlim([-0.04, 0.10])
ylim([-0.10, 0.05])

xlabel('x [mm]')
ylabel('y [mm]')

v = VideoWriter('finger_animation.mp4','MPEG-4');
v.FrameRate = 30;
v.Quality = 100;

open(v)


for i = 1:50:length(thetaMCP)

    % =========================
    % ORIGINAL DATA TRAJECTORY
    % =========================

    s = [0, ...
         cos(thetaMCP(i))*lproximal, ...
         cos(thetaMCP(i))*lproximal + ...
         cos(thetaMCP(i)+thetaPIP(i))*lmiddle, ...
         cos(thetaMCP(i))*lproximal + ...
         cos(thetaMCP(i)+thetaPIP(i))*lmiddle + ...
         cos(thetaMCP(i)+thetaPIP(i)+thetaDIP(i))*ldistal];

    u = [0, ...
         sin(thetaMCP(i))*lproximal, ...
         sin(thetaMCP(i))*lproximal + ...
         sin(thetaMCP(i)+thetaPIP(i))*lmiddle, ...
         sin(thetaMCP(i))*lproximal + ...
         sin(thetaMCP(i)+thetaPIP(i))*lmiddle + ...
         sin(thetaMCP(i)+thetaPIP(i)+thetaDIP(i))*ldistal];

    % =========================
    % FUNCTION-BASED TRAJECTORY
    % =========================

    t = i;

    thetaMCP2 = rad2deg(abs(thetaMCP(t)));
    thetaPIP2 = -(6e-6*(thetaMCP2)^4 - 0.0015*(thetaMCP2)^3 + 0.11*(thetaMCP2)^2 - 0.96*(thetaMCP2) + 5.6);
    thetaDIP2 = -(-1.7e-6*(thetaPIP2)^4 + 0.00026*(abs(thetaPIP2))^3 - 0.0053*(abs(thetaPIP2))^2 + 0.17*(abs(thetaPIP2)) + 0.52);
    thetaMCP2 = -thetaMCP2;

    s2 = [0, ...
          cosd(thetaMCP2)*lproximal, ...
          cosd(thetaMCP2)*lproximal + ...
          cosd(thetaMCP2+thetaPIP2)*lmiddle, ...
          cosd(thetaMCP2)*lproximal + ...
          cosd(thetaMCP2+thetaPIP2)*lmiddle + ...
          cosd(thetaMCP2+thetaPIP2+thetaDIP2)*ldistal];

    u2 = [0, ...
          sind(thetaMCP2)*lproximal, ...
          sind(thetaMCP2)*lproximal + ...
          sind(thetaMCP2+thetaPIP2)*lmiddle, ...
          sind(thetaMCP2)*lproximal + ...
          sind(thetaMCP2+thetaPIP2)*lmiddle + ...
          sind(thetaMCP2+thetaPIP2+thetaDIP2)*ldistal];

    % Update original trajectory
    set(h1,'XData',s(1:2),'YData',u(1:2))
    set(h2,'XData',s(2:3),'YData',u(2:3))
    set(h3,'XData',s(3:4),'YData',u(3:4))

    % Update overlay trajectory
    set(h1b,'XData',s2(1:2),'YData',u2(1:2))
    set(h2b,'XData',s2(2:3),'YData',u2(2:3))
    set(h3b,'XData',s2(3:4),'YData',u2(3:4))
    legend

    drawnow
    frame = getframe(gcf);
    writeVideo(v, frame);
end

close(v)

%%

%check design variables
for i = 1:length(x1)
    disp("Design variable no.: " + var_strings{i} + " = " + num2str(x1(i)))
end