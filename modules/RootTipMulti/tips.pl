use Data::Dumper;
use File::Path;

my $tipcsv  = <<END;
type,name,value,x,y,z,t,ch
resource,,
point,,
vertex,,,693.333333333,870.933322483,0.0,0.0,

point,,
vertex,,,666.666666667,735.822211372,0.0,0.0,

point,,
vertex,,,705.777777778,595.377766927,0.0,0.0,

point,,
vertex,,,679.111111111,444.266655816,0.0,0.0,

point,,
vertex,,,664.888888889,334.044433594,0.0,0.0,

point,,
vertex,,,643.555555556,218.488878038,0.0,0.0,
END


sub readtips {
  
  my $staging = ".";

  use Text::CSV; 
  my $csv = Text::CSV->new(); 
 
  my @tips; 
  foreach my $line  (split( /^/, $tipcsv )){ 
    print $line; 
    if ($csv->parse($line)) { 
      my @cols = $csv->fields(); 
      print Dumper(@cols); 
      if ($cols[0] eq 'vertex' ) { 
        push (@tips ,  "$cols[3], $cols[4] "); 
      } 
    }else { 
      my $err = $csv->error_input; 
      print "Failed to parse line: $err"; 
    } 
  } 
 
  my $tipout = './tips.csv'; 
 
  open(TIPS, ">$tipout"); 
  foreach my $tip (@tips) {  
    print TIPS "$tip\n"; 
  } 
  close(TIPS); 

}
readtips();

