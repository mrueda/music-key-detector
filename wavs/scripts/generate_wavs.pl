#!/usr/bin/env perl
#
# Music Tone and Key Generator Script
# Author: Manuel Rueda, PhD
# License: MIT License
#
# Generates single tones and scales for recognition purposes.

use strict;
use warnings;
use PDL;
use File::Path qw(remove_tree make_path);
use constant PI   => atan2( 0, -1 );
use constant RATE => 44100;
use feature 'signatures';
no warnings 'experimental::signatures';

# Frequencies for chromatic notes
my %frequencies = (
    'C'  => 440 * 2**( (-9) / 12 ),
    'C#' => 440 * 2**( (-8) / 12 ),
    'D'  => 440 * 2**( (-7) / 12 ),
    'D#' => 440 * 2**( (-6) / 12 ),
    'E'  => 440 * 2**( (-5) / 12 ),
    'F'  => 440 * 2**( (-4) / 12 ),
    'F#' => 440 * 2**( (-3) / 12 ),
    'G'  => 440 * 2**( (-2) / 12 ),
    'G#' => 440 * 2**( (-1) / 12 ),
    'A'  => 440,
    'A#' => 440 * 2**( (1) / 12 ),
    'B'  => 440 * 2**( (2) / 12 ),
);

# Generate sine wave samples
sub sine_wave ( $n_samples, $frequency ) {
    my $phase = sequence($n_samples) * 2 * PI * $frequency / RATE;
    return sin($phase);
}

# Write WAV file
sub prepare_and_write_wav ( $samples, $path ) {
    my $amplitude = 2**15 - 1;
    my $max       = max( abs $samples );
    my $sound16   = short( $samples / $max * $amplitude )->get_dataref;

    open( my $fh, '>', $path ) or die "Cannot write to $path: $!";
    binmode $fh;

    print $fh 'RIFF';
    print $fh pack( 'l', 36 + length($$sound16) );    # File size
    print $fh 'WAVEfmt ';
    print $fh pack( 'l', 16 );                        # Subchunk size
    print $fh pack( 'ssllss', 1, 1, RATE, RATE * 2, 2, 16 );
    print $fh 'data';
    print $fh pack( 'l', length($$sound16) );
    print {$fh} $$sound16;

    close $fh;
    print "Generated: $path\n";
}

# Generate single tones
sub generate_single_tones {
    remove_tree("tones", { error => \my $err });
    make_path("tones") or die "Failed to create tones directory: $!";
    
    foreach my $note ( sort keys %frequencies ) {
        my $samples = sine_wave( RATE, $frequencies{$note} );
        prepare_and_write_wav( $samples, "tones/$note.wav" );
    }
}

# Generate scales (scales)
sub generate_scale ( $root, $intervals, $output_path ) {
    my @notes = sort keys %frequencies;
    my $current_index = (grep { $notes[$_] eq $root } 0..$#notes)[0];

    my @scale;
    push @scale, $frequencies{$notes[$current_index]};

    foreach my $interval (@$intervals) {
        $current_index = ($current_index + $interval) % @notes;
        push @scale, $frequencies{$notes[$current_index]};
    }

    my $samples = pdl([]);
    foreach my $freq (@scale) {
        $samples = $samples->append( sine_wave( RATE * 2 / 7, $freq ) );  # Each note for ~0.2 seconds
    }

    prepare_and_write_wav( $samples, $output_path );
}

# Main
generate_single_tones();

# Define scales
my %scales = (
    'Major'        => [2, 2, 1, 2, 2, 2, 1],
    'Natural Minor'=> [2, 1, 2, 2, 1, 2, 2],
    'Harmonic Minor'=> [2, 1, 2, 2, 1, 3, 1],
    'Melodic Minor'=> [2, 1, 2, 2, 2, 2, 1],
    'Dorian'       => [2, 1, 2, 2, 2, 1, 2],
    'Phrygian'     => [1, 2, 2, 2, 1, 2, 2],
    'Lydian'       => [2, 2, 2, 1, 2, 2, 1],
    'Mixolydian'   => [2, 2, 1, 2, 2, 1, 2],
    'Locrian'      => [1, 2, 2, 1, 2, 2, 2]
);

# Generate scales
remove_tree("scales", { error => \my $err });
make_path("scales") or die "Failed to create scales directory: $!";
    
foreach my $scale_name (sort keys %scales) {
    my $intervals = $scales{$scale_name};
    my $output_file = "scales/C_$scale_name.wav";
    generate_scale('C', $intervals, $output_file);
}
