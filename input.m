addpath('../dineof-3.0/Scripts/IO');

function flag = informat(name)
  flag = 0;

  files = glob(strcat(name, '/*.mat'));
  timeline = [];

  for i=1:length(files)
    eval(['load ' files(i){:}]);
    data(:,:,i) = chlor;
    [~, fname] = fileparts(files{i});
    timeline = [timeline; str2num(substr(fname, 6, 3))];
  endfor

  [x, y, t] = size(data)
  mask = ones(x, y);
  for i=1:x
    for j=1:y
      if length(find(~isnan(data(i,j,:)))) / t < 0.05
        data(i,j,:) = NaN(t, 1);
        mask(i,j) = 0;
      endif
    endfor
  endfor

  gwrite("datafile.dat", data);
  gwrite("maskfile.dat", mask);
  incr = timeline(2:length(timeline)) - timeline(1:length(timeline)-1);
  disp("max time increment:"), disp(max(incr))
  disp("mean time increment:"), disp(mean(incr))
  gwrite("timefile.dat", timeline);
  save -mat7-binary 'timeline.mat' timeline;

  flag = 1;
endfunction
