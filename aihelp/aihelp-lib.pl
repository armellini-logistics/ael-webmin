# aihelp-lib.pl
# Common functions for the AI Help Chatbot module

use strict;
use warnings;
our (%text, %config, $config_directory, $root_directory, $module_name);
foreign_require("webmin", "webmin-lib.pl");

# get_config()
# Get settings for this module
sub get_config
{
    my %cfg;
    &read_file("$config_directory/$module_name/config", \%cfg);
    return %cfg;
}

# save_config(&cfg)
# Save settings for this module
sub save_config
{
    my ($cfg) = @_;
    &make_dir("$config_directory/$module_name", 0700) if (!-d "$config_directory/$module_name");
    &write_file("$config_directory/$module_name/config", $cfg);
}

# rebuild_help_index()
# Index all module help files into a single cached JSON file
sub rebuild_help_index
{
    my $db_dir = "$config_directory/$module_name";
    &make_dir($db_dir, 0700) if (!-d $db_dir);
    my $db_file = "$db_dir/help_db.json";
    
    my @help_data;
    # Scan all directories in Webmin root
    opendir(my $dh, $root_directory);
    while (my $dir = readdir($dh)) {
        next if ($dir =~ /^\./ || $dir eq "tarballs" || $dir eq "newkey" || $dir eq "deb");
        my $help_dir = "$root_directory/$dir/help";
        if (-d $help_dir) {
            opendir(my $hdh, $help_dir);
            while (my $file = readdir($hdh)) {
                next if ($file =~ /^\./ || $file !~ /\.html$/ || $file =~ /\.[a-z]{2}\.html$/); # Skip non-HTML or translated
                my $path = "$help_dir/$file";
                my $content = &read_file_contents($path);
                next if (!$content);
                
                # Strip HTML tags
                $content =~ s/<script[^>]*>.*?<\/script>//igs;
                $content =~ s/<style[^>]*>.*?<\/style>//igs;
                $content =~ s/<[^>]+>//g;
                # Normalize whitespace
                $content =~ s/\s+/ /g;
                $content =~ s/^\s+//;
                $content =~ s/\s+$//;
                
                # Limit size to prevent overflow
                $content = substr($content, 0, 5000);
                
                push(@help_data, {
                    'module' => $dir,
                    'file' => $file,
                    'text' => $content
                });
            }
            closedir($hdh);
        }
    }
    closedir($dh);
    
    # Save as JSON using Webmin core function
    my $json_str = &convert_to_json(\@help_data);
    &write_file_contents($db_file, $json_str);
}

# search_help_index($query)
# Perform keyword search over help index
sub search_help_index
{
    my ($query) = @_;
    my $db_file = "$config_directory/$module_name/help_db.json";
    if (!-r $db_file) {
        &rebuild_help_index();
    }
    my $raw = &read_file_contents($db_file);
    return ( ) if (!$raw);
    my $db = &convert_from_json($raw);
    return ( ) if (ref($db) ne 'ARRAY');
    
    # Extract search terms (length > 2)
    my @words = grep { length($_) > 2 } split(/\W+/, lc($query));
    # Exclude basic common terms
    my %stopwords = map { $_ => 1 } qw(the and for you how can out get set add make list edit view check is what this details some files system webmin);
    @words = grep { !$stopwords{$_} } @words;
    
    return ( ) if (!@words);
    
    # Score documents
    my @scored;
    foreach my $doc (@$db) {
        my $score = 0;
        my $text = lc($doc->{'text'});
        foreach my $w (@words) {
            my $count = () = $text =~ /\b\Q$w\E\b/g;
            $score += $count * 3;
            if (lc($doc->{'module'}) eq $w) {
                $score += 10;
            }
        }
        if ($score > 0) {
            push(@scored, { %$doc, 'score' => $score });
        }
    }
    
    # Sort by score descending and return top 8
    @scored = sort { $b->{'score'} <=> $a->{'score'} } @scored;
    if (@scored > 8) {
        @scored = @scored[0..7];
    }
    return @scored;
}

1;
