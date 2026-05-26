clc; clear; close all

% Design variables

% var_strings = {'K_MCP', 'K_PIP', 'K_DIP', 
%                'l_s_MCP','l_s_PIP', 'l_s_DIP', 
%                'T_s_MCP','T_s_PIP','T_s_DIP' ,
%                'p1xMCP', 'p1xPIP', 'p1xDIP', 
%                'p1yMCP', 'p1yPIP', 'p1yDIP', 
%                'rMCP', 'rPIP', 'rDIP',
%                'theta1MCP','theta1PIP','theta1DIP',
%                'ROM_MCP','ROM_PIP','ROM_DIP'};

var_strings = {'springID_MCP', 'springID_PIP', 'springID_DIP', 
               'p1xMCP', 'p1xPIP', 'p1xDIP',
               'p1yMCP', 'p1yPIP', 'p1yDIP', 
               'r_sMCP', 'r_sPIP', 'r_sDIP',
               'r_tMCP', 'r_tPIP', 'r_tDIP',
               'theta1MCP','theta1PIP','theta1DIP'};

%loading spring variables from RS components CSV file
opts = detectImportOptions('RS-DK-traekfjedre.csv', 'Delimiter', ',');
springTable = readtable('RS-DK-traekfjedre.csv', opts);

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


nVars = numel(var_strings);

IntCon = [1 7 13]; % indices of integer variables


lb = [1, -60*10^-3, 0, 5*10^-3, 2.5*10^-3, 45, 1, -50*10^-3, 0, 5*10^-3, 2.5*10^-3, 45, 1, -36*10^-3, 0, 5*10^-3, 2.5*10^-3, 90];
ub = [10,-25*10^-3, 15*10^-3, 15*10^-3, 10*10^-3, 180, 10, -25*10^-3, 15*10^-3, 15*10^-3, 10*10^-3, 180, 10, -25*10^-3, 10*10^-3, 15*10^-3, 10*10^-3, 180];

%check that boundaries match the design variables
for i = 1:length(ub)
    disp("Design variable no.  " + num2str(i) + ": " + var_strings{i} + ". Lower limit: "+ num2str(lb(i)) + ", upper limit: " + num2str(ub(i)))
end

ROM_MCP = 87;
ROM_PIP = 110;
ROM_DIP = 60;

%working parameters (only ad ROM=60)
% x_valid = [2, -40*10^-3, 10*10^-3, 14*10^-3, 5*10^-3,160,...
%     2, -40*10^-3, 10*10^-3, 14*10^-3, 5*10^-3,160, ...
%     2, -40*10^-3, 10*10^-3, 14*10^-3, 5*10^-3,160,];

x_valid = [2, -45*10^-3, 8*10^-3, 14*10^-3, 5*10^-3,170,...
    7, -50*10^-3, 13*10^-3, 14*10^-3, 5*10^-3,165, ...
    8, -36*10^-3, 10*10^-3, 14*10^-3, 5*10^-3,160,];

fitness = @(x) objective_function(x, spring_db, ROM_MCP, ROM_PIP, ROM_DIP);
nonlcon_handle = @(x) nonlcon(x, spring_db);

% Normalize parameters

lb_norm = zeros(1, nVars);
ub_norm = ones(1, nVars);

%lb_norm(IntCon) = 1;
%ub_norm(IntCon) = 10;


% fitness_norm = @(x_norm) objective_function( ...
%     decode(x_norm, lb, ub, [1 7 13]), ...
%     spring_db, ROM_MCP, ROM_PIP, ROM_DIP);

fitness_norm = @(x_norm) objective_function( ...
    fix_ints(denormalize(x_norm, lb, ub), IntCon), ...
    spring_db, ROM_MCP, ROM_PIP, ROM_DIP);

nonlcon_handle_norm = @(x_norm) nonlcon( ...
    decode(x_norm, lb, ub, [1 7 13]), ...
    spring_db);

x_valid_norm = (x_valid - lb) ./ (ub - lb);



%%
%GA options
% options = optimoptions('ga', ...
%     'PopulationSize', 100, ...
%     'MaxGenerations', 50, ...
%     'Display', 'iter', ...
%     'UseParallel', true, ...
%     'PlotFcn', {@gaplotbestf}, ...
%     'InitialPopulationMatrix',x_valid);

%GA options testing
% options = optimoptions('ga', ...
%     'PopulationSize', 10, ...
%     'MaxGenerations', 5, ...
%     'Display', 'iter', ...
%     'UseParallel', true, ...
%     'PlotFcn', {@gaplotbestf});

%GA options for normalised variables
options = optimoptions('ga', ...
    'Display', 'iter', ...
    'UseParallel', true, ...
    'PlotFcn', {@gaplotbestf}, ...
    'InitialPopulationMatrix',x_valid_norm, ...
    'EliteCount',5);


% Run GA
%with constraints
% [x_opt, fval] = ga(fitness, nVars, ...
%     [], [], [], [], lb, ub, ...
%     nonlcon_handle,IntCon, options);

%without constraints
% [x_opt, fval] = ga(fitness, nVars, ...
%     [], [], [], [], lb, ub, ...
%     [], options);

%with normalized variables
[x_opt_norm, fval] = ga(fitness_norm, nVars, ...
    [], [], [], [], lb_norm, ub_norm, ...
    nonlcon_handle_norm, options);

x_opt = decode(x_opt_norm, lb, ub, [1 7 13]);



disp('Optimal design:');

for i = 1:length(ub)
    disp(var_strings{i} + " = "+ num2str(x_opt(i)))
end

function x = denormalize(x_norm, lb, ub)
    x = lb + x_norm .* (ub - lb);
end

function x = decode(x_norm, lb, ub, IntCon)

    % Step 1: denormalize
    x = lb + x_norm .* (ub - lb);

    % Step 2: round integer variables
    x(IntCon) = round(x(IntCon));

    % Step 3: clamp to bounds
    x(IntCon) = max(min(x(IntCon), ub(IntCon)), lb(IntCon));

end

function x = fix_ints(x, IntCon)
    x(IntCon) = round(x(IntCon));
end