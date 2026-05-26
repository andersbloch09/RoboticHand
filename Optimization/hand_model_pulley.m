function [thetaA, thetaB, thetaC] = hand_model_pulley(rA,rB,rC, kA, kB, kC, T)

    % Define symbolic variables
  

    taus = [T*rA; T*rB; T*rC];

    thetaA = taus(1)/kA;
    thetaB = taus(2)/kB;
    thetaC = taus(3)/kC;
 
end