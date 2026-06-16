function [thetaA, thetaB, thetaC, F_tip] = hand_model_3rd(l_pp, l_mp, l_dp, kA1, kA2, kA3, kA4, kB1, kB2, kB3, kB4, kC1, kC2, kC3, kC4, T)



    % Define symbolic variables
    syms thetaA thetaB thetaC
    
    % Tip position
    xTIP = l_pp*cos(thetaA) + l_mp*cos(thetaA + thetaB) + l_dp*cos(thetaA + thetaB + thetaC);
    yTIP = l_pp*sin(thetaA) + l_mp*sin(thetaA + thetaB) + l_dp*sin(thetaA + thetaB + thetaC);
    
    x = [xTIP; yTIP];
    theta = [thetaA, thetaB, thetaC];
    
    % Jacobian
    J = jacobian(x, theta);
    
    % Torques
    taus = [kA1*thetaA^3+kA2*thetaA^2+kA3*thetaA+kA4;
            kB1*thetaB^3+kB2*thetaB^2+kB3*thetaB+kB4; 
            kC1*thetaC^3+kC2*thetaC^2+kC3*thetaC+kC4];
    
    
    % Force at tip
    that = [-sin(thetaA+thetaB+thetaC); cos(thetaA+thetaB+thetaC)];
    
    thetaA = zeros(100);
    thetaB = zeros(100);
    thetaC=zeros(100);
    
    F_tip = T*that;
    % Equations in the form eqs = 0
    eqs = taus - J'*F_tip;   % <--- subtract, do NOT use '=='
    
    % Initial guess
    theta0 = [0.1, 0.1, 0.1];
    
    % Convert symbolic equations to numeric function
    F_fun = matlabFunction(eqs, 'Vars', {theta});
    
    % Solve numerically
    theta_sol = fsolve(F_fun, theta0);
    
    %disp(theta_sol)
    
    thetaA=theta_sol(1,1);
    thetaB=theta_sol(1,2);
    thetaC=theta_sol(1,3);
 
end





