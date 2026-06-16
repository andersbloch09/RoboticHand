function [thetaA_real, thetaB_real, thetaC_real] = hand_model_pulley_3rd(rA,rB,rC, kA1, kA2, kA3, kA4, kB1, kB2, kB3, kB4, kC1, kC2, kC3, kC4, T)

    % Define symbolic variables
  

    taus = [T*rA; T*rB; T*rC];

    %thetaA = (taus(1)-kA4)/(kA1^3+kA2^2+kA3);
    %thetaB = (taus(2)-kB4)/(kB1^3+kB2^2+kB3);
    %thetaC = (taus(3)-kC4)/(kC1^3+kC2^2+kC3);
    
    
    coeffA = [kA1, kA2, kA3, kA4 - taus(1)];
    thetaA_all = roots(coeffA);
    
    coeffB = [kB1, kB2, kB3, kB4 - taus(2)];
    thetaB_all = roots(coeffB);
    
    coeffC = [kC1, kC2, kC3, kC4 - taus(3)];
    thetaC_all = roots(coeffC);

    thetaA_real = thetaA_all(abs(imag(thetaA_all)) < 1e-8);
    thetaA_real = real(thetaA_real);

    thetaB_real = thetaB_all(abs(imag(thetaB_all)) < 1e-8);
    thetaB_real = real(thetaB_real);

    thetaC_real = thetaC_all(abs(imag(thetaC_all)) < 1e-8);
    thetaC_real = real(thetaC_real);



 
end