#!/usr/bin/perl
package BQPhytomorph::SeedSize;

use warnings;
use strict;

use Cwd 'abs_path';
use File::Basename;
use File::Copy;
use File::Glob;
use Getopt::Long;
use XML::LibXML;
use XML::Simple;
use Text::CSV;
use POSIX qw(strftime);
use URI::Escape;
use Log::Log4perl;

use BQPhytomorph;

our $EXEC          = "./seedSize";

my $log = Log::Log4perl::get_logger('seedsize');

#########################################
## Argument handling
my ($help, $image, $mex, $user, $password, $userpass, $staging_path, $token);
my $series_id = '';
my $debug = 0;
my $dryrun = 0;

usage() if ( ! GetOptions('help|?' => \$help, 
                          'debug|d' => \$debug,
                          'dryrun|n' => \$dryrun,
                          'mex_url=s' => \$mex,
                          'image_url=s' => \$image, 
                          'staging_path=s'=>\$staging_path,
                          'user=s' => \$user,
                          'password=s' => \$password,
                          'token=s' => \$token,
)
          or defined $help );

my $options = { debug=> $debug, dryrun => $dryrun };
my $command  = shift;

$command = 'start' if (!defined $command);

if ($user && $password) {
  $userpass = $user . ':' . $password;
}


print "command is " . $command . "\n";

my $ret=0;
$ret = command_setup() if ($command eq 'setup');
$ret = command_teardown() if ($command eq 'teardown');
$ret = command_start() if ($command eq 'start');

exit($ret);


sub usage {
  print "Unknown option: @_\n" if ( @_ );
  print "usage: SeedSize [--mex_url=URL] [--user=USER --password=PASS|token=TOKEN] [--image_url=IMAGE] [--staging_path=SERIES_ID] [--debug] [--help]  [start|finished|test|test_finished] \n";
  exit 1;
}


sub command_setup {
  my $bq = new BQPhytomorph(mex_url => $mex, userpass => $userpass,
                            token=> $token, options=>$options );
  my $imgdir = "$staging_path/images";
  unless ( -d $imgdir ) {
    mkdir $imgdir or die "Can't make  $imgdir";
  }

  $bq->update_mex('initializing');


  my @localfiles;
  if ($image =~ m/dataset/g) {
    @localfiles = $bq->fetch_dataset ($image,  $imgdir);
  } else {
    @localfiles = $bq->fetch_image ($image,  $imgdir);
  }

  $bq->update_mex('scheduling');
  return 0;
}
sub command_start {
  my $bq = new BQPhytomorph(mex_url => $mex, userpass => $userpass,
                            token=> $token, options=>$options );

  $bq->update_mex('running');

  my $imgdir = "$staging_path/images/";
  return system ($EXEC, $imgdir);
}

sub command_teardown {
  my $bq = new BQPhytomorph(mex_url => $mex, userpass=>$userpass,
                            token=>$token,
                            options=>$options) ;
  # Collect results, process and save

  my @localfiles = glob "$staging_path/images/*C.csv";
  my $summary    = "$staging_path/images/summary.csv";

  my @mextags;
  eval {
    for my $mc (@localfiles) {
      if (-f $mc) {
        push (@mextags, saveStats ($bq, $mex, $image, $mc ) )
      }
    }
    1;
  } or do {
    $log->error("problems while saving data $@");
    print "FAILED";
    $bq->finish_mex ( status => 'FAILED', msg=> $@ );
    return 1;
  };
  # Update the MEX with state
  print "FINISHED";
  $bq->finish_mex ( status => 'FINISHED', tags=> \@mextags );
  return 0;
}

sub saveStats {
  my ($bq, $mex, $image,  $MC) = @_;

  print "READING $MC\n";

  #area-0, minor axis len-1, major axis len-2, centerX-3, centerY-4, rotation-5, minorX-6, minorY-7, majorX-8,majorY-9

  my $csv = Text::CSV->new();
  my @seeds;
  open (MC, "<", $MC) or die "No $MC";
  while (<MC>) {
    if ($csv->parse($_)) {
      my @cols = $csv->fields();
      push ( @seeds,
        { type => "seed",
          tag => [ { name=>"area", value=> $cols[0] },
                   { name=>"major", value=> $cols[2] },
                   { name=>"minor", value=> $cols[1] } ],
          ellipse => { 
               vertex=> [ { x=> $cols[3], y=> $cols[4], index=>0 },
                          { x=> $cols[8], y=> $cols[9], index=>1 },
                          { x=> $cols[6], y=> $cols[7], index=>2 }
                        ]
                     }
        });
    }
  }
  close(MC);
  my $xs = new XML::Simple(RootName=>undef);


  # Add Gobjects directly to image
  my $gobreq = { gobject => { name=>"SeedSize",
                              gobject => \@seeds
                            }
               };
  my $content =  $xs->XMLout($gobreq);
  my $gurl    = "";
  my $doc;
  if ( ! $dryrun ) {
    $doc = $bq->postxml ($image . "/gobjects", $content);
    die "post failed:" . $image . "/gobjects" unless defined $doc;
    $gurl = $doc->findnodes('//gobject/@uri')->to_literal->value;
  }
  if ( $debug ) {
    print "GOB $gurl\n";
    print "GOB => $content";
  }

  # Add Tag to image also
  my $tagreq = { tag =>
                 { name => "SeedSize",
                   tag => [{ name=>"gobjects_url", type=>"link", value=>$gurl},
                           { name=>"mex_url", type=>"link", value=>$mex},
                           { name=>'date_time', value=> strftime "%Y-%m-%d %H:%M:%S", localtime },
                           { name=>"area-histogram", type=>"statistics",
                             value => ("http:/stats?url=" . uri_escape($gurl) 
                                       ."&xpath=".uri_escape('//tag[@name="area"]')
                                       ."&xmap=".uri_escape("tag-value-number")
                                       ."&xreduce=histogram&run=true")},

                           { name=>"major-histogram", type=>"statistics",
                             value => ("http:/stats?url=" . uri_escape($gurl) 
                                       ."&xpath=".uri_escape('//tag[@name="major"]')
                                       ."&xmap=".uri_escape("tag-value-number")
                                       ."&xreduce=histogram&run=true")},

                           { name=>"minor-histogram", type=>"statistics",
                             value => ("http:/stats?url=" . uri_escape($gurl) 
                                       ."&xpath=".uri_escape('//tag[@name="minor"]')
                                       ."&xmap=".uri_escape("tag-value-number")
                                       ."&xreduce=histogram&run=true")},
                           { name=>"csv-area-major-minor", type=>"file",
                             value => ("http:/stats/csv?url=" . uri_escape($gurl)
                                       ."&xpath=".uri_escape('//tag[@name="area"]')
                                       ."&xpath1=".uri_escape('//tag[@name="major"]')
                                       ."&xpath2=".uri_escape('//tag[@name="minor"]')
                                       ."&xmap=".uri_escape("tag-value-number")
                                       ."&xreduce=vector")},
                          ]
                 }
               };
  $content =  $xs->XMLout($tagreq);
  if (! $dryrun ) {
    $doc = $bq->postxml ($image . "/tags", $content);
    die "post failed:" . $image . "/tags" unless defined $doc;
  }
  if ( $debug ) {
    print "TAG => $content";
  }
  # Add the pointers in the mex

  my $mextag = {name=>"gobjects_url", type=>"link", value=>$gurl};

  return $mextag
}






