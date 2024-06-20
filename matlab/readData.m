% Define the filename
filename = '../data/MVC_20-6--11-49.csv';
fs = 750;

% Create an import options object
opts = detectImportOptions(filename);

% Set the data lines to start reading from the second line
opts.DataLines = 2;

% Get the number of variables (columns) in the file
numVars = length(opts.VariableNames);

% Define custom column names, skipping the first column
customNames = {'Time', 'EMG0', 'EMG1', 'Torque', 'Angle', 'Target', 'Velocity'}; % Adjust the number and names of the columns

% Update the variable names in the import options, excluding the first column
opts.VariableNames = customNames;
opts.SelectedVariableNames = customNames;

% Import the data
data = readtable(filename, opts);

MVC0 = max(data.('EMG0'))
MVC1 = max(data.('EMG1'))

% Display the data (optional)
% head(data);

% Create a figure window with tabs for each column
fig = figure;
tgroup = uitabgroup('Parent', fig);

% Loop through each column and create a tab with a plot
for i = 2:width(data)
    % Create a new tab
    tab = uitab('Parent', tgroup, 'Title', customNames{i});
    
    % Create an axes in the tab
    ax = axes('Parent', tab);
    
    % Plot the data for the current column
    plot(data.Time, data.(customNames{i}));
    
    % Label the axes
    xlabel(ax, 'Index');
    ylabel(ax, customNames{i});
    title(ax, ['Plot of ', customNames{i}]);
end