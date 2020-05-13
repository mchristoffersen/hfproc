block.ch0 = raw.data;
block.clutter = zeros(size(raw.data));
block.dt = 1/raw.fs;
block.name = "University of Arizona LoWRES";
block.chirp.cf = raw.ch.cf;
block.chirp.bw = raw.ch.bw;
block.chirp.amp = raw.ch.amp;
block.chirp.len = raw.ch.len;
block.prf = raw.prf;
block.stack = raw.stack;
block.elev_surf = zeros(size(block.twtt,2));
block.dist_lin
