% points2gobjects - writies points to Bisque Gobjects XML format
% 
%   INPUT:
%       filename - string of file name to write
%       m        - detected nuclei positions, is a matrix where
%                   m(:,1) -> Y coordinate (starting at 1)
%                   m(:,2) -> X coordinate (starting at 1)
%                   m(:,3) -> Z coordinate (starting at 1)
%                   m(:,4) -> point IDs
%                   m(:,5) -> probability
%                   m(:,6) -> probability based on counts
%                   m(:,7) -> probability based on sums
%                   m(:,8) -> probability based on mean
%                   m(:,9) -> probability based on LoG mean
%       type     - string with the user-given type for the block of points
%       name     - string with the user-given name for the block of points
%       color    - optional: string with HTML style default color for points
%       fid      - optional: file handle for an open file to append block
%       indx     - optional: indices of points to store
%
%   AUTHOR:
%       Dmitry Fedorov, www.dimin.net
%
%   VERSION:
%       0.1 - 2011-03-29 First implementation

function points2gobjects ( filename, m, type, name, color, fid, indx )
  if nargin < 5, color = []; end
  [num_nuclei, num_data] = size(m);
  if nargin<7 || isempty(indx), indx = [1:num_nuclei]; end 

  if ~isempty(filename) && (nargin<6 || isempty(fid)), 
      fid = fopen(filename, 'wt');
  end
  
  fprintf(fid, '<gobject type="%s" name="%s" >\n', type, name);     
  
  for n=1:num_nuclei,
     if isempty(intersect(indx, n)), continue; end
     x = m(n, 2)-1.0;       
     y = m(n, 1)-1.0; 
     z = m(n, 3)-1.0; 

     fprintf(fid, '  <gobject type="point" name="%d" >\n', n);     
     fprintf(fid, '    <vertex x="%.2f" y="%.2f" z="%.2f" />\n', x, y, z); 
     if ~isempty(color),
       fprintf(fid, '    <tag name="color" value="%s" />\n', color);
     end     
     
     if num_data>=5,
       p = m(n, 5)*100.0;   
       fprintf(fid, '      <tag name="probability" value="%.2f" />\n', p);         
     end     

     if num_data>=6,
       p = m(n, 6)*100.0;   
       fprintf(fid, '      <tag name="probability_counts" value="%.2f" />\n', p);         
     end         

     if num_data>=7,
       p = m(n, 7)*100.0;   
       fprintf(fid, '      <tag name="probability_sums" value="%.2f" />\n', p);         
     end  
     
     if num_data>=8,
       p = m(n, 8)*100.0;   
       fprintf(fid, '      <tag name="probability_mean" value="%.2f" />\n', p);         
     end  
     
     if num_data>=9,
       p = m(n, 9)*100.0;   
       fprintf(fid, '      <tag name="probability_log_mean" value="%.2f" />\n', p);         
     end    
     
     if num_data>=10,
       p = m(n, 10);   
       fprintf(fid, '      <tag name="intensity_sum" value="%.2f" />\n', p);         
     end         
     
     fprintf(fid, '  </gobject>\n');      
  end        
  
  fprintf(fid, '</gobject>\n');
  
  if ~isempty(filename) || nargin<6, 
      fclose(fid);
  end  
end 
