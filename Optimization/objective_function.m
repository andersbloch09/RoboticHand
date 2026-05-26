function cost = objective_function(x, spring_db, ROM_MCP, ROM_PIP, ROM_DIP)

params = unpack_vars(x,spring_db);

try
    [thetaMCP, thetaPIP, thetaDIP, valid] = model_function(params, ROM_MCP, ROM_PIP, ROM_DIP);
    
    if ~valid
        cost = 1e6; % penalty
        return;
    end
  

    
    %thetaDIP_ref = 0.6*thetaPIP;
    u = rad2deg(thetaPIP);
    v = -1.7e-6*u.^4 + 0.00026*u.^3 - 0.0053*u.^2 + 0.17*u + 0.52;
    thetaDIP_ref = deg2rad(v);


    % Compute error
    cost = rmse(thetaDIP, thetaDIP_ref);
    

    penalty = zeros(1,length(thetaMCP));
    for i = 1:length(thetaDIP)
        if thetaPIP(i) < thetaMCP(i)*deg2rad(42)/deg2rad(50)
            penalty(i) = thetaMCP(i)*deg2rad(42)/deg2rad(50) - thetaPIP(i);
        end
    end

    for i = 1:length(thetaDIP)
        if thetaPIP(i) > thetaMCP(i).*deg2rad(130)/deg2rad(60)
            penalty(i) = thetaPIP(i) - thetaMCP(i)*deg2rad(130)/deg2rad(60); 
        end
    end

    totpen = sum(penalty)/length(thetaMCP);

    cost = cost + totpen;

catch
    %disp("crash")
    cost = 1e6; % catch crashes safely
end

end