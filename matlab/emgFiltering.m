clear all;
close all;

filename = '../data/MVC_11-31_14-06-2024.csv';

% Set table options
opts = detectImportOptions(filename);
opts.DataLines = 2;
numVars = length(opts.VariableNames);
columnNames = {'Time', 'EMG0', 'EMG1', 'Torque', 'Angle', 'Target', 'Velocity'};
opts.VariableNames = columnNames;
opts.SelectedVariableNames = columnNames;

% Import the data
data = readtable(filename, opts);

% Select EMG to work on
emg = data.EMG0;

% Parameters
Fs = 750; % Sampling frequency in Hz
f_notch = 50; % Notch filter frequency for power line interference
f_highpass = 15; % High-pass filter cutoff frequencies in Hz
f_lowpass = 1.6; % Low-pass filter cutoff frequency in Hz

% Create figure with tabs
figure;
tgroup = uitabgroup;

% Step 0: Original EMG
tab1 = uitab(tgroup, 'Title', 'Original EMG');
ax1 = axes('Parent', tab1);
subplot(2,1,1, 'Parent', tab1);
plot(emg);
title('Original EMG in Time Domain');
xlabel('Samples');
ylabel('Amplitude');

subplot(2,1,2, 'Parent', tab1);
pwelch(emg, [], [], [], Fs);
title('Periodogram of Original EMG');

% Step 1: Notch-filtering (if necessary)
d_notch = designfilt('bandstopiir', 'FilterOrder', 2, ...
    'HalfPowerFrequency1', f_notch-1, 'HalfPowerFrequency2', f_notch+1, ...
    'DesignMethod', 'butter', 'SampleRate', Fs);
emg_notched = filtfilt(d_notch, emg);

% Step 2: High/band-pass filtering
d_highpass = designfilt('highpassiir', 'FilterOrder', 2, ...
    'HalfPowerFrequency', f_highpass, 'DesignMethod', 'butter', 'SampleRate', Fs);
emg_filtered = filtfilt(d_highpass, emg_notched);

% Step 3: Filtered EMG
tab2 = uitab(tgroup, 'Title', 'Filtered EMG');
ax2 = axes('Parent', tab2);
subplot(2,1,1, 'Parent', tab2);
plot(emg_filtered);
title('Filtered EMG in Time Domain');
xlabel('Samples');
ylabel('Amplitude');

subplot(2,1,2, 'Parent', tab2);
pwelch(emg_filtered, [], [], [], Fs);
title('Periodogram of Filtered EMG');

% Step 4: Rectification
emg_rectified = abs(emg_filtered);

% Step 5: Low-pass filtering
d_lowpass = designfilt('lowpassiir', 'FilterOrder', 2, ...
    'HalfPowerFrequency', f_lowpass, 'DesignMethod', 'butter', 'SampleRate', Fs);
emg_envelope = filtfilt(d_lowpass, emg_rectified);

% Step 6: Linear Envelope
tab3 = uitab(tgroup, 'Title', 'Linear Envelope');
ax3 = axes('Parent', tab3);
subplot(2,1,1, 'Parent', tab3);
plot(emg_envelope);
title('EMG Linear Envelope in Time Domain');
xlabel('Samples');
ylabel('Amplitude');

subplot(2,1,2, 'Parent', tab3);
pwelch(emg_envelope, [], [], [], Fs);
title('Periodogram of EMG Linear Envelope');

% Step 7: Identify the max linear envelope value for each muscle
max_envelope_value = max(emg_envelope);

% Step 8: Normalization with respect to the max MVC value
normalized_emg = emg_envelope / max_envelope_value;

% Normalized EMG
tab4 = uitab(tgroup, 'Title', 'Normalized EMG');
ax4 = axes('Parent', tab4);
plot(normalized_emg);
title('Normalized EMG');
xlabel('Samples');
ylabel('Normalized Amplitude');
