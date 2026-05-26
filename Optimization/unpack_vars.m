function params = unpack_vars(x, spring_db)

    % Example per joint (repeat for MCP/PIP/DIP)
    
    idxMCP = max(1, min(10, round(x(1)))); % MCP spring choice
    %disp(idxMCP)

    params.MCP.K  = spring_db(idxMCP).K;
    params.MCP.ls = spring_db(idxMCP).ls;
    params.MCP.Ts = spring_db(idxMCP).Ts;
    params.MCP.maxl = spring_db(idxMCP).maxl;

    params.MCP.p1     = [x(2); x(3)];
    params.MCP.rs      = x(4);
    params.MCP.rt = x(5);
    params.MCP.angle0 = x(6);

    % PIP
    idxPIP = max(1, min(10, round(x(7)))); % MCP spring choice

    params.PIP.K  = spring_db(idxPIP).K;
    params.PIP.ls = spring_db(idxPIP).ls;
    params.PIP.Ts = spring_db(idxPIP).Ts;
    params.PIP.maxl = spring_db(idxPIP).maxl;

    params.PIP.p1     = [x(8); x(9)];
    params.PIP.rs      = x(10);
    params.PIP.rt = x(11);
    params.PIP.angle0 = x(12);

    %DIP
    idxDIP = max(1, min(10, round(x(13)))); % MCP spring choice

    params.DIP.K  = spring_db(idxDIP).K;
    params.DIP.ls = spring_db(idxDIP).ls;
    params.DIP.Ts = spring_db(idxDIP).Ts;
    params.DIP.maxl = spring_db(idxDIP).maxl;

    params.DIP.p1     = [x(14); x(15)];
    params.DIP.rs      = x(16);
    params.DIP.rt = x(17);
    params.DIP.angle0 = x(18);

    % Repeat for PIP, DIP...
end