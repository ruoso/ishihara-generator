#!/usr/bin/env perl
use strict;
use warnings;
use XML::Compile::Schema;
use XML::Compile::Util qw(pack_type);
use Math::Trig;
use Math::Round qw(nhimult nlowmult round);
use List::Util qw(uniq);
use Graphics::Color::HSV;

use constant SVG => 'http://www.w3.org/2000/svg';

sub circle {
  my $point = shift;
  my $base_color = shift;
  my $variability = 0.3;
  my $variation = rand($variability)-$variability/2;
  my $h = $base_color->[0];
  my $s = $base_color->[1];
  my $v = $base_color->[2] + $variation;
  $v = 1 if $v > 1;
  $v = 0 if $v < 0;
  my $color = Graphics::Color::HSV->new
    ({
      hue => $h,
      saturation => $s,
      value => $v
     });
  return
    {
     cx => $point->[0],
     cy => $point->[1],
     r  => $point->[4],
     fill => $color->to_rgb()->as_hex_string('#'),
    };
}

sub make_circles {
  my $size = shift;
  my $count = shift;
  my $base_color_a = shift;
  my $base_color_b = shift;
  my $mask_func = shift;

  my @points = map
    {
      my $angle    = rand(2*pi);
      # log distribution, since circumference
      # grows exponentially, and we want to
      # occupy the space equally.
      my $distr    = log(rand(9)+1)/log(10);
      my $distance = $distr * ($size/2);
      [
       ($size/2)+($distance * cos($angle)),
       ($size/2)+($distance * sin($angle)),
      ]
    } 1..$count;

  # we want to find out how big each circle needs to be.
  # that will depend on the circles that are close to it.
  # in order to avoid having to search every other circle for
  # each circle, we divide in blocks, so we reduce the search
  # space.
  my @blocks;
  my $block_count_per_axis = int(log($count)/log(2));
  foreach my $p (@points) {
    my $block_x = ($p->[0]/$size)*$block_count_per_axis;
    my $block_y = ($p->[1]/$size)*$block_count_per_axis;
    my @blx = uniq nlowmult(1,$block_x), nhimult(1,$block_x);
    my @bly = uniq nlowmult(1,$block_y), nhimult(1,$block_y);
    $p->[2] = \@blx;
    $p->[3] = \@bly;
    foreach my $blx (@blx) {
      $blocks[$blx] ||= [];
      foreach my $bly (@bly) {
        $blocks[$blx][$bly] ||= [];
        push @{$blocks[$blx][$bly]}, $p;
      }
    }
  }

  # now let's find out the smallest distance from a point to any
  # other point.
  foreach my $p (@points) {
    my @otherpoints;
    foreach my $blx (@{$p->[2]}) {
      foreach my $bly (@{$p->[3]}) {
        push @otherpoints, @{$blocks[$blx][$bly]};
      }
    }
    @otherpoints = uniq @otherpoints;
    my $smallestdist = $size;
    foreach my $op (@otherpoints) {
      next if $op->[0] == $p->[0] && $op->[1] == $p->[1];
      my $dist = sqrt( ($op->[0] - $p->[0])**2 + ($op->[1] - $p->[1])**2 );
      if ($dist < $smallestdist) {
        $smallestdist = $dist;
      }
      $p->[4] = $smallestdist;
    }

  }

  return map {
    circle($_, $mask_func->($_) ? $base_color_a : $base_color_b )
  } @points;
}

sub ishihara_circles {
  my $size = shift;
  my $count = shift;
  my $base_color_a = shift;
  my $base_color_b = shift;
  my $mask_func = shift;
  my @circles = map { { circle => $_ } }
    make_circles($size, $count, $base_color_a, $base_color_b, $mask_func);
  return \@circles;
}

sub ishihara_svg_data {
  my $size = shift;
  my $count = shift;
  my $base_color_a = shift;
  my $base_color_b = shift;
  my $mask_func = shift;
  my $circles =
    ishihara_circles
    (
     $size, $count,
     $base_color_a,
     $base_color_b,
     $mask_func
    );
  return
    {
     width => $size,
     height => $size,
     cho_desc => $circles,
    };
}

sub make_mask_func {
  my $mask = shift;
  my $size = shift;
  my @mask_arr =
    map {
      [
       split '', $_
      ]
    } split /\n/, $mask;
  my $y_size = scalar @mask_arr;
  my @x_sizes = map { scalar @$_ } @mask_arr;
  my $x_size = (sort { $b <=> $a } @x_sizes)[0];
  return sub {
    my $p = shift;
    my $mx = round(($p->[0]/$size)*$x_size);
    my $my = round(($p->[1]/$size)*$y_size);
    if (exists $mask_arr[$my] && $mask_arr[$my]) {
      if (exists $mask_arr[$my][$mx] && $mask_arr[$my][$mx] ne " ") {
        return 1;
      }
    }
    return 0;
  }
};

my $mask = <<MASK;
    
    
              ##
            ####
          ######
         ### ###         
        ###  ###
        ###  ###
        ###########
        ###########
             ###
             ###
             ###
    
MASK

my $data = ishihara_svg_data
  (
   600, 3000,
   [319, .36, .55],
   [0, .36, .55],
   make_mask_func($mask, 600),
  );

my $schema = XML::Compile::Schema->new(['SVG.xsd', 'xlink.xsd', 'xml.xsd']);
my $writer = $schema->compile
  (
   WRITER => pack_type( SVG, 'svg' ),
   prefixes => { SVG, 'svg' },
  );
my $doc    = XML::LibXML::Document->new('1.0', 'UTF-8');
my $xml    = $writer->($doc, $data);
$doc->setDocumentElement($xml);
print $doc->toString(1);
