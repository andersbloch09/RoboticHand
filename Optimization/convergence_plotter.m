clc; clear;

openfig('x_opt_11.fig');

% Find all scatter objects
h = findobj(gca, 'Type', 'Scatter');

% Use the first scatter
h1 = h(2);

% Extract data
x = h1.XData;
y = h1.YData;

close all

% Connect points
figure
hold on
plot(x, y, '-o', 'LineWidth',1, 'Color','#06CAA6')

% Add y-value labels at each point
for i = 1:length(x)
    text(x(i), y(i), sprintf('%.2e', y(i)), ...
        'VerticalAlignment','bottom', ...
        'HorizontalAlignment','left', ...
        'FontSize',8);
end

ylim([0,10e6])
grid on

ax = gca;
ax.YScale = 'log';

sprintf('%.2e', y(i))

xlabel('Generation no.')
ylabel('f(x)')

hold off