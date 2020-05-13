fdir = '/home/mchristo/DATA/';
files = dir(fdir);

for k=1:length(files)
    file = files(k).name;
    sz = files(k).bytes;
    
    if(~endsWith(file,".dat"))
        continue
    end
    
    if(exist(replace(file,'.dat','.mat')))
        continue
    end
    
    disp(file)
    fd = fopen([fdir, file],'rb');
    fseek(fd, 4, 0);
    raw.version = fread(fd, 1, 'single');
    raw.ch.cf = fread(fd, 1, 'double');
    raw.ch.bw = fread(fd, 1, 'double');
    raw.ch.len = fread(fd, 1, 'double');
    raw.ch.amp = fread(fd, 1, 'double');
    raw.ch.prf = fread(fd, 1, 'double');
    raw.tracelen = fread(fd, 1, 'double');
    raw.fs = fread(fd, 1, 'double');
    raw.stack = fread(fd, 1, 'uint');
    
    nt =  floor((sz - 68)/(20056));
    
    raw.data = zeros(5000, nt);
    raw.lat = zeros(1, nt);
    raw.lon = zeros(1, nt);
    raw.alt = zeros(1, nt);
    raw.timefull = zeros(1, nt);
    raw.timefrac = zeros(1, nt);
    
    % for ntrace
    for j=1:nt
        fread(fd, 1, 'int64');
        raw.timefull(j) = fread(fd, 1, 'int64');
        raw.timefrac(j) = fread(fd, 1, 'double');
        raw.ntrace = fread(fd, 1, 'int64');
        raw.lat(j) = fread(fd, 1, 'single');
        raw.lon(j) = fread(fd, 1, 'single');
        raw.alt(j) = fread(fd, 1, 'single');
        dop = fread(fd, 1, 'single');
        nsat = fread(fd, 1, 'uint32');
        fread(fd, 1, 'int32');
        raw.data(:,j) = fread(fd, [5000, 1], 'single');
    end

    t = [0:1./raw.fs:raw.ch.len];
    c = chirp(t, raw.ch.cf - (raw.ch.cf - .5*raw.ch.cf*(raw.ch.bw/100)), raw.ch.len, raw.ch.cf + (.5*raw.ch.cf*(raw.ch.bw/100)), 'linear', -90);
    %if(raw.ch.len == 5e-6)
     %   open('5us.mat');
      %  c = refchirp';
    %elseif(raw.ch.len == 3e-6)
     %   open('3us.mat');
      %  c = refchirp';
    %else
     %   disp("no ref")
    %end
            
    c(length(c)+1:5000) = 0;
    C = fft(c);
    
    raw.pc = zeros(size(raw.data));
    
    mt = zeros(5000,1);
    %raw.Hbp = Hbp;
    
    for j=1:size(raw.data,2)
        %raw.data(:,j) = filtfilt(Hbp.Numerator, 1, raw.data(:,j));
        mt = mt+(raw.data(:,j)./size(raw.data,2));
    end
    
    
    for j=1:size(raw.data,2)
       t = raw.data(:,j) - mt;
       T = fft(t);
       P = T.*C';
       raw.pc(:,j) = ifft(P);
    end
    

    raw.data = single(raw.data);
    raw.pc = single(raw.pc);
    
    img = log(raw.pc.^2);
    img = img - min(min(img));
    img = img ./ max(max(img));
    
    img(img < .4) = .4;
    img = (img - .4)/.6;
    imwrite(img, [fdir, replace(file, '.dat', '.png')], 'png');
    
    loc = [raw.lat', raw.lon', raw.alt'];
    dlmwrite([fdir, replace(file, '.dat', '.csv')], loc, 'precision', 10);
    ofile = replace(file, '.dat', '.mat');
    save([fdir, ofile], 'raw');
end