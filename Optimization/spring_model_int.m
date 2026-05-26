function [tau, theta, valid] = spring_model_int(p1, r, ls, k, ROMdeg, T_s, angle0)
    valid = true;
    %angle0 = 90 + ROMdeg/2;
    
    step = 1;
    
    for i = 1:step:ROMdeg + 1
        
        theta(i) = -deg2rad(i-1);
    
        p2x = cos(theta(i) + deg2rad(angle0))*r;
        p2y = sin(theta(i) + deg2rad(angle0))*r;
        
        p2{i} = [p2x; p2y];
    
        spring = p2{i} - p1;
        if norm(spring) < ls
            valid = false;
            %disp("Spring geometry not valid!")
        end
        
        x(i) = norm(spring) - ls;
    
        F(i) = x(i)*k + T_s;
    
        phi(i) = acos(dot(spring,p2{i})/(norm(spring)*norm(p2{i})));
    
        tau(i) = sin(phi(i))*F(i)*r;
    
    end
    
    % figure
    % plot(rad2deg(theta),tau)
    % xlabel("theta")
    % ylabel("tau")

    %fit = polyfit(-theta,tau,3);

    %lin = fitlm(-theta,tau,"linear");

    %disp(lin.Coefficients.Estimate(2))
    
    % syms x
    % 
    % figure
    % subplot(1,2,1)
    % fplot(fit(1)*x^3+fit(2)*x^2+fit(3)*x+fit(4))
    % 
    % hold on
    % 
    % figure
    % plot(-theta,tau)
    % xlabel("theta")
    % ylabel("tau")
    % xlim([min(-theta) max(-theta)])
    % 
    % subplot(1,2,2)
    % hold on
    % scatter(p1(1),p1(2))
    % scatter(p2{1}(1),p2{1}(2))
    % scatter(cellfun(@(v)v(1), p2), cellfun(@(v)v(2), p2))
    % yline(0)
    % axis equal
    % xlim([p1(1), 10*10^-3])
    
    theta = -theta;

    % figure
    % plot(F,tau)
    % xlabel('Spring force  [N]')
    % ylabel('Torque [Nm]')
    % 
    % ylim([-1000, 0])
    % 
    % disp("max joint torque:")
    % disp(max(tau))
    %disp("spring: ")
    %disp(valid)
end
