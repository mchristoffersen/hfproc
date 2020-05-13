% data = double(raw.data);
% 
%     
% t = [0:1/raw.fs:raw.ch.len];
% c = chirp(t, raw.ch.cf - (raw.ch.cf - .5*raw.ch.cf*(raw.ch.bw/100)), raw.ch.len, raw.ch.cf + (.5*raw.ch.cf*(raw.ch.bw/100)), 'linear', -90);
% 
% 
% c(length(c)+1:5000) = 0;
% C = fft(c);
% 
% pc = zeros(size(data));
% 
% mt = zeros(5000,1);
% 
% 
% for j=1:size(data,2)
%     sumint = 100;
%     mt = zeros(5000,1);
%     data(:,j) = filtfilt(Hbp.Numerator, 1, data(:,j));
%     
%     if(j <= sumint/2)
%         for k=1:sumint
%             mt = mt + (data(:,k)./sumint);
%         end
%         data(:,j) = data(:,j)-mt;
%     elseif(j >= size(data,2)-sumint/2)
%         for k=size(data,2)-sumint:size(data,2)
%             mt = mt + (data(:,k)./sumint);
%         end
%         data(:,j) = data(:,j)-mt;
%     else
%         for k=j-sumint/2:j+sumint/2
%             mt = mt + (data(:,k)./sumint);
%         end
%         data(:,j) = data(:,j)-mt;
%     end
% end
% 
% 
% for j=1:size(raw.data,2)
%     %raw.data(:,j) = filtfilt(Hbp.Numerator, 1, raw.data(:,j));
%     mt = mt+(raw.data(:,j)./size(raw.data,2));
% end
% 
% for j=1:size(data,2)
%    t = data(:,j)-mt;
%    t(t<-1e-3) = -1e-3;
%    t(t>1e-3) = 1e-3;
%    T = fft(t);
%    P = T.*C';
%    pc(:,j) = ifft(P);
% end
pcstack = zeros(size(raw.pc,1),ceil(size(raw.pc,2)/10));

for i=1:size(raw.pc,2)
    j = ceil(i/10);
    pcstack(:,j) = pcstack(:,j) + raw.pc(:,i);
end

pcstack = pcstack(:,750:1000);

mt = zeros(5000,1);

for j=1:size(pcstack,2)
    mt = mt+(pcstack(:,j)./size(pcstack,2));
end

for j=1:size(pcstack,2)
    pcstack(:,j) = pcstack(:,j)-mt;
end
