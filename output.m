addpath('../dineof-3.0/Scripts/IO');

% convert dineof_output to .mat
%
% Input:
%   name: name for output file
%
% Output:
%   flag: 1 on success; 0 otherwise

function flag = outformat(name)
  flag = 0;

  chlor = gread('dineof_output/output.filled');
  outpath = strcat('dineof_output/', name)
  eval(['save -mat7-binary ' outpath ' chlor']);

  flag = 1;
endfunction