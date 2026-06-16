function [c, ceq] = nonlcon(x, spring_db)

params = unpack_vars(x, spring_db);

% MCP
p2xMCP = cos(deg2rad(params.MCP.angle0))*params.MCP.rs;
p2yMCP = sin(deg2rad(params.MCP.angle0))*params.MCP.rs; 
p2MCP = [p2xMCP; p2yMCP];
springMCP = p2MCP - params.MCP.p1;

% PIP
p2xPIP = cos(deg2rad(params.PIP.angle0))*params.PIP.rs;
p2yPIP = sin(deg2rad(params.PIP.angle0))*params.PIP.rs; 
p2PIP = [p2xPIP; p2yPIP];
springPIP = p2PIP - params.PIP.p1;

% DIP
p2xDIP = cos(deg2rad(params.DIP.angle0))*params.DIP.rs;
p2yDIP = sin(deg2rad(params.DIP.angle0))*params.DIP.rs; 
p2DIP = [p2xDIP; p2yDIP];
springDIP = p2DIP - params.DIP.p1;

% example geometry rules
c1 = params.MCP.ls - norm(springMCP); %length of spring at theta = 0, must be equal to or greater than spring rest length
c2 = params.PIP.ls - norm(springPIP);
c3 = params.DIP.ls - norm(springDIP);
c4 = norm(springMCP) - 1.3*params.MCP.ls;
c5 = norm(springPIP) - 1.3*params.PIP.ls;
c6 = norm(springDIP) - 1.3*params.DIP.ls;

% combine constraints
c = [c1; c2; c3; c4; c5; c6];
ceq = [];

end