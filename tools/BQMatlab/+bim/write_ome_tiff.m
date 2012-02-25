% write_ome_tiff - writies 3-4D OME TIFF files
% 
%   INPUT:
%       im       - 3D image matrix or a cell with mat files to load
%       filename - string of file name to write
%       dim      - struct with image dimension, ususally should be []
%                  dim.type, dim.x, dim.y, dim.c, dim.z, dim.t
%       res      - struct with image resolution, if known
%                  res.x, res.y, res.z, res.t
%
%   AUTHOR:
%       Dmitry Fedorov, <www.dimin.net>
%
%   VERSION:
%       1  - 2012-01-11 first implementation

function write_ome_tiff( data, filename, dim, res)

    if ~iscell(data),
        im = data;
        num_t = 1;
    else
        im = load_from_file(data{1,1});
        num_t = size(data,1);
    end

    if isempty(dim),
        dim = get_image_dims(im);
    end
    dim.t = num_t;
    
    xml = get_ome_xml(dim, res);
    
    tif = Tiff(filename, 'w');  
    for t=1:dim.t,    
        if iscell(data),    
            im = load_from_file(data{t,1});
        end    
        for z=1:dim.z,
            tags = struct;
            tags.ImageLength         = dim.x;
            tags.ImageWidth          = dim.y;
            tags.Photometric         = Tiff.Photometric.MinIsBlack;
            tags.BitsPerSample       = pixel_bit_depth(im);
            tags.SamplesPerPixel     = 1;
            tags.RowsPerStrip        = 16;
            tags.PlanarConfiguration = Tiff.PlanarConfiguration.Chunky;
            tags.Software            = 'bimwrite';
            if z==1 && t==1,
                tags.ImageDescription = xml;
            end
            tif.setTag(tags);   
            tif.write(im(:,:,z));
            tif.writeDirectory();
        end
    end
    tif.close();
end

function [depth] = pixel_bit_depth(im)
    e = im(ones(1,ndims(im)));
    e = e(1);
    r = whos('e');
    depth = r.bytes*8;
end

function [dim] = get_image_dims(im)
    dim = struct;
    dim.type = class(im);
    dim.x = size(im,1);
    dim.y = size(im,2);    
    dim.z = size(im,3);    
    dim.t = 1;    
    dim.c = 1; 
end

function [xml] = get_ome_xml(dim, res)
    xml = '<?xml version="1.0" encoding="UTF-8"?>';
    xml = [xml '<OME xmlns="http://www.openmicroscopy.org/XMLschemas/OME/FC/ome.xsd" '];
    xml = [xml 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '];
    xml = [xml 'xsi:schemaLocation="http://www.openmicroscopy.org/XMLschemas/OME/FC/ome.xsd '];
    xml = [xml 'http://www.openmicroscopy.org/XMLschemas/OME/FC/ome.xsd">'];
    xml = [xml '<Image ID="openmicroscopy.org:Image:1" Name="libbioimage" DefaultPixels="openmicroscopy.org:Pixels:1-1">'];
    xml = [xml '<Pixels ID="openmicroscopy.org:Pixels:1-1" DimensionOrder="XYCZT" BigEndian="false"'];

    d = sprintf(' PixelType="%s" SizeX="%d" SizeY="%d" SizeC="%d" SizeZ="%d" SizeT="%d"',... 
                dim.type, dim.x, dim.y, dim.c, dim.z, dim.t);

    if ~isempty(res),
    r = sprintf(' PhysicalSizeX="%f" PhysicalSizeY="%f" PhysicalSizeZ="%f" TimeIncrement="%f"',... 
                res.x, res.y, res.z, res.t);
    end
            
    xml = [xml d r ' >'];
    xml = [xml '<TiffData/>'];
    xml = [xml '</Pixels>'];
    xml = [xml '</Image>'];
    xml = [xml '</OME>'];    
end

function [im] = load_from_file(name)
    l = load(name);
    im = l.x;
    l = [];
end
